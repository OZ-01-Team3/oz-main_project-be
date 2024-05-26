# from django.test import TestCase
# from django.urls import reverse
# from mypyc.irbuild.builder import IRBuilder
# from mypyc.irbuild.builder.IRBuilder import self
# from rest_framework import status
# from rest_framework.test import APIClient
#
# from apps.product.models import Product
#
#
# class ProductListAPITest(TestCase):
#     def setUp(self):
#         self.client = APIClient()
#         self.product1 = Product.objects.create(
#             name='Product 1',
#             user_id=1,
#             brand='Brand 1',
#             condition='Good',
#             purchasing_price=100000,
#             rental_fee=5000,
#             size='L',
#             views=100,
#             product_category_id=1,
#             style_category_id=1,
#             status=True
#         )
#         self.product2 = Product.objects.create(
#             name='Product 2',
#             user_id=2,
#             brand='Brand 2',
#             condition='Bad',
#             purchasing_price=80000,
#             rental_fee=4000,
#             size='S',
#             views=0,
#             product_category_id=2,
#             style_category_id=2,
#             status=False
#         )
#
#         # API 호출
#
#     response = self.client.get('/api/products/')
#
#     # 응답 확인
#     self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#     # 응답 데이터의 길이가 2인지 확인 (2개의 상품이 반환되어야 함)
#     self.assertEqual(len(response.data), 2)
#
#     # 상품의 모든 필드들을 확인
#     self.assertEqual(response.data[0]['name'], 'Product 1')
#     self.assertEqual(response.data[0]['user'], 1)
#     self.assertEqual(response.data[0]['brand'], 'Brand 1')
#     self.assertEqual(response.data[0]['condition'], 'New')
#     self.assertEqual(response.data[0]['purchasing_price'], 10000)
#     self.assertEqual(response.data[0]['rental_fee'], 5000)
#     self.assertEqual(response.data[0]['size'], 'M')
#     self.assertEqual(response.data[0]['views'], 0)
#     self.assertEqual(response.data[0]['product_category_id'], 1)
#     self.assertEqual(response.data[0]['style_category_id'], 1)
#     self.assertEqual(response.data[0]['status'], True)
#
#     self.assertEqual(response.data[1]['name'], 'Product 2')
#     self.assertEqual(response.data[1]['user'], 2)
#     self.assertEqual(response.data[1]['brand'], 'Brand 2')
#     self.assertEqual(response.data[1]['condition'], 'Used')
#     self.assertEqual(response.data[1]['purchasing_price'], 8000)
#     self.assertEqual(response.data[1]['rental_fee'], 4000)
#     self.assertEqual(response.data[1]['size'], 'L')
#     self.assertEqual(response.data[1]['views'], 0)
#     self.assertEqual(response.data[1]['product_category_id'], 2)
#     self.assertEqual(response.data[1]['style_category_id'], 2)
#     self.assertEqual(response.data[1]['status'], True)
#
#     def test_product_list_api_view(self):
#         url = reverse("product_list")
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.data), Product.objects.count())
#
#     def test_product_create_api_view(self):
#         url = reverse("product_create")
#         response = self.client.post(url, self.product_data, format="json")
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#
#     def test_product_detail_api_view(self):
#         url = reverse("product_detail", args=[self.product.pk])
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         #내가 셋업에 만든 상품이랑 이 뷰에서 조회 하고자 하는 상품의 데이터가 일치 하는 지를 확인해야함
#
