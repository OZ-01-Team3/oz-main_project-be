import threading

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string


class EmailThread(threading.Thread):
    def __init__(self, email, verification_code) -> None:
        self.subject = render_to_string("account/email/email_confirmation_subject.txt", context={})
        self.subject = " ".join(self.subject.splitlines())
        self.content = render_to_string("account/email/email_verification_message.html", context={"code": verification_code})
        self.sender = settings.DEFAULT_FROM_EMAIL
        self.recipient_list = [email]
        threading.Thread.__init__(self)

    def run(self) -> None:
        send_mail(subject=self.subject, message="", from_email=self.sender, recipient_list=self.recipient_list, html_message=self.content)


def send_email(email, verification_code):
    EmailThread(email, verification_code).start()


def generate_confirmation_code():
    return get_random_string(length=int(settings.CONFIRM_CODE_LENGTH))


# def send_email(email, verification_code):
#     subject = render_to_string("account/email/email_confirmation_subject.txt", context={})
#     subject = " ".join(subject.splitlines())
#     content = render_to_string("account/email/email_verification_message.html", context={"code": verification_code})
#     sender = settings.DEFAULT_FROM_EMAIL
#     recipient_list = [email]
#     send_mail(subject=subject, message="", from_email=sender, recipient_list=recipient_list, html_message=content)
