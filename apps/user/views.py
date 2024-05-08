# from allauth.account.models import EmailConfirmationHMAC, EmailConfirmation
# from django.http import HttpResponseRedirect
# from rest_framework.permissions import AllowAny
# from rest_framework.views import APIView
#
#
# class ConfirmEmailView(APIView):
#     permission_classes = [AllowAny]
#
#     def get(self, *args, **kwargs):
#         self.object = confirmation = self.get_object()
#         confirmation.confirm(self.request)
#         return HttpResponseRedirect("/")
#
#     def get_object(self, queryset=None):
#         key = self.kwargs.get("key")
#         email_confirmation = EmailConfirmationHMAC.from_key(key)
#         if not email_confirmation:
#             if queryset is None:
#                 queryset = self.get_queryset()
#             try:
#                 email_confirmation = queryset.get(key=key.lower())
#             except EmailConfirmation.DoesNotExist:
#                 return HttpResponseRedirect('/')
#         return email_confirmation
#
#     def get_queryset(self):
#         qs = EmailConfirmation.objects.all_valid()
#         qs = qs.select_related("email_address__user")
#         return qs
