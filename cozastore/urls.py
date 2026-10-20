from django.contrib import admin
from django.urls import path, include
from orders.views import stripe_webhook
from django.conf.urls.i18n import i18n_patterns
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path("superuser/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("webhook/", stripe_webhook, name="stripe_webhook"),
    path("accounts/", include("allauth.urls")),
    path("accounts/", include("accounts.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]

urlpatterns += i18n_patterns(
    path("cart/", include("cart.urls")),
    path("wishlist/", include("wishlist.urls")),
    path("orders/", include("orders.urls")),
    path("", include("core.urls")),
    prefix_default_language=True,
)


handler404 = "core.views.handler_404"
handler500 = "core.views.handler_500"
