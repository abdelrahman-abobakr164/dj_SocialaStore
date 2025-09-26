from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task
def send_mails_to_clients(subject, message, to_client_email):
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[to_client_email],
        fail_silently=False,
    )

    return None
