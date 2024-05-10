from typing import Any

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.db import models

from apps.category.models import Category
from apps.common.models import BaseModel
from apps.common.utils import uuid4_generator


class AccountManager(BaseUserManager["Account"]):
    def create_user(self, email: str, password: str, **extra_fields: Any) -> Any:
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, **extra_fields: Any) -> Any:
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


def upload_to_s3_account(instance: models.Model, filename: str) -> str:
    return f"images/account/{uuid4_generator(length=8)} + {filename}"


class Account(AbstractBaseUser, PermissionsMixin, BaseModel):
    email = models.EmailField(max_length=100, unique=True, null=False, blank=False)
    nickname = models.CharField(max_length=15, unique=True)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=7, null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    region = models.CharField(max_length=30, null=True, blank=True)
    phone = models.CharField(max_length=15)
    grade = models.CharField(max_length=10, null=True, blank=True)
    # interest_cate = models.ManyToManyField(Category, blank=True)
    profile_img = models.ImageField(upload_to=upload_to_s3_account, null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    objects = AccountManager()
