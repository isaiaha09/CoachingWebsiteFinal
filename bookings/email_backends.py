from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail import EmailMessage
from django.conf import settings
from sib_api_v3_sdk import ApiClient, Configuration
from sib_api_v3_sdk.api import transactional_emails_api
from sib_api_v3_sdk.models import SendSmtpEmail, SendSmtpEmailTo
import logging

logger = logging.getLogger(__name__)

# ---------------------------
# Django Email Backend
# ---------------------------
class BrevoEmailBackend(BaseEmailBackend):
    """Optional: Django email backend for general emails."""
    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        configuration = Configuration()
        configuration.api_key['api-key'] = settings.BREVO_API_KEY
        api_instance = transactional_emails_api.TransactionalEmailsApi(ApiClient(configuration))

        sent_count = 0
        for message in email_messages:
            try:
                to_list = []
                for addr in message.to:
                    # Use the recipient name from the message object if available, otherwise fallback to email username
                    recipient_name = getattr(message, 'recipient_name', None) or addr.split('@')[0]
                    to_list.append(SendSmtpEmailTo(email=addr, name=recipient_name))

                email = SendSmtpEmail(
                    to=to_list,
                    sender={'email': settings.EMAIL_HOST_USER, 'name': 'Developmental Baseball'},
                    subject=message.subject,
                    html_content=message.body,
                )
                api_instance.send_transac_email(email)
                sent_count += 1
            except Exception as e:
                if not self.fail_silently:
                    logger.error(f"Failed to send email to {message.to}: {e}", exc_info=True)
        return sent_count


# ---------------------------
# Helper function for sending booking emails
# ---------------------------
def send_booking_mail(client_email, client_name, booking_details=None, custom_message=None):
    """
    Send email via Brevo. client_name is required for recipient name.
    """
    configuration = Configuration()
    configuration.api_key['api-key'] = settings.BREVO_API_KEY
    api_instance = transactional_emails_api.TransactionalEmailsApi(ApiClient(configuration))

    to_list = [SendSmtpEmailTo(email=client_email, name=client_name)]
    email = SendSmtpEmail(
        to=to_list,
        sender={'email': settings.EMAIL_HOST_USER, 'name': 'Developmental Baseball'},
        subject=booking_details.get('subject') if booking_details else "No Subject",
        html_content=custom_message or (
            f"Hello {client_name},\n\n"
            "Your lesson has been booked!"
        )
    )

    try:
        response = api_instance.send_transac_email(email)
        logger.info(f"Email sent to {client_email}, Brevo response: {response}")
        return response
    except Exception as e:
        logger.error(f"Failed to send email to {client_email}: {e}", exc_info=True)
        # Re-raise so Django logs it properly
        raise