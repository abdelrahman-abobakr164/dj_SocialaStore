from django.contrib import admin
from .models import *


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "order_number",
        "total",
        "is_ordered",
        "shipping_address",
        "billing_address",
        "status",
        "updated_at",
    ]
    list_filter = ["user", "created_at", "updated_at"]
    search_fields = ["order_number"]
    list_editable = ["status", "is_ordered"]
    list_per_page = 20
    inlines = [OrderItemInline]


class OrderItemAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "order",
        "product",
        "quantity",
        "color",
        "size",
        "product_price",
        "created_at",
        "updated_at",
    ]
    list_filter = ["user", "product", "created_at", "updated_at"]
    list_display_links = ["user"]
    list_per_page = 20


class AddressAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "first_name",
        "phone",
        "address1",
        "address2",
        "city",
        "address_type",
        "default",
    ]
    list_filter = ["user", "email"]
    search_fields = ["user", "email"]
    list_display_links = ["user"]
    list_editable = ["default", "address_type"]
    list_per_page = 20


class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "order",
        "user",
        "method",
        "amount",
        "payment_id",
        "status",
    ]
    list_filter = ["order"]
    search_fields = ["user", "order_order_number"]
    list_display_links = ["order"]
    list_per_page = 20


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "order", "amount", "status", "created_at")
    list_display_links = ["id", "order"]
    list_per_page = 20
    actions = ["approve_refund", "decline_refund"]

    def approve_refund(self, request, queryset):
        for refund in queryset.filter(status="PENDING"):
            if refund.payment.method == "Stripe":
                try:
                    refund.process_refund(refund.payment.payment_id)
                    self.message_user(request, f"Refund APPROVED.")

                except Exception as e:
                    self.message_user(request, f"Error processing {e}")
            else:
                self.message_user(request, "The Payment Method Should be Stripe")

    def decline_refund(self, request, queryset):
        for refund in queryset.filter(status="PENDING"):
            try:
                refund.status = "DECLINED"
                refund.save()
                self.message_user(request, f"Refund DECLINED.")
            except Exception as e:
                self.message_user(request, f"Error processing {e}")


admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(Payment, PaymentAdmin)
