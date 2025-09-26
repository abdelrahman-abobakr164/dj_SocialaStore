from django.urls import path
from .views import *
from core.api import *

urlpatterns = [
    path("api-list/", product_api, name="api"),
    path("api-detail/<str:id>/", productdetail_api, name="api-detail"),
    path("store/", index, name="store"),
    path("shop/", shop, name="shop"),
    path("shop/color/<str:color>/", shop, name="color_slug"),
    path(
        "cat/<category_slug>/<str:slug>/<str:pk>/",
        product_detail,
        name="product-detail",
    ),
    path(
        "review/cat/<category_slug>/<str:slug>/<str:pk>/",
        product_review,
        name="product-review",
    ),
]
