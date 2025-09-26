from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.core.paginator import Paginator
from .serializers import *
from .models import *


@api_view(["GET"])
def product_api(request):
    queryset = Product.objects.all()
    paginator = Paginator(queryset, 1)
    page = request.GET.get("page")
    page_obj = paginator.get_page(page)

    serializer = ProductsSerializers(page_obj, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def productdetail_api(request, id):
    queryset = Product.objects.get(id=id)
    serializer = ProductsSerializers(queryset, many=False)
    return Response(serializer.data)
