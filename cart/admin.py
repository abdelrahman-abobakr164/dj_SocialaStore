from django.contrib import admin
from .models import *

# Register your models here.


class CartAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "active"]
    list_filter = ["user"]
    list_per_page = 20


class CartItemAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "cart",
        "product",
        "price",
        "color",
        "size",
        "quantity",
    ]
    list_filter = ["product", "quantity"]
    list_editable = ["price"]
    list_per_page = 20


class CouponAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "amount",
        "max_uses",
        "used_count",
        "end_date",
    ]
    list_editable = ["amount", "max_uses"]
    list_per_page = 20


admin.site.register(Coupon, CouponAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)
