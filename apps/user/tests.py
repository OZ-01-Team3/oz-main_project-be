import base64
import io
from io import BytesIO
from unittest import mock
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.user.models import Account


class AccountModelTests(TestCase):
    def setUp(self) -> None:
        # Given
        self.account = get_user_model()
        self.email = "user@email.com"
        self.password = "felsejfla234234"
        self.nickname = "nick"
        self.phone = "1234"

    def test_create_user_successful(self) -> None:
        # When
        user = self.account.objects.create_user(
            email=self.email, password=self.password, nickname=self.nickname, phone=self.phone
        )
        # Then
        self.assertEqual(user.email, self.email)
        self.assertTrue(user.check_password(self.password))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_without_email(self) -> None:
        with self.assertRaises(ValueError):
            self.account.objects.create_user(email="", password=self.password, nickname=self.nickname, phone=self.phone)

    def test_create_superuser(self) -> None:
        superuser = self.account.objects.create_superuser(email=self.email, password=self.password)
        self.assertEqual(superuser.email, self.email)
        self.assertTrue(superuser.check_password(self.password))
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_active)

    def test_create_superuser_without_staff(self) -> None:
        with self.assertRaises(ValueError):
            self.account.objects.create_superuser(email=self.email, password=self.password, is_staff=False)

    def test_create_superuser_without_superuser(self) -> None:
        with self.assertRaises(ValueError):
            self.account.objects.create_superuser(email=self.email, password=self.password, is_superuser=False)


class SignupViewTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.url = reverse("signup")
        self.data = {
            "email": "dup@example.com",
            "password": "duplicate",
            "nickname": "nickname",
            "phone": "010-1234-1234",
        }
        self.user = Account.objects.create(**self.data)

    def test_signup_successful(self) -> None:
        # Given
        data = {
            "email": "user@email.com",
            "password1": "felsejfla234234",
            "password2": "felsejfla234234",
            "nickname": "nick",
            "phone": "1234",
        }
        # When
        res = self.client.post(self.url, data)
        res_data = res.json()
        # Then
        self.assertEqual(res.status_code, 201)
        self.assertTrue("access" in res_data)
        self.assertTrue("refresh" in res_data)
        self.assertTrue(Account.objects.filter(email=data["email"]).exists())

    def test_signup_without_email(self) -> None:
        data = {
            "password1": "felsejfla234234",
            "password2": "felsejfla234234",
            "nickname": "nick",
            "phone": "1234",
        }
        res = self.client.post(self.url, data)
        self.assertEqual(res.status_code, 400)

    def test_signup_without_nickname(self) -> None:
        data = {
            "email": "user@email.com",
            "password1": "felsejfla234234",
            "password2": "felsejfla234234",
            "phone": "1234",
        }
        res = self.client.post(self.url, data)
        self.assertEqual(res.status_code, 400)

    def test_signup_without_phone(self) -> None:
        data = {
            "email": "user@email.com",
            "password1": "felsejfla234234",
            "password2": "felsejfla234234",
            "nickname": "nick",
        }
        res = self.client.post(self.url, data)
        self.assertEqual(res.status_code, 400)

    def test_signup_with_different_password(self) -> None:
        data = {
            "email": "user@email.com",
            "password1": "felsejfla234234",
            "password2": "felejfla234234",
            "nickname": "nick",
            "phone": "1234",
        }
        res = self.client.post(self.url, data)
        self.assertEqual(res.status_code, 400)

    def test_signup_with_short_password(self) -> None:
        data = {
            "email": "user@email.com",
            "password1": "fel2348",
            "password2": "fel2348",
            "nickname": "nick",
            "phone": "1234",
        }
        res = self.client.post(self.url, data)
        self.assertEqual(res.status_code, 400)

    def test_signup_with_duplicate_email(self) -> None:
        data = {
            "email": "dup@example.com",
            "password1": "fel2348",
            "password2": "fel2348",
            "nickname": "nick",
            "phone": "1234",
        }
        res = self.client.post(self.url, data)
        self.assertEqual(res.status_code, 400)

    def test_signup_with_duplicate_nickname(self) -> None:
        data = {
            "email": "user@email.com",
            "password1": "fel2348",
            "password2": "fel2348",
            "nickname": "nickname",
            "phone": "1234",
        }
        res = self.client.post(self.url, data)
        self.assertEqual(res.status_code, 400)


class LoginViewTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.url = reverse("login")
        data = {
            "email": "user@email.com",
            "password": "fels3570",
            "nickname": "nick",
            "phone": "1234",
        }
        self.user = Account.objects.create_user(**data)

    def test_valid_login(self) -> None:
        data = {"email": "user@email.com", "password": "fels3570"}
        res = self.client.post(self.url, data, format="json")
        res_data = res.json()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue("access" in res_data)
        self.assertTrue("refresh" in res_data)

    def test_login_with_wrong_password(self) -> None:
        data = {"email": "user@email.com", "password": "wrong"}
        res = self.client.post(self.url, data, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_email_field(self) -> None:
        data = {"password": "fels3570"}
        res = self.client.post(self.url, data, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_password_field(self) -> None:
        data = {
            "email": "user@email.com",
        }
        res = self.client.post(self.url, data, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class LogoutViewTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.url = reverse("rest_logout")
        data = {
            "email": "user@email.com",
            "password": "fels3570",
            "nickname": "nick",
            "phone": "1234",
        }
        self.user = Account.objects.create_user(**data)
        # self.refresh = RefreshTokeddn.for_user(self.user)
        # self.token = TokenModel.objects.create(user=self.user)
        # self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token.key}")

    def test_logout_authenticated_user(self) -> None:
        self.client.force_login(self.user)
        res = self.client.post(self.url)
        res_data = res.json()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res_data["detail"], "Successfully logged out.")


class UserDetailViewTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.url = reverse("rest_user_details")
        self.data = {
            "email": "user@email.com",
            "password": "fels3570",
            "nickname": "nick",
            "phone": "1234",
            "age": 20,
            "gender": "female",
            "height": 190,
            "region": "Seoul",
        }
        self.user = get_user_model().objects.create(**self.data)
        self.client.force_login(self.user)
        self.token = AccessToken.for_user(self.user)

    def generate_image_file(self) -> BytesIO:
        image = Image.new("RGBA", size=(100, 100), color=(100, 100, 100))
        file = BytesIO(image.tobytes())
        image.save(file, format="PNG")
        file.name = "test.png"
        file.seek(0)
        return file

    def generate_image_to_base64(self) -> bytes:
        file = BytesIO()
        image = Image.new("RGBA", size=(100, 100), color=(155, 0, 0))
        image.save(file, "png")
        img_str = base64.b64encode(file.getvalue())
        return img_str

    def test_get_user_info(self) -> None:
        res = self.client.get(self.url, headers={"Authorization": f"Bearer {self.token}"})
        res_data = res.json()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res_data.get("email"), self.data["email"])
        self.assertEqual(res_data.get("nickname"), self.data["nickname"])
        self.assertEqual(res_data.get("phone"), self.data["phone"])
        self.assertEqual(res_data.get("age"), self.data["age"])
        self.assertEqual(res_data.get("gender"), self.data["gender"])
        self.assertEqual(res_data.get("height"), self.data["height"])
        self.assertEqual(res_data.get("region"), self.data["region"])

    def test_update_user_info(self) -> None:
        data = {
            "email": "update@email.com",
            "nickname": "updatednickname",
            "password1": "ejfeiwlfjlsf",
            "password2": "ejfeiwlfjlsf",
            "phone": "0987654321",
            "age": 30,
            "gender": "female",
            "height": 170,
            "region": "Gyeongi",
            "grade": "Silver",
        }
        res = self.client.put(self.url, data, headers={"Authorization": f"Bearer {self.token}"})
        res_data = res.json()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res_data["email"], data["email"])
        self.assertEqual(res_data["nickname"], data["nickname"])
        self.assertEqual(res_data["phone"], data["phone"])
        self.assertEqual(res_data["age"], data["age"])
        self.assertEqual(res_data["gender"], data["gender"])
        self.assertEqual(res_data["height"], data["height"])
        self.assertEqual(res_data["region"], data["region"])
        self.assertEqual(res_data["grade"], data["grade"])

        # DB에도 업데이트 됐는지 확인
        updated_user = Account.objects.get(id=self.user.id)
        self.assertEqual(updated_user.email, data["email"])
        self.assertEqual(updated_user.nickname, data["nickname"])
        self.assertEqual(updated_user.phone, data["phone"])
        self.assertEqual(updated_user.age, data["age"])
        self.assertEqual(updated_user.gender, data["gender"])
        self.assertEqual(updated_user.height, data["height"])
        self.assertEqual(updated_user.region, data["region"])
        self.assertEqual(updated_user.grade, data["grade"])
        self.assertTrue(updated_user.check_password(str(data["password1"])))

    def test_update_user_info_with_duplicate_nickname(self) -> None:
        existing_nickname = "existing"
        Account.objects.create_user(email="dfdf@dfdf.com", password="password", nickname=existing_nickname)
        data = {"nickname": existing_nickname}
        res = self.client.patch(self.url, data, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_user_info_with_same_nickname(self) -> None:
        data = {"nickname": self.data["nickname"]}
        res = self.client.patch(self.url, data, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_update_user_info_with_different_passwords(self) -> None:
        data = {"password1": "password1", "password2": "password2"}
        res = self.client.patch(self.url, data, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # def test_upload_profile_image(self) -> None:
    #     image_file = self.generate_image_file()
    #     data = {"profile_img": image_file}
    #     res = self.client.patch(self.url, data, format="multipart")
    #     self.assertEqual(res.status_code, status.HTTP_200_OK)

    # TODO: 테스트 돌릴 때마다 S3에 올라감 이슈
    # def test_update_profile_image(self) -> None:
    #     profile_img = self.generate_image_file()
    #     data = {
    #         "email": "user@email.com",
    #         "profile_img": profile_img
    #     }
    #     # Account.objects.create(**data)
    #     res = self.client.patch(self.url, data, format="multipart")
    #     image_file = self.generate_image_file()
    #     data = {"email": "user@email.com", "profile_img": image_file}
    #     res = self.client.patch(self.url, data, format="multipart")
    #     self.assertEqual(res.status_code, status.HTTP_200_OK)


class DeleteUserViewTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.url = reverse("delete-user")
        data = {
            "email": "user@email.com",
            "password": "fels3570",
            "nickname": "nick",
            "phone": "1234",
        }
        self.user = Account.objects.create_user(**data)
        self.client.force_login(self.user)
        self.token = AccessToken.for_user(self.user)

    def test_delete_user(self) -> None:
        res = self.client.delete(self.url, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        user_exists = Account.objects.filter(email=self.user.email).exists()
        self.assertFalse(user_exists)


class SendCodeViewTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.url = reverse("send-code")
        self.email = "test@example.com"

    @patch("apps.user.views.send_email")
    def test_send_code(self, mock_send_email: MagicMock) -> None:
        data = {"email": self.email}
        res = self.client.post(self.url, data, format="json")
        # 이메일 보내졌는지 확인
        mock_send_email.assert_called_once_with(self.email, mock.ANY)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # 캐시에 저장됐는지 확인
        confirmation_code = cache.get(self.email)
        self.assertIsNotNone(confirmation_code)
        self.assertEqual(len(confirmation_code), int(settings.CONFIRM_CODE_LENGTH))

    def test_send_code_with_duplicate_email(self) -> None:
        data = {
            "email": "user@email.com",
            "password": "fels3570",
            "nickname": "nick",
            "phone": "1234",
        }
        self.user = Account.objects.create(**data)
        data = {"email": data["email"]}
        res = self.client.post(self.url, data, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class ConfirmEmailViewTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.url = reverse("confirm-email")
        self.email = "test@example.com"
        self.code = "1234567"
        cache.set(self.email, self.code)

    def test_confirm_email(self) -> None:
        data = {"email": self.email, "code": self.code}
        res = self.client.post(self.url, data, format="json")
        res_data = res.json()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res_data.get("message"), "Email confirmation successful.")
        # cache 지워졌는지 확인
        cached_code = cache.get(self.email)
        self.assertIsNone(cached_code)

    def test_confirm_email_with_expired_code(self) -> None:
        data = {"email": self.email, "code": self.code}
        cache.delete(self.email)
        res = self.client.post(self.url, data)
        res_data = res.json()
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res_data.get("error"), "The confirmation code has expired or does not exist.")

    def test_confirm_email_with_invalid_code(self) -> None:
        data = {"email": self.email, "code": "invalidcode"}
        res = self.client.post(self.url, data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_email_with_too_long_code(self) -> None:
        data = {"email": self.email, "code": "toolongcode"}
        res = self.client.post(self.url, data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class TokenVerifyViewTests(TestCase):
    pass


class TokenRefreshViewTests(TestCase):
    pass
