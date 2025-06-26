from django.urls import path
from .views import *


urlpatterns = [
    path("", index, name="index"),
    path("shop/", shop, name="shop"),
    path("shop/category/<cat_slug>/", shop, name="cat_slug"),
    path("shop/brand/<brand_slug>/", shop, name="brand_slug"),
    path("shop/color/<color_slug>/", shop, name="color_slug"),
    path("shop/size/<size_slug>/", shop, name="size_slug"),
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
