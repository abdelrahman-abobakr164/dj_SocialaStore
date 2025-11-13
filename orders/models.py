from phonenumber_field.modelfields import PhoneNumberField
from django.utils.translation import gettext_lazy as _
from core.models import Product, Variation
from stripe import StripeError
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
    ("PayPal", "PayPal"),
    ("Stripe", "Stripe"),
    ("CashOnDelivery", "CashOnDelivery"),
)


ORDER_STATUS = (
    ("Uncomplete", "Uncomplete"),
    ("Pending", "Pending"),
    ("Paid", "Paid"),
    ("Delivered", "Delivered"),
    ("Canceled", "Canceled"),
    ("Refund Requested", "Refund Requested"),
    ("Refunded", "Refunded"),
)


REFUND_REASON_CHOICES = [
    ("Damaged Item", "Damaged Item"),
    ("Wrong Item Delivered", "Wrong Item Delivered"),
    ("other", "Other"),
]


REFUND_CHOICES = [
    ("PENDING", "PENDING"),
    ("APPROVED", "APPROVED"),
    ("DECLINED", "DECLINED"),
]


class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_index=True
    )
    shipping_address = models.ForeignKey(
        "Address",
        related_name="shipping_address",
        on_delete=models.CASCADE,
        null=True,
    )
    billing_address = models.ForeignKey(
        "Address",
        related_name="billing_address",
        on_delete=models.CASCADE,
        null=True,
    )
    total = models.DecimalField(
        _("Total"), max_digits=10, decimal_places=2, null=True, blank=True
    )
    status = models.CharField(
        _("Status"), max_length=150, default="Uncomplete", choices=ORDER_STATUS
    )
    order_number = models.UUIDField(
        _("Order Number"), default=uuid.uuid4, unique=True, editable=False
    )
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email


class OrderItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, db_index=True
    )
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items", null=True
    )
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
    quantity = models.IntegerField(_("Quantity"))
    product_price = models.DecimalField(
        _("Product Price"), max_digits=10, decimal_places=2
    )
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
        Order, on_delete=models.CASCADE, related_name="payment", db_index=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True
    )
    payment_id = models.CharField(max_length=255)
    status = models.BooleanField(_("Status"), default=False)
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
        db_index=True,
    )
    first_name = models.CharField(_("First Name"), max_length=50)
    last_name = models.CharField(_("Last Name"), max_length=50)
    phone = PhoneNumberField(
        _("Phone Number"),
    )
    email = models.EmailField(_("Email Address"), max_length=254)
    address1 = models.CharField(_("Address1"), max_length=200)
    address2 = models.CharField(_("Address2"), max_length=200, blank=True, null=True)
    city = models.CharField(_("City"), max_length=100)
    zipcode = models.CharField(_("Zip Code"), max_length=9, blank=True, null=True)
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
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="refunds",
        db_index=True,
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="refunds")
    payment = models.ForeignKey(
        Payment, on_delete=models.CASCADE, related_name="refunds", null=True
    )
    refund_id = models.CharField(_("Refund Id"), max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(
        _("Reason"), max_length=100, choices=REFUND_REASON_CHOICES
    )
    email = models.EmailField(_("Email Address"), max_length=250)
    image = models.ImageField(upload_to="RefundImage")
    status = models.CharField(
        _("Status"), max_length=20, choices=REFUND_CHOICES, default="PENDING"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Refund for Order {self.user} {self.order.order_number} - {self.amount} ({self.status})"

    def process_refund(self, payment_intent_id):
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            charge_id = payment_intent.latest_charge

            refund = stripe.Refund.create(
                charge=charge_id,
                amount=int(self.amount * 100),
            )
            self.status = "APPROVED"
            self.order.status = "Refunded"
            self.save()
            return refund
        except StripeError as e:
            self.status = "DECLINED"
            self.save()
            raise e
