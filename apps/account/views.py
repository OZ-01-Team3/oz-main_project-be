from django.shortcuts import render
from rest_framework import generics

from apps.account.models import Account


class LoginView(generics.CreateAPIView[Account]):
    pass
