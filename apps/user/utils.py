import threading

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.crypto import get_random_string


class EmailThread(threading.Thread):
    def __init__(self, subject, body, from_email, recipient, fail_silently, html) -> None:
        self.subject = subject
        self.body = body
        self.recipient = recipient
        self.from_email = from_email
        self.fail_silently = fail_silently
        self.html = html
        threading.Thread.__init__(self)

    def run(self) -> None:
        msg = EmailMultiAlternatives(self.subject, self.body, self.from_email, self.recipient)
        if self.html:
            msg.attach_alternative(self.html, "text/html")
        msg.send(self.fail_silently)


def send_mail(subject, body, from_email, recipient, fail_silently=False, html=None, *args, **kwargs):
    EmailThread(subject, body, from_email, recipient, fail_silently, html).start()


def generate_confirmation_code():
    return get_random_string(length=int(settings.CONFIRM_CODE_LENGTH))
