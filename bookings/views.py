from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from django.contrib.auth.forms import PasswordResetForm
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.db.models import Q
from django.conf import settings
from django.urls import reverse, reverse_lazy
from datetime import datetime, timedelta, date
from django.contrib.auth.models import User
from .models import Booking, Client, LessonType, BlockedTime
from .forms import BookingForm, SignUpForm, ForgotUsernameForm, CustomLoginForm, SMSOptInForm
import json
import requests 
from django.contrib import messages
from twilio.rest import Client as TwilioClient
from django.http import HttpResponse
from django.contrib.auth.views import PasswordResetView
import threading
from django.views.generic import FormView
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
import asyncio
import aiohttp
from .email_backends import send_booking_mail  # Import the function here



# ==========================
# CONTACT FORM
# ==========================
@csrf_exempt  # Remove if you handle CSRF in front-end
def contact(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            payload = {
                "sender": {"name": "Developmental Baseball", "email": "contact@coachalvarez44.com"},
                "to": [{"email": settings.EMAIL_RECEIVER}],
                "subject": data.get("subject", "New Contact Form Submission"),
                "textContent": f"""
Name: {data.get('firstname')} {data.get('lastname')}
Email: {data.get('email')}
Phone: {data.get('phone')}
Message: {data.get('message')}
""",
            }
            response = requests.post(
                "https://api.brevo.com/v3/smtp/email",
                json=payload,
                headers={
                    "api-key": settings.BREVO_API_KEY,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                timeout=10
            )
            response.raise_for_status()
            return JsonResponse({"success": True, "message": "Your message has been sent to me! I will get back to you soon!"})
        except Exception as e:
            return JsonResponse({"success": False, "message": "Server error. Try again later.", "error": str(e)}, status=500)
    return render(request, 'bookings/contact.html')


# ==========================
# SIGNUP
# ==========================
def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("client_menu")
    else:
        form = SignUpForm()
    return render(request, "bookings/signup.html", {"form": form})


# ==========================
# CLIENT MENU
# ==========================
@login_required
def client_menu(request):
    return render(request, 'bookings/client_menu.html')


# ==========================
# BOOK LESSON
# ==========================
@login_required
@never_cache
def book_lesson(request):
    initial_data = {}
    date_param = request.GET.get("date")
    if date_param:
        try:
            parsed_datetime = datetime.fromisoformat(date_param)
            initial_data["date"] = parsed_datetime.date()
            initial_data["start_time"] = parsed_datetime.time()
        except ValueError:
            pass

    if request.method == "POST":
        form = BookingForm(request.POST, initial=initial_data)
        if form.is_valid():
            booking_date = form.cleaned_data['date']
            today = date.today()

            # Calculate current and next month limits
            end_of_current_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            seven_days_before_end = end_of_current_month - timedelta(days=7)
            next_month_start = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
            end_of_next_month = (next_month_start.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            # Enforce booking range
            if not ((today <= booking_date <= end_of_current_month) or
                    (today >= seven_days_before_end and next_month_start <= booking_date <= end_of_next_month)):
                form.add_error('date', "You can only book within the current month, or next month starting 7 days before the month ends.")
                return render(request, "bookings/booking_form.html", {"form": form})

            booking = form.save(commit=False)
            booking.client = Client.objects.get(user=request.user)
            booking.save()

            # ⬇️ Send the booking email here
            booking_details = {
                "first_name": booking.client.first_name,
                "date": booking.date.strftime("%Y-%m-%d"),
                "start_time": booking.start_time.strftime("%I:%M %p"),
                "end_time": (datetime.combine(booking.date, booking.start_time)
                             + timedelta(minutes=booking.lesson_type.duration)
                            ).strftime("%I:%M %p"),
                "lesson_type": booking.lesson_type.name,
            }
            try:
                send_booking_mail(booking.client.email, booking_details)
            except Exception as e:
                print("Email failed:", e)

            return redirect("my_bookings")
    else:
        form = BookingForm(initial=initial_data)

    return render(request, "bookings/booking_form.html", {"form": form})


# ==========================
# MY BOOKINGS
# ==========================
@login_required
def my_bookings(request):
    client = get_object_or_404(Client, user=request.user)
    now = datetime.now()

    # Only show bookings that are in the future or today but not started yet
    bookings = Booking.objects.filter(
        client=client
    ).filter(
        Q(date__gt=now.date()) | Q(date=now.date(), start_time__gte=now.time())
    ).order_by('date', 'start_time')

    show_message = bookings.exists()
    
    return render(request, 'bookings/my_bookings.html', {
        'bookings': bookings,
        'show_message': show_message
    })


# ==========================
# CALENDAR DATA (JSON)
# ==========================
@login_required
def calendar_view(request):
    start_param = request.GET.get("start")
    end_param = request.GET.get("end")

    if start_param and end_param:
        start_date = datetime.fromisoformat(start_param).date()
        end_date = datetime.fromisoformat(end_param).date()
    else:
        today = date.today()
        start_date = today.replace(day=1)
        end_date = (today.replace(day=28) + timedelta(days=4)).replace(day=1)

    events = []
    blocked_full_days = []

    # Bookings
    bookings = Booking.objects.filter(date__range=(start_date, end_date))
    for b in bookings:
        start_dt = datetime.combine(b.date, b.start_time)
        end_dt = start_dt + timedelta(minutes=b.lesson_type.duration)
        events.append({
            'title': f"Booked - {b.lesson_type.name}",
            'start': start_dt.isoformat(),
            'end': end_dt.isoformat(),
            'allDay': False,
            "color": "#616161ff",
            "textColor": "white",
            "extendedProps": {"blocked": True},
            })
       

    # Blocked times
    blocked_times = BlockedTime.objects.filter(date__range=(start_date, end_date))
    for blocked in blocked_times:
        if not blocked.start_time and not blocked.end_time:
            # Full day block
            blocked_full_days.append(blocked.date.strftime('%Y-%m-%d'))
            events.append({
                "title": "Unavailable",
                "start": blocked.date.isoformat(),
                "allDay": True,
                "color": "#616161ff",
                "textColor": "white",
                "extendedProps": {"blocked": True},
            })
        else:
            # Partial block
            start_dt = datetime.combine(blocked.date, blocked.start_time)
            end_dt = datetime.combine(blocked.date, blocked.end_time)
            events.append({
                "title": "Unavailable",
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
                "allDay": False,
                "color": "#616161ff",
                "textColor": "white",
                "extendedProps": {"blocked": True},
            })

    return JsonResponse({"events": events, "blocked_dates": blocked_full_days})


# ==========================
# CALENDAR PAGE
# ==========================
@login_required
def calendar_page(request):
    blocked_full_days = BlockedTime.objects.filter(start_time__isnull=True, end_time__isnull=True).values_list('date', flat=True)
    blocked_dates = [d.strftime('%Y-%m-%d') for d in blocked_full_days]
    return render(request, 'bookings/calendar.html', {"blocked_dates": blocked_dates})


@login_required
def book_lesson(request):
    initial_data = {}
    date_param = request.GET.get("date")
    if date_param:
        try:
            parsed_datetime = datetime.fromisoformat(date_param)
            initial_data["date"] = parsed_datetime.date()
            initial_data["start_time"] = parsed_datetime.time()
        except ValueError:
            pass

    if request.method == "POST":
        form = BookingForm(request.POST, initial=initial_data)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.client = Client.objects.get(user=request.user)
            booking.save()

            sms_body = (
                f"Hello {booking.client.first_name}, your lesson has been booked!\n"
                f"Date: {booking.date.strftime('%b %d, %Y')}\n"
                f"Time: {booking.start_time.strftime('%I:%M %p')} - "
                f"{(datetime.combine(booking.date, booking.start_time) + timedelta(minutes=booking.lesson_type.duration)).strftime('%I:%M %p')}\n"
                f"Lesson Type: {booking.lesson_type.name}\n\n"
                "Thank you! See you soon!"
            )

            if booking.client.sms_opt_in and False: # change to True when ready
                # Send SMS only if client opted in
                send_sms(booking.client.phone, sms_body, client_obj=booking.client)

            # Build booking_details dict for email
            end_time_dt = datetime.combine(booking.date, booking.start_time) + timedelta(minutes=booking.lesson_type.duration)
            booking_details = {
                "first_name": booking.client.first_name,
                "last_name": booking.client.last_name,
                "lesson_type": booking.lesson_type.name,
                "date": booking.date.strftime("%b %d, %Y"),
                "start_time": booking.start_time.strftime("%I:%M %p"),
                "end_time": end_time_dt.strftime("%I:%M %p"),
            }

            # ✅ Send confirmation email with client_name
            send_booking_mail(
                booking.client.email,
                booking_details,
                client_name=booking.client.first_name or booking.client.username
            )

            return redirect("my_bookings")
    else:
        form = BookingForm(initial=initial_data)

    return render(request, "bookings/booking_form.html", {"form": form})

@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, client__user=request.user)

    # Capture booking details
    lesson_name = booking.lesson_type.name
    booking_date = booking.date
    booking_time = booking.start_time.strftime("%I:%M %p")
    client_email = booking.client.email
    client_first_name = booking.client.first_name

    # Delete booking
    booking.delete()

    # Send cancellation email using Brevo
    send_booking_mail(
        client_email,
        {
            "first_name": client_first_name,
            "lesson_type": lesson_name,
            "date": booking_date.strftime('%b %d, %Y'),
            "start_time": booking_time,
            "subject": "Lesson Cancellation Confirmation"
        },
        custom_message=f"Hi {client_first_name},\n\nYour {lesson_name} lesson scheduled for {booking_date} at {booking_time} has been successfully cancelled.\n\nThank you!"
    )

    messages.success(request, "Your booking has been cancelled. A confirmation email has been sent.")
    return redirect("my_bookings")


# ==========================
# CUSTOM LOGIN
# ==========================
class CustomLoginView(LoginView):
    authentication_form = CustomLoginForm
    template_name = "bookings/login.html"

    def form_invalid(self, form):
        # Called when username or password is incorrect
        messages.error(self.request, "Invalid username or password")
        return super().form_invalid(form)

    def form_valid(self, form):
        response = super().form_valid(form)

        if form.cleaned_data.get("remember_me"):
            self.request.session.set_expiry(60*60*24*30)  # 30 days
        else:
            # Delete everything except the current user login
            self.request.session.set_expiry(0)
       

        return response
    def dispatch(self, request, *args, **kwargs):
    # If the session has expired, user will be logged out automatically.
    # Only redirect if you *really* want to prevent logged-in users from seeing login page.
        if request.user.is_authenticated and request.session.get_expiry_age() > 0:
            if request.user.is_staff:
                return redirect('admin:index')
            return redirect('client_menu')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('admin:index') if self.request.user.is_staff else reverse_lazy('client_menu')
# ==========================
# FORGOT USERNAME
# ==========================
def forgot_username(request):
    form = ForgotUsernameForm(request.POST or None)
    message_sent = False
    login_url = request.build_absolute_uri(reverse('login'))

    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data['email']
        users = User.objects.filter(email=email)

        if not users.exists():
            form.add_error('email', "No user found with that email.")
        else:
            # Send all usernames associated with this email
            usernames = [user.username for user in users]
            username_list = "\n".join(usernames)
             # Use your Brevo email function
            send_booking_mail(
                client_email=email,
                booking_details={
                    "first_name": "there",
                    "subject": "Your Username(s)",
                },
                custom_message=f"Hello!\n\nThis is the username(s) associated with this email:\n{username_list}\n\nLog back in here: {login_url}"
            )
            message_sent = True

    return render(request, "bookings/forgot_username.html", {"form": form, "message_sent": message_sent})


# ==========================
# SEND BOOKING EMAIL (Optional)
# ==========================

def send_booking_mail(client_email, booking_details=None, custom_message=None, client_name=None):
    """
    Send email via Brevo. client_name is required for recipient name.
    """
    if client_name is None:
        client_name = booking_details.get("first_name") if booking_details else client_email.split("@")[0]

    message_text = custom_message or f"""
Hello {booking_details['first_name'] if booking_details else client_name},

Your lesson has been booked!
"""
    payload = {
        "sender": {"name": "Developmental Baseball", "email": "noreply@coachalvarez44.com"},
        "to": [{"email": client_email, "name": client_name}],  # ✅ include name here
        "subject": booking_details.get("subject", "Booking Confirmation") if booking_details else "No Subject",
        "textContent": message_text
    }

    import requests
    from django.conf import settings

    response = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        json=payload,
        headers={"api-key": settings.BREVO_API_KEY, "Content-Type": "application/json"},
        timeout=10
    )
    response.raise_for_status()
    return response.json()


def send_24hr_booking_reminder(booking):
    import requests
    from django.conf import settings

    client_email = booking.client.email

    text = (
        f"Hello {booking.client.first_name},\n\n"
        f"This is a 24-hour reminder that you have a lesson on:\n"
        f"Date: {booking.date.strftime('%b %d, %Y')}\n"
        f"Time: {booking.start_time.strftime('%I:%M %p')}\n"
        f"Lesson Type: {booking.lesson_type.name}\n\n"
        "Thank you! See you tomorrow!"
    )

    payload = {
        "sender": {"name": "Developmental Baseball", "email": "noreply@coachalvarez44.com"},
        "to": [{"email": client_email}],
        "subject": f"24-Hour Reminder: {booking.lesson_type.name} Lesson",
        "textContent": text
    }

    response = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        json=payload,
        headers={"api-key": settings.BREVO_API_KEY, "Content-Type": "application/json"},
        timeout=10
    )
    response.raise_for_status()
    print(f"24-hour reminder sent to {client_email}!")


from datetime import datetime, timedelta
import requests
from django.conf import settings

def send_24hr_email_reminder(booking):
    if not booking.client or not booking.client.email:
        return "No client email found"

    start_time = booking.start_time.strftime('%I:%M %p')
    end_time = (datetime.combine(booking.date, booking.start_time) + timedelta(minutes=booking.lesson_type.duration)).strftime('%I:%M %p')
    custom_message = (
        f"Hi {booking.client.first_name},\n\n"
        f"This is a 24-hour reminder that you have a {booking.lesson_type.name} lesson on:\n"
        f"Date: {booking.date.strftime('%b %d, %Y')}\n"
        f"Time: {start_time} - {end_time}\n\n"
        "Thank you! See you tomorrow!"
    )

    booking_details = {
        "first_name": booking.client.first_name,
        "lesson_type": booking.lesson_type.name,
        "date": booking.date.strftime('%b %d, %Y'),
        "start_time": start_time,
        "end_time": end_time,
        "subject": f"24-Hour Reminder: {booking.lesson_type.name} Lesson"
    }

    send_booking_mail(booking.client.email, booking_details, custom_message=custom_message)
    return f"24-hour reminder sent to {booking.client.email}"


@csrf_exempt
@login_required
def register_device_token(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            token = data.get("device_token")
            if not token:
                return JsonResponse({"status": "error", "message": "No token provided."}, status=400)

            try:
                client = Client.objects.get(user=request.user)
            except Client.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Client record not found."}, status=404)

            client.device_token = token
            client.save()
            return JsonResponse({"status": "success", "message": "Device token saved."})
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON."}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)


def send_sms(phone_number, message, client_obj=None):
    # Only send if client opted in
    if client_obj and not client_obj.sms_opt_in:
        print("Client has not opted in. Skipping SMS.")
        return

    twilio_client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    twilio_client.messages.create(
        to=phone_number,
        from_=settings.TWILIO_PHONE_NUMBER,  # or messaging_service_sid=settings.TWILIO_MESSAGING_SERVICE_SID
        body=message
    )
    
def send_cancellation_sms(booking):
    sms_body = (
        f"{booking.client.first_name}, {booking.lesson_type.name} lesson has been cancelled.\n\n"
        f"Date: {booking.date.strftime('%b %d, %Y')}\n"
        f"Time: {booking.start_time.strftime('%I:%M %p')}\n\n"
        "If this was a mistake, please rebook online. Thank you!"
    )
    return send_sms(booking.client.phone, sms_body)
    
def send_24hr_sms_reminder(booking):
    sms_body = (
        f"This is a 24hr Reminder: You have a {booking.lesson_type.name} lesson tomorrow!\n"
        f"Date: {booking.date.strftime('%b %d, %Y')}\n"
        f"Time: {booking.start_time.strftime('%I:%M %p')}"
    )
    return send_sms(booking.client.phone, sms_body)

@login_required
def update_sms_opt_in(request):
    if request.method == "POST":
        client = Client.objects.get(user=request.user)
        opt_in_value = request.POST.get("sms_opt_in") == "true"
        client.sms_opt_in = opt_in_value
        client.save()
        return JsonResponse({"status": "success", "sms_opt_in": client.sms_opt_in})
    return JsonResponse({"status": "error"}, status=400)

def send_sms_confirmation(client_obj, message):
    if not client_obj.sms_opt_in or not client_obj.phone:
        return  # don't send if they opted out

    twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    
    twilio_client.messages.create(
        to=client_obj.phone,
        from_=settings.TWILIO_PHONE_NUMBER,  # or messaging_service_sid=settings.TWILIO_MESSAGING_SERVICE_SID
        body=message
    )

class CustomPasswordResetView(PasswordResetView):
    template_name = 'bookings/registration/password_reset.html'
    success_url = reverse_lazy('password_reset_done')

    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        """
        Override to send email via Brevo and include recipient 'name'
        """
        user = context['user']
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_url = f"https://coachalvarez44.com/reset/{uid}/{token}/"

        recipient_name = user.first_name or user.username

        # Send via your Brevo function
        send_booking_mail(
        client_email=user.email,
        client_name=recipient_name,  # ✅ use it here
        booking_details={
            "first_name": recipient_name,
            "subject": "Password Reset Request",
        },
        custom_message=(
            f"Hi {recipient_name},\n\n"
            "We received a request to reset your password.\n\n"
            f"Click the link below to reset it:\n{reset_url}\n\n"
            "If you didn’t request this, you can ignore this email."
        )
    )