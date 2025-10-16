from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta, date

class BlockedTime(models.Model):
    date = models.DateField(blank=True, null=True)  # allow form to skip this
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    reason = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['date', 'start_time']

    def clean(self):
        # Remove this block:
        # if self.date is None:
        #     raise ValidationError("Please provide a date.")

        # If both times are empty → full-day block, skip time checks
        if self.start_time is None and self.end_time is None:
            return

        # If one time is set but not the other → invalid
        if self.start_time is None or self.end_time is None:
            raise ValidationError("Both start and end times must be set, or leave both empty for a full-day block.")

        # Validate normal time range
        if self.start_time >= self.end_time:
            raise ValidationError("End time must be after start time.")
        
    def __str__(self):
        if self.start_time and self.end_time:
            return f"{self.date} from {self.start_time} to {self.end_time}"
        return f"{self.date} (Full-day block)"

class LessonType(models.Model):
    DURATION_CHOICES = [
        (30, '30 Minutes'),
        (60, '1 Hour'),
    ]

    name = models.CharField(max_length=50)  # e.g., Hitting
    duration = models.PositiveBigIntegerField(choices=DURATION_CHOICES)
    price = models.PositiveIntegerField()  # store price directly

    def __str__(self):
        return f"{self.name} ({self.get_duration_display()} - ${self.price})"

class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    device_token = models.TextField(blank=True, null=True)
    sms_opt_in = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Booking(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='bookings')
    lesson_type = models.ForeignKey(LessonType, on_delete=models.PROTECT)
    date = models.DateField()
    start_time = models.TimeField()
    additional_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        ordering = ['date', 'start_time']
        constraints = [
            models.UniqueConstraint(fields=['client','date', 'start_time'], 
            name='unique_booking_per_client_start'
            )
        ]

    def __str__(self):
        return f"{self.client} - {self.date} {self.start_time}"
    
    def clean(self):
        from .models import BlockedTime
        # Ensure both date and start_time are provided
        if self.date is None:
            raise ValidationError("Please select a date.")
        if self.start_time is None:
            raise ValidationError("Please select a start time.")

        today = date.today()
        now = datetime.now()
        booking_datetime = datetime.combine(self.date, self.start_time)

        # Validate date is not in the past
        if booking_datetime < now:
            raise ValidationError("Cannot book in the past.")
        
        today = date.today()
        end_of_current_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        seven_days_before_end = end_of_current_month - timedelta(days=7)
        next_month_start = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
        end_of_next_month = (next_month_start.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        if not ((today <= self.date <= end_of_current_month) or
                (today >= seven_days_before_end and next_month_start <= self.date <= end_of_next_month)):
            raise ValidationError(
                "You can only book within the current month, or next month starting 7 days before the month ends."
            )

        # Require bookings to be made at least 24 hours in advance
        if booking_datetime < now + timedelta(hours=24):
            raise ValidationError("Bookings must be made at least 24 hours in advance.")

        # Add checks for overlapping bookings
        start_dt = datetime.combine(self.date, self.start_time)
        end_dt = start_dt + timedelta(minutes=self.lesson_type.duration)  # default duration assumed 1 hour

        # Check against blocked times
        full_day_block = BlockedTime.objects.filter(date=self.date, start_time__isnull=True, end_time__isnull=True)
        if full_day_block.exists():
            raise ValidationError("This day is blocked and cannot be booked.")
        
        # Check specific blocked times
        time_blocks = BlockedTime.objects.filter(date=self.date)
        for block in time_blocks:
            if block.start_time and block.end_time:
                bstart = datetime.combine(block.date, block.start_time)
                bend = datetime.combine(block.date, block.end_time)
                if start_dt < bend and end_dt > bstart:
                    raise ValidationError(f"This time overlaps with a blocked period: {block.start_time} to {block.end_time}")


        overlapping = Booking.objects.filter(date=self.date).exclude(pk=self.pk)
        for b in overlapping:
            bstart = datetime.combine(b.date, b.start_time)
            bend = bstart + timedelta(minutes=b.lesson_type.duration)
            if not(end_dt <= bstart or start_dt >= bend):
                raise ValidationError('This time overlaps with another booking')
        return super().clean()

    def __str__(self):
        return f"{self.client} - {self.date} {self.start_time}"