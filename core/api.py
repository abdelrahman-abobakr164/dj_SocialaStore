from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.core.paginator import Paginator
from rest_framework.pagination import PageNumberPagination
from .serializers import *
from .models import *


@api_view(["GET"])
def product_api(request):
    products = Product.objects.all()
    
    paginator = PageNumberPagination()
    paginator.page_size = 1
    
    result_page = paginator.paginate_queryset(products, request)
    
    serializer = ProductsSerializers(result_page, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def productdetail_api(request, id):
    queryset = Product.objects.get(id=id)
    serializer = ProductsSerializers(queryset, many=False)
    return Response(serializer.data)
