from django import forms
from .models import Booking, LessonType, Client
from datetime import date, time, datetime, timedelta
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import admin
from .models import BlockedTime
from django.contrib.auth.forms import AuthenticationForm


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(required=False)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        if phone:
            # Remove non-digit characters
            digits = "".join(c for c in phone if c.isdigit())

            # If 10 digits, prepend +1
            if len(digits) == 10:
                digits = "+1" + digits
            # If already 11 digits and starts with 1, prepend +
            elif len(digits) == 11 and digits.startswith("1"):
                digits = "+" + digits
            else:
                raise forms.ValidationError("Please enter a valid US phone number")

            phone = digits
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            # Use cleaned phone value here
            phone_number = self.cleaned_data.get("phone")
            Client.objects.create(
                user=user,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                phone=phone_number
            )
        return user


from django import forms
from .models import Booking, LessonType
from datetime import date, timedelta

class BookingForm(forms.ModelForm):
    lesson_type = forms.ModelChoiceField(queryset=LessonType.objects.all())
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'readonly': 'readonly'})
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'step': 1800, 'readonly': 'readonly'})
    )

    def clean_date(self):
        print("BookingForm.clean_date called!", self.cleaned_data.get('date'))
        return self.cleaned_data.get('date')

    class Meta:
        model = Booking
        fields = ('lesson_type', 'date', 'start_time', 'additional_notes')

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        booking_date = cleaned_data.get('date')
        today = date.today()

        if not start_time:
            raise forms.ValidationError("Please select a valid time.")

        # Skip 30-min increment check if time came from initial
        if 'start_time' in self.initial and start_time == self.initial['start_time']:
            pass
        elif start_time.minute % 30 != 0:
            raise forms.ValidationError("Start time must be in 30-minute increments.")

        # No past bookings
        if booking_date and booking_date < today:
            raise forms.ValidationError("Cannot book in the past.")

        return cleaned_data

class ForgotUsernameForm(forms.Form):
    email = forms.EmailField(label="Enter your email address:")

    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("No user is registered with this email.")
        return email

class CustomLoginForm(AuthenticationForm):
    remember_me = forms.BooleanField(required=False, initial=False)

from django import forms
from .models import BlockedTime

class BlockMultipleDaysForm(forms.ModelForm):
    start_date = forms.DateField(label="Start Date", widget=forms.SelectDateWidget)
    end_date = forms.DateField(label="End Date", widget=forms.SelectDateWidget)

    class Meta:
        model = BlockedTime
        fields = ('start_time', 'end_time', 'reason')  # only model fields here

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_time'].required = False
        self.fields['end_time'].required = False

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("End date must be after start date.")
        return cleaned_data
    

class SMSOptInForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['sms_opt_in']
        widgets = {
            'sms_opt_in': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'sms_opt_in': 'I want to receive SMS notifications about my lessons',
        }