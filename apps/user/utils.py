import threading

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from django.utils.safestring import SafeString


class EmailThread(threading.Thread):
    def __init__(self, email: str, verification_code: str) -> None:
        self.subject = render_to_string("user/email/email_confirmation_subject.txt", context={})
        self.subject = SafeString(" ".join(self.subject.splitlines()))  # 두줄 이상이면 메시지 전송 실패
        self.content = render_to_string(
            "user/email/email_confirmation_message.html", context={"code": verification_code}
        )
        self.sender = settings.DEFAULT_FROM_EMAIL
        self.recipient_list = [email]
        threading.Thread.__init__(self)

    def run(self) -> None:
        send_mail(
            subject=self.subject,
            message="",
            from_email=self.sender,
            recipient_list=self.recipient_list,
            html_message=str(self.content),
        )


def send_email(email: str, verification_code: str) -> None:
    EmailThread(email, verification_code).start()


def generate_confirmation_code() -> str:
    return get_random_string(length=int(settings.CONFIRM_CODE_LENGTH))  # TODO: 굳이?


# def send_email(email, verification_code):
#     subject = render_to_string("user/email/email_confirmation_subject.txt", context={})
#     subject = " ".join(subject.splitlines())
#     content = render_to_string("user/email/email_confirmation_message.html", context={"code": verification_code})
#     sender = settings.DEFAULT_FROM_EMAIL
#     recipient_list = [email]
#     send_mail(subject=subject, message="", from_email=sender, recipient_list=recipient_list, html_message=content)
