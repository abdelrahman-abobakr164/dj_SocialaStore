from django.shortcuts import render, redirect, get_object_or_404
from wishlist.models import Wishlist
from core.models import Product


def wish_summary(request):
    return render(request, "wishlist/wish.html")


def add(request, cat_slug, product_slug, pk):
    url = request.META.get("HTTP_REFERER")
    product = get_object_or_404(
        Product,
        category__slug=cat_slug,
        slug=product_slug,
        pk=pk,
    )
    list_obj, created = Wishlist.objects.get_or_new(request, product)
    return redirect(url)


def remove(request, cat_slug, product_slug, pk):
    product = get_object_or_404(
        Product,
        category__slug=cat_slug,
        slug=product_slug,
        pk=pk,
    )

    if request.user.is_authenticated:
        wish = Wishlist.objects.filter(user=request.user, product=product).first()
    else:
        wish = Wishlist.objects.filter(
            id=request.session.get("list_id"),
            product=product,
        ).first()

    if wish:
        wish.product.remove(product)
        wish.save()
        return redirect("wish-summary")
