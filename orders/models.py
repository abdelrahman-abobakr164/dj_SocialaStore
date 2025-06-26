from phonenumber_field.modelfields import PhoneNumberField
from core.models import Product, Variation
from stripe.error import StripeError
from django.conf import settings
from django.db import models
import stripe
import uuid

stripe.api_key = settings.STRIPE_SECRET_KEY


ADDRESS_CHOICES = (
    ("Billing", "Billing"),
    ("Shipping", "Shipping"),
)


PAYMENT_METHODS = (
    ("Stripe", "Stripe"),
    ("CashOnDelivery", "CashOnDelivery"),
)


ORDER_STATUS = (
    ("Pending", "Pending"),
    ("Paid", "Paid"),
    ("Delivered", "Delivered"),
    ("Canceled", "Canceled"),
    ("Refunded", "Refunded"),
)


REFUND_CHOICES = [
    ("PENDING", "PENDING"),
    ("APPROVED", "APPROVED"),
    ("DECLINED", "DECLINED"),
]


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    shipping_address = models.ForeignKey(
        "Address", related_name="shipping_address", on_delete=models.CASCADE, null=True
    )
    billing_address = models.ForeignKey(
        "Address", related_name="billing_address", on_delete=models.CASCADE, null=True
    )
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=150, default="Pending", choices=ORDER_STATUS)
    order_number = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email


class OrderItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.ForeignKey(
        Variation,
        on_delete=models.CASCADE,
        related_name="ordersize",
        null=True,
        blank=True,
    )
    color = models.ForeignKey(
        Variation,
        on_delete=models.CASCADE,
        related_name="ordercolor",
        null=True,
        blank=True,
    )
    quantity = models.IntegerField()
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_product_price(self):
        base_price = (
            self.product.discount_price
            if self.product.discount_price
            else self.product.price
        )

        variation_price = 0
        if self.color:
            if self.color.price:
                variation_price += self.color.price

        if self.size:
            if self.size.price:
                variation_price += self.size.price

        return base_price + variation_price


class Payment(models.Model):
    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="payment"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True
    )
    payment_id = models.CharField(max_length=255)
    status = models.BooleanField(default=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=50, choices=PAYMENT_METHODS)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order} - {self.method}"


class Address(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = PhoneNumberField()
    email = models.EmailField(max_length=254)
    address1 = models.CharField(max_length=200)
    address2 = models.CharField(max_length=200, blank=True, null=True)
    city = models.CharField(max_length=100)
    zipcode = models.CharField(max_length=9, blank=True, null=True)
    address_type = models.CharField(max_length=10, choices=ADDRESS_CHOICES)
    default = models.BooleanField(default=False)

    def __str__(self):
        return str(self.user)

    def full_address(self):
        if self.address2:
            return f"({self.address1}), ({self.address2}), ({self.city})"
        return f"({self.address1}), ({self.city})"


class Refund(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="refunds"
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="refunds")
    payment = models.ForeignKey(
        Payment, on_delete=models.CASCADE, related_name="refunds", null=True
    )
    refund_id = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    email = models.EmailField(max_length=250)
    image = models.ImageField(upload_to="RefundImage")
    status = models.CharField(max_length=20, choices=REFUND_CHOICES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Refund for Order {self.user} {self.order.order_number} - {self.amount} ({self.status})"

    def process_refund(self, stripe_payment_id):

        try:
            refund = stripe.Refund.create(
                payment_intent=stripe_payment_id,
                amount=int(self.amount * 100),
            )
            self.stripe_refund_id = refund.id
            self.status = "COMPLETED"
            self.order.status = "Refunded"
            self.save()
            return refund
        except StripeError as e:
            self.status = "DECLINED"
            self.save()
            raise e
