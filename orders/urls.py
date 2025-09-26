from django.urls import path
from . import views


urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("order-list/", views.order_list, name="order-list"),
    path("uncomplete-orders/<uuid:order_number>", views.uncomplete_orders, name="uncomplete-orders"),
    # path("buy-now/<int:id>/<str:slug>/", views.buy_now, name="buy-now"),
    path("canceled/<uuid:order_number>/", views.order_canceled, name="order-canceled"),
    path("success/<uuid:order_number>/", views.success, name="success"),
    path("failed/<uuid:order_number>/", views.failed, name="failed"),
    path(
        "create_checkout_session/<uuid:order_number>/",
        views.create_checkout_session,
        name="create_checkout_session",
    ),
    path(
        "payment/<str:payment_option>/<uuid:order_number>/",
        views.payment,
        name="payment",
    ),
    path(
        "request-refund/<uuid:order_number>/",
        views.request_refund,
        name="request-refund",
    ),
    path(
        "refund/<uuid:refund_number>/<uuid:order_number>/",
        views.refund_payment,
        name="refund",
    ),
    path("<uuid:order_number>/", views.order_detail, name="order-detail"),
]
