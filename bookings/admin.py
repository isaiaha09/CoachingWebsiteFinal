from django.contrib import admin
from .models import Client, Booking, LessonType, BlockedTime, DefaultDayHours, TemporaryDefaultOverride
from django import forms
from datetime import timedelta
from .forms import BlockMultipleDaysForm

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone')
    search_fields = ('first_name', 'last_name', 'email')

@admin.register(LessonType)
class LessonTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('client', 'lesson_type', 'date', 'start_time')
    list_filter = ('date', 'lesson_type')
    search_fields = ('client__first_name', 'client__last_name')
    ordering = ('-date', 'start_time')


@admin.register(BlockedTime)
class BlockedTimeAdmin(admin.ModelAdmin):
    form = BlockMultipleDaysForm
    list_display = ('date', 'start_time', 'end_time', 'reason')
    ordering = ('-date',)

    def save_model(self, request, obj, form, change):
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        start_time = form.cleaned_data.get('start_time')
        end_time = form.cleaned_data.get('end_time')
        reason = form.cleaned_data.get('reason')

        if start_date and end_date and start_date != end_date:
            current = start_date
            while current <= end_date:
                BlockedTime.objects.create(
                    date=current,
                    start_time=start_time,
                    end_time=end_time,
                    reason=reason
                )
                current += timedelta(days=1)
        else:
            obj.date = start_date or obj.date
            super().save_model(request, obj, form, change)

@admin.register(DefaultDayHours)
class DefaultDayHoursAdmin(admin.ModelAdmin):
    list_display = ['weekday', 'start_time', 'end_time']  # 'weekday' will show human-readable names
    ordering = ['weekday']

@admin.register(TemporaryDefaultOverride)
class TemporaryDefaultOverrideAdmin(admin.ModelAdmin):
    list_display = ['start_date', 'end_date', 'start_time', 'end_time', 'reason']