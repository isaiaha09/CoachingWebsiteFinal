from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail import EmailMessage
from django.conf import settings
from sib_api_v3_sdk import ApiClient, Configuration
from sib_api_v3_sdk.api import transactional_emails_api
from sib_api_v3_sdk.models import SendSmtpEmail, SendSmtpEmailTo

class BrevoEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        configuration = Configuration()
        configuration.api_key['api-key'] = settings.BREVO_API_KEY

        api_instance = transactional_emails_api.TransactionalEmailsApi(ApiClient(configuration))

        sent_count = 0
        for message in email_messages:
            try:
                to_list = [SendSmtpEmailTo(email=addr, name='') for addr in message.to]
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
                    print(f"Failed to send email: {e}")
        return sent_count
