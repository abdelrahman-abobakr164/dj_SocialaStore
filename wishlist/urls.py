from django.urls import path
from . import views


urlpatterns = [
    path("", views.wish_summary, name="wish-summary"),
    path("add/cat/<cat_slug>/<product_slug>/<str:pk>/", views.add, name="add"),
    path("remove/cat/<cat_slug>/<product_slug>/<str:pk>/", views.remove, name="remove"),
]
