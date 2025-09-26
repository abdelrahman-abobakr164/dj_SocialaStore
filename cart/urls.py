from django.urls import path
from .views import *


urlpatterns = [
    path("", cart_summary, name="cart-summary"),
    path("apply-coupon/", apply_coupon, name="apply-coupon"),
    path(
        "c-b/cat/<category_slug>/<product_slug>/<str:pk>/",
        add_and_buy,
        name="c-b",
    ),
    path("remove-from-cart/<cartitem_pk>/", remove_from_cart, name="remove-from-cart"),
    path("minus-from-cart/<cartitem_pk>/", minus_from_cart, name="minus-from-cart"),
]
