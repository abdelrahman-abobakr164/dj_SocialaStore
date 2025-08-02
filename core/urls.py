from django.urls import path
from .views import *


urlpatterns = [
    path("store/", index, name="store"),
    path("shop/", shop, name="shop"),
    path("shop/category/<category>/", shop, name="cat_slug"),
    path("page/<int:page>/", shop, name="product_list_paginated"),
    path("shop/brand/<brand>/", shop, name="brand_slug"),
    path("shop/color/<color>/", shop, name="color_slug"),
    path("shop/size/<size>/", shop, name="size_slug"),
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
