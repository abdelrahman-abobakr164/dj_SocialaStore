from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from .models import *


class ProductImageInline(admin.TabularInline):
    model = Gallary
    extra = 1


class VariationInline(admin.TabularInline):
    model = Variation
    extra = 1


class VariationAdmin(admin.ModelAdmin):
    list_display = ["product", "key", "value", "price","active"]
    list_editable = ["active"]
    list_filter = ["key"]
    search_fields = ("product__name", "key", "value")
    list_per_page = 20


class ReviewAdmin(admin.ModelAdmin):
    list_display = ["product", "subject", "rating", "status", "user"]
    list_editable = ["status"]
    list_filter = ["product", "user", "rating"]
    search_fields = ["product"]
    list_per_page = 20


class ProductAdmin(TranslationAdmin):
    list_display = ["name", "price", "discount_price", "stock", "category"]
    list_editable = ["stock", "discount_price"]
    list_filter = ["price"]
    list_per_page = 20
    inlines = [ProductImageInline, VariationInline]
    search_fields = ["name", "category__name"]


class CategoryAdmin(TranslationAdmin):
    list_display = ["name", "slug"]


class BrandAdmin(TranslationAdmin):
    list_display = ["name", "slug"]


admin.site.register(Product, ProductAdmin)
admin.site.register(Brand, BrandAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Variation, VariationAdmin)
admin.site.register(Gallary)
admin.site.register(Review, ReviewAdmin)
