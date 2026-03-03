from django.urls import path
from . import views
from django.views.generic import TemplateView




urlpatterns = [
    path('', TemplateView.as_view(template_name='bookings/index.html'), name='index'),
    path('book/', TemplateView.as_view(template_name='bookings/booking.html'), name='booking_portal'),


    # Main Pages

    path('contact/', views.contact, name='contact'),
    path('gallery/', TemplateView.as_view(template_name='bookings/gallery.html'), name='gallery'),
    path('my-story/', TemplateView.as_view(template_name='bookings/my-story.html'), name='my-story'),
    path('credibility/', TemplateView.as_view(template_name='bookings/credibility.html'), name='credibility'),
]
