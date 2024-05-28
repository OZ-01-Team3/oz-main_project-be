import re
import uuid

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import UnreadablePostError
from django.middleware.csrf import CsrfViewMiddleware, CSRF_SESSION_KEY, _check_token_format, CSRF_TOKEN_LENGTH, \
    _unmask_cipher_token, InvalidTokenFormat, RejectRequest, REASON_NO_CSRF_COOKIE, REASON_CSRF_TOKEN_MISSING, \
    _does_token_match, REASON_BAD_ORIGIN, _add_new_csrf_cookie


def uuid4_generator(length: int) -> str:
    return uuid.uuid4().hex[:length]


class CustomCsrfViewMiddleware(CsrfViewMiddleware):
    def _get_secret(self, request):
        if settings.CSRF_USE_SESSIONS:
            try:
                csrf_secret = request.session.get(CSRF_SESSION_KEY)
            except AttributeError:
                raise ImproperlyConfigured(
                    "CSRF_USE_SESSIONS is enabled, but request.session is not "
                    "set. SessionMiddleware must appear before CsrfViewMiddleware "
                    "in MIDDLEWARE."
                )
        else:
            try:
                # csrf_secret = request.COOKIES[settings.CSRF_COOKIE_NAME]
                data = request.headers.get("Cookie")
                match = re.search(r'csrftoken=([^;]+)', str(data))
                if match:
                    csrf_secret = match.group(1)
                else:
                    raise KeyError
            except KeyError:
                csrf_secret = None
            else:
                _check_token_format(csrf_secret)
        if csrf_secret is None:
            return None
        if len(csrf_secret) == CSRF_TOKEN_LENGTH:
            csrf_secret = _unmask_cipher_token(csrf_secret)
        return csrf_secret

    def _check_token(self, request):
        try:
            csrf_secret = self._get_secret(request)
        except InvalidTokenFormat as exc:
            raise RejectRequest(f"CSRF cookie {exc.reason}.")

        if csrf_secret is None:
            raise RejectRequest(REASON_NO_CSRF_COOKIE)

        request_csrf_token = ""
        if request.method == "POST":
            try:
                request_csrf_token = request.POST.get("csrfmiddlewaretoken", "")
            except UnreadablePostError:
                pass

        if request_csrf_token == "":
            try:
                request_csrf_token = request.META[settings.CSRF_HEADER_NAME]
            except KeyError:
                raise RejectRequest(REASON_CSRF_TOKEN_MISSING)
            token_source = settings.CSRF_HEADER_NAME
        else:
            token_source = "POST"

        try:
            _check_token_format(request_csrf_token)
        except InvalidTokenFormat as exc:
            reason = super()._bad_token_message(exc.reason, token_source)
            raise RejectRequest(reason)

        if not _does_token_match(request_csrf_token, csrf_secret):
            reason = super()._bad_token_message("incorrect", token_source)
            raise RejectRequest(reason)

    def process_request(self, request):
        try:
            csrf_secret = self._get_secret(request)
        except InvalidTokenFormat:
            _add_new_csrf_cookie(request)
        else:
            if csrf_secret is not None:
                request.META["CSRF_COOKIE"] = csrf_secret

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if getattr(request, "csrf_processing_done", False):
            return None

        if getattr(callback, "csrf_exempt", False):
            return None

        if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
            return super()._accept(request)

        if getattr(request, "_dont_enforce_csrf_checks", False):
            return super()._accept(request)

        if "HTTP_ORIGIN" in request.META:
            if not super()._origin_verified(request):
                return super()._reject(
                    request, REASON_BAD_ORIGIN % request.META["HTTP_ORIGIN"]
                )
        elif request.is_secure():
            try:
                super()._check_referer(request)
            except RejectRequest as exc:
                return super()._reject(request, exc.reason)

        try:
            self._check_token(request)
        except RejectRequest as exc:
            return super()._reject(request, exc.reason)

        return super()._accept(request)
