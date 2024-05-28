import random
from datetime import datetime
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

from apps.category.models import Category
from apps.chat.models import Chatroom
from apps.product.models import Product

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test data with a specified number of chatrooms and associated users.'

    def handle(self, *args: Any, **kwargs: Any) -> None:
        try:
            self.stdout.write(self.style.MIGRATE_LABEL('테스트에 사용할 채팅방의 수를 입력해주세요.'))
            input_num = input()
            if not input_num.isdigit():
                raise CommandError('숫자만 입력해주세요.')
            chatroom_number = int(input_num)
            if chatroom_number < 1:
                raise CommandError('1 이상의 수를 입력해 주세요.')
            for i in range(0, chatroom_number * 2, 2):
                # 테스트를 진행할 두 유저 생성
                user1, created1 = User.objects.get_or_create(
                    email=f"test{i}@example.com",
                    nickname=f'test_user{i}',
                )
                user1.set_password("password123@")
                user1.save()

                if created1:
                    self.stdout.write(self.style.SUCCESS(f'Successfully created user: {user1.nickname}'))
                else:
                    self.stdout.write(self.style.WARNING(f'User already exists: {user1.nickname}'))

                user2, created2 = User.objects.get_or_create(
                    email=f"test{i+1}@example.com",
                    nickname=f'test_user{i+1}',
                )
                user2.set_password("password123@")
                user2.save()

                if created2:
                    self.stdout.write(self.style.SUCCESS(f'Successfully created user: {user2.nickname}'))
                else:
                    self.stdout.write(self.style.WARNING(f'User already exists: {user2.nickname}'))

                # category 모델 생성
                category, created3 = Category.objects.get_or_create(
                    name=f'test-category-{i}'
                )
                if created3:
                    self.stdout.write(self.style.SUCCESS(f'Successfully created category: {category.name}'))
                else:
                    self.stdout.write(self.style.WARNING(f'category already exists: {category.name}'))

                # product 모델 생성
                product, created4 = Product.objects.get_or_create(
                    name=f'test product-{i/2}',
                    product_category=category,
                    lender=user1,
                    purchase_date=datetime.now(),
                    purchase_price=random.randint(10000, 100000),
                    rental_fee=random.randint(3000, 5000),
                    condition="good"
                )
                if created3:
                    self.stdout.write(self.style.SUCCESS(f'Successfully created category: {product.name}'))
                else:
                    self.stdout.write(self.style.WARNING(f'category already exists: {product.name}'))

                # 테스트를 진행할 두 유저가 판매자, 대여자로 참가한 채팅방을 생성
                chatroom = Chatroom.objects.create(
                    product=product, lender=user1, borrower=user2, lender_status=True, borrower_status=True
                )
                self.stdout.write(self.style.SUCCESS(f'Successfully created chatroom: {chatroom.id}'))

            self.stdout.write(self.style.SUCCESS(f'Successfully created {chatroom_number} chatrooms with product, 2 users'))
        except CommandError as e:
            self.stdout.write(self.style.ERROR(str(e)))
        except Exception as e:
            self.stdout.write(self.style.MIGRATE_LABEL(str(e)))