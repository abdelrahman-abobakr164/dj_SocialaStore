from django.conf import settings
from django.contrib import admin
from django.conf.urls.static import static
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from orders.views import stripe_webhook

urlpatterns = [
    path("superuser/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("webhook/", stripe_webhook, name="stripe_webhook"),
    path("accounts/", include("allauth.urls")),
    path("accounts/", include("accounts.urls")),
]

urlpatterns += i18n_patterns(
    path("cart/", include("cart.urls")),
    path("wishlist/", include("wishlist.urls")),
    path("orders/", include("orders.urls")),
    path("", include("core.urls")),
    prefix_default_language=True,
)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


handler404 = "core.views.handler_404"
handler500 = "core.views.handler_500"
