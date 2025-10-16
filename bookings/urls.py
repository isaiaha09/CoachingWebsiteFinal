from django.urls import path, reverse_lazy
from . import views
from .views import CustomLoginView, contact
from django.contrib.auth.views import LogoutView
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView





urlpatterns = [
    path('', TemplateView.as_view(template_name='bookings/index.html'), name='index'),

    path('book-lesson/', views.book_lesson, name='book_lesson'), # shows the form at /bookings/
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('client_menu/', views.client_menu, name='client_menu'),
    path('calendar/json/', views.calendar_view, name='calendar_view'), # JSON data for calendar
    path('calendar/', views.calendar_page, name='calendar_page'), # HTML page
    path('signup/', views.signup, name='signup'),
    path('cancel/<int:booking_id>/', views.cancel_booking, name="cancel_booking"),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='/login/', http_method_names=['get', 'post']), name="logout"),


    # Main Pages

    path('contact/', views.contact, name='contact'),
    path('gallery/', TemplateView.as_view(template_name='bookings/gallery.html'), name='gallery'),
    path('my-story/', TemplateView.as_view(template_name='bookings/my-story.html'), name='my-story'),
    path('credibility/', TemplateView.as_view(template_name='bookings/credibility.html'), name='credibility'),


    # Password reset views with app namespace
    path(
        'password_reset/',
        auth_views.PasswordResetView.as_view(
            template_name='bookings/registration/password_reset.html',
            email_template_name='bookings/registration/password_reset_email.html',
            success_url='/password_reset/done/'
        ),
        name='password_reset'
    ),

    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='bookings/registration/password_reset_done.html'
         ),
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='bookings/registration/password_reset_confirm.html',
             success_url=reverse_lazy('password_reset_complete')
         ),
         name='password_reset_confirm'),

    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='bookings/registration/password_reset_complete.html'
         ),
         name='password_reset_complete'),

    path('forgot_username/', views.forgot_username, name='forgot_username'),

    path('update_sms_opt_in/', views.update_sms_opt_in, name='update_sms_opt_in'),
]
