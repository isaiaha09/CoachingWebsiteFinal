import firebase_admin
from firebase_admin import credentials, messaging
import os
from bookings.models import Client

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cred_path = os.path.join(BASE_DIR, 'firebase', 'developmental-baseball-firebase-cred.json')

cred = credentials.Certificate(cred_path)

if not firebase_admin._apps:
    firebase_app = firebase_admin.initialize_app(cred)
else:
    firebase_app = firebase_admin.get_app()

def send_push_notification(token, title, body):
    """
    token: the FCM device token from the client app
    title: notification title
    body: notification message
    """
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        token=token
    )
    response = messaging.send(message)
    return response

def send_24hr_reminder(booking):
    if booking.client and booking.client.device_token:  # store this token in Client model
        title = "24-Hour Lesson Reminder"
        body = f"Hi {booking.client.first_name}, you have a {booking.lesson_type.name} lesson on {booking.date.strftime('%b %d, %Y')} at {booking.start_time.strftime('%I:%M %p')}."
        send_push_notification(booking.client.device_token, title, body)


def send_test_notification(user):
    try:
        client = Client.objects.get(user=user)
        if not client.device_token:
            return "No device token saved."

        title = "Test Notification"
        body = f"Hi {client.first_name}, this is a test!"
        response = send_push_notification(client.device_token, title, body)
        return f"Notification sent: {response}"
    except Client.DoesNotExist:
        return "Client not found."