from django.db import models
from django.conf import settings
from core.models import Product, Variation

# Create your models here.


class CartManager(models.Manager):
    def get_or_new(self, request):

        cart_id = request.session.get("cart_id")
        cart_obj = None
        created = False

        if request.user.is_authenticated:
            user_cart = (
                self.get_queryset().filter(user=request.user, active=True).first()
            )

            if cart_id:
                try:
                    session_cart = self.get_queryset().get(id=cart_id, active=True)

                    if user_cart and session_cart.id != user_cart.id:
                        session_items = session_cart.cartitem_set.all()
                        for item in session_items:

                            existing_item = user_cart.cartitem_set.filter(
                                product=item.product,
                                size=item.size,
                                color=item.color,
                            ).first()
                            if existing_item:
                                existing_item.quantity += item.quantity
                                existing_item.save()
                                item.delete()
                            else:
                                item.cart = user_cart
                                item.save()

                        if session_cart.user is None:
                            session_cart.delete()

                        cart_obj = user_cart

                    elif not user_cart:
                        session_cart.user = request.user
                        session_cart.save()
                        cart_obj = session_cart
                    else:
                        cart_obj = user_cart

                except self.model.DoesNotExist:

                    if user_cart:
                        cart_obj = user_cart
                    else:
                        cart_obj = self.model.objects.create(
                            user=request.user, active=True
                        )
                        created = True

            else:
                if user_cart:
                    cart_obj = user_cart
                else:
                    cart_obj = self.model.objects.create(user=request.user, active=True)
                    created = True

            request.session["cart_id"] = cart_obj.id

        else:
            if cart_id:
                try:
                    cart_obj = self.get_queryset().get(id=cart_id, active=True)
                except self.model.DoesNotExist:
                    cart_obj = self.model.objects.create(active=True)
                    created = True
                    request.session["cart_id"] = cart_obj.id
            else:
                cart_obj = self.model.objects.create(active=True)
                created = True
                request.session["cart_id"] = cart_obj.id

        return cart_obj, created


class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    active = models.BooleanField(default=True)

    objects = CartManager()

    def __str__(self):
        return str(self.id)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    size = models.ForeignKey(
        Variation,
        on_delete=models.CASCADE,
        related_name="size",
        null=True,
        blank=True,
    )
    color = models.ForeignKey(
        Variation,
        on_delete=models.CASCADE,
        related_name="color",
        null=True,
        blank=True,
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return str(self.id)

    def get_price(self):
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

        return (base_price + variation_price) * self.quantity


class Coupon(models.Model):
    code = models.CharField(max_length=10, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    max_uses = models.PositiveIntegerField(blank=True, null=True)
    used_count = models.PositiveIntegerField(default=0, editable=False)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - (${self.amount})"
