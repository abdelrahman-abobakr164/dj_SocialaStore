from django.urls import path
from . import views


urlpatterns = [
    path("settings/", views.settings, name="settings"),
    path("my-account/", views.my_account, name="my-account"),
    path("my-address/", views.my_address, name="my-address"),
    path("contact-us/", views.contact_us, name="contact-us"),

]
