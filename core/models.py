from django.db import models
from django.urls import reverse
from accounts.models import User
from django.db.models import Avg
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Product(models.Model):
    name = models.CharField(max_length=150, verbose_name=_("Name"))
    img = models.ImageField(upload_to="Product_img")
    price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Price")
    )
    discount_price = models.DecimalField(
        _("Discount Price"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="This Is A New price",
    )
    description = models.TextField(_("Description"), null=True, blank=True)
    stock = models.IntegerField()
    category = models.ForeignKey(
        "Category", on_delete=models.SET_NULL, null=True, related_name="categories"
    )
    brand = models.ForeignKey(
        "Brand", on_delete=models.SET_NULL, null=True, related_name="brands"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.CharField(_("Slug"), max_length=150, null=True, blank=True)

    def discount_percentage(self):
        if self.discount_price and self.price:
            discount = ((self.price - self.discount_price) / self.price) * 100
            return f" %{round(discount, 1 )}"
        return 0

    def get_absolute_url(self):

        return reverse(
            "product-detail",
            kwargs={
                "category_slug": self.category.slug,
                "slug": self.slug,
                "pk": self.pk,
            },
        )

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name_ar, allow_unicode=True)
        super().save(*args, **kwargs)

    def review_url(self):
        return reverse(
            "product-review",
            kwargs={
                "category_slug": self.category.slug,
                "slug": self.slug,
                "pk": self.pk,
            },
        )

    def add_to_cart_url(self):
        return reverse(
            "add-to-cart",
            kwargs={
                "category_slug": self.category.slug,
                "product_slug": self.slug,
                "pk": self.pk,
            },
        )

    def __str__(self):
        return self.name

    def calc_rating(self):
        reviews = Review.objects.filter(product=self, status=True).aggregate(
            average=Avg("rating")
        )
        avg = 0
        if reviews["average"] is not None:
            avg = sum(reviews["average"])
        return avg

    class Meta:
        ordering = ["-created_at"]


class Brand(models.Model):
    name = models.CharField(_("Brand Name"), max_length=150)
    slug = models.CharField(max_length=150, null=True, blank=True)

    def get_absolute_url(self):
        return reverse("brand_slug", kwargs={"brand": self.slug})

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name_ar, allow_unicode=True)

        super().save(*args, **kwargs)


class Category(models.Model):
    name = models.CharField(_("Category Name"), max_length=150)
    image = models.ImageField(upload_to="CategoryImage")
    slug = models.CharField(max_length=150, null=True, blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("cat_slug", kwargs={"category": self.slug})

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name_ar, allow_unicode=True)

        super().save(*args, **kwargs)


class VariationManager(models.Manager):
    def color(self):
        return super(VariationManager, self).filter(key="color", active=True)

    def size(self):
        return super(VariationManager, self).filter(key="size", active=True)


variation_choices = (("color", "color"), ("size", "size"))


class Variation(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="variations"
    )
    key = models.CharField(max_length=150, choices=variation_choices)
    value = models.CharField(_("Value"), max_length=150)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="The Color price Not The New Product Pice like (red = $5) ",
    )
    active = models.BooleanField(default=True)

    objects = VariationManager()

    def __str__(self):
        return f"{self.product.name} - {self.value}"

    def save(self, *args, **kwargs):
        self.value = self.value.capitalize()
        return super(Variation, self).save(*args, **kwargs)


class Gallary(models.Model):
    img = models.ImageField(upload_to="Product_Gallary")
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="gallary"
    )

    def __str__(self):
        return self.product.name


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="products"
    )
    subject = models.CharField(max_length=50, blank=True)
    review = models.TextField(max_length=300, blank=True)
    rating = models.FloatField()
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.subject

    class Meta:
        ordering = ("-updated_at",)
