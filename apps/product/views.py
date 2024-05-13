from rest_framework import viewsets
from rest_framework.permissions import AllowAny#IsAuthenticated
from apps.product.models import Product
from apps.product.serializers import ProductSerializer
from rest_framework.decorators import action
from rest_framework.response import Response


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        product = serializer.save(user=self.request.user)

    # @action(detail=False, methods=['GET'])
    # def product_list(self, request):
    #     queryset = self.filter_queryset(self.get_queryset())
    #     serializer = self.get_serializer(queryset, many=True)
    #     return Response(serializer.data)
    #
    # @action(detail=True, methods=['GET'])
    # def product_detail(self, request):
    #     instance = self.get_object()
    #     serializer = self.get_serializer(instance)
    #     return Response(serializer.data)
    #
    # @action(detail=False, methods=['POST'])
    # def product_create(self, request):
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save()
    #     return Response(serializer.data, status=201)
    #
    # @action(detail=True, methods=['PUT', 'PATCH'])
    # def product_update(self, request):
    #     instance = self.get_object()
    #     serializer = self.get_serializer(instance, data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save()
    #     return Response(serializer.data)
    #
    # @action(detail=True, methods=['DELETE'])
    # def product_delete(self, request):
    #     instance = self.get_object()
    #     instance.delete()
    #     return Response(status=204)

# from rest_framework import viewsets
# from rest_framework import status
# from rest_framework.response import Response
# from apps.product.models import Product
# from apps.product.serializers import ProductSerializer
#
#
# class ProductViewSet(viewsets.ModelViewSet):
#     queryset = Product.objects.all()
#     serializer_class = ProductSerializer
#
#     def _perform_update(self, request, partial=False, *args, **kwargs):
#         kwargs['partial'] = partial
#         return super().update(request, *args, **kwargs)
#
#     update = partial_update = _perform_update

# class ProductViewSet(viewsets.ModelViewSet):
#     queryset = Product.objects.all()
#     serializer_class = ProductSerializer

    # def get_queryset(self):
    #     queryset = super().get_queryset()
    #
    #     # 검색 파라미터가 있는 경우에만 필터링
    #     name = self.request.query_params.get('name')
    #     style = self.request.query_params.get('style')
    #     category = self.request.query_params.get('category')
    #     size = self.request.query_params.get('size')
    #     status = self.request.query_params.get('status')
    #
    #     if name:
    #         queryset = queryset.filter(name__icontains=name)
    #     if style:
    #         queryset = queryset.filter(style__icontains=style)
    #     if category:
    #         queryset = queryset.filter(category__icontains=category)
    #     if size:
    #         queryset = queryset.filter(size__icontains=size)
    #     if status:
    #         status = True if status.lower() == 'true' else False
    #         queryset = queryset.filter(status=status)
    #
    #     return queryset

    # def partial_update(self, request, *args, **kwargs):
    #     kwargs['partial'] = True
    #     return super().partial_update(request, *args, **kwargs)
    #
    # def update(self, request, *args, **kwargs):
    #     kwargs['partial'] = False
    #     return super().update(request, *args, **kwargs)
    #
    # def delete(self, request, *args, **kwargs):
    #     instance = self.get_object()
    #     self.perform_delete(instance)
    #     return Response(status=status.HTTP_204_NO_CONTENT)

# from django.shortcuts import get_object_or_404
# from rest_framework import status
# from rest_framework.response import Response
# from rest_framework.views import APIView
#
# from apps.product.models import Product
# from apps.product.serializers import ProductSerializer
#
#
# class ProductListAPIView(APIView):
#     def get(self, request):
#         products = Product.objects.all()
#         serializer = ProductSerializer(products, many=True)
#         return Response(serializer.data)
#
#
# class ProductCreateAPIView(APIView):
#     def post(self, request):
#         serializer = ProductSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response({"message": "상품이 등록 되었습니다."}, status=status.HTTP_201_CREATED)
#         return Response({"message": "상품 등록에 실패 했습니다."}, status=status.HTTP_400_BAD_REQUEST)
#
#
# class ProductDetailAPIView(APIView):
#     def get(self, request, product_id):
#         product = get_object_or_404(Product, product_id)
#         serializer = ProductSerializer(product)
#         return Response(serializer.data)
#
#
# class ProductUpdateAPIView(APIView):
#     def put(self, request, product_id):
#         product = get_object_or_404(Product, product_id)
#         serializer = ProductSerializer(product, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response({"message": "상품을 수정했습니다."})
#         return Response({"message": "상품 수정에 실패했습니다."}, status=status.HTTP_400_BAD_REQUEST)
#
#
# class ProductPartialUpdateAPIView(APIView):
#     def patch(self, request, product_id):
#         product = get_object_or_404(Product, product_id)
#         serializer = ProductSerializer(product, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response({"message": "상품을 일부 수정 했습니다."})
#         return Response({"message": "상품의 일부 수정에 실패했습니다."}, status=status.HTTP_400_BAD_REQUEST)
#
#
# class ProductDeleteAPIView(APIView):
#     def delete(self, request, product_id):
#         try:
#             product = Product.objects.get(product_id)
#         except Product.DoesNotExist:
#             return Response({"message": "상품이 존재하지 않습니다."}, status=status.HTTP_404_NOT_FOUND)
#
#         product.delete()
#         return Response({"message": "상품이 삭제되었습니다."}, status=status.HTTP_204_NO_CONTENT)
#
#
# class ProductSearchAPIView(APIView):
#     def get(self, request):  # 쿼리 파라미터에서 검색어 받아오기
#         name = request.query_params.get("name")
#         style = request.query_params.get("style")
#         category = request.query_params.get("category")
#         size = request.query_params.get("size")
#         status = request.query_params.get("status")
#
#         # 모든 상품 가져오기
#         products = Product.objects.all()
#
#         # 검색 조건이 있을 경우 필터링
#         if name:
#             products = products.filter(name__icontains=name)
#         if style:
#             products = products.filter(style__icontains=style)
#         if category:
#             products = products.filter(category__icontains=category)
#         if size:
#             products = products.filter(size__icontains=size)
#         if status:
#             status = True if status.lower() == "true" else False
#             products = products.filter(status=status)
#
#         # 검색 결과 직렬화하여 반환
#         serializer = ProductSerializer(products, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)
#
#
# class ProductStatusUpdateAPIView(APIView):
#     def patch(self, request):
#         product_id = request.data.get('product_id')
#         if product_id is None:
#             return Response({"message": "상품_id가 제공되지 않았습니다."}, status=status.HTTP_400_BAD_REQUEST)
#
#         product = get_object_or_404(Product, product_id)
#         product.status = True  # 또는 원하는 상태값으로 변경
#         product.save()
#         return Response({"message": "상품 상태가 변경되었습니다."}, status=status.HTTP_200_OK)
