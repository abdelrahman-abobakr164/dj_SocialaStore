from django.contrib import admin
from .models import Wishlist

# Register your models here.


class WishlistAdmin(admin.ModelAdmin):
    list_display = ["id", "user"]
    list_filter = ["user"]
    list_per_page = 20


admin.site.register(Wishlist, WishlistAdmin)
