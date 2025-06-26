from django.shortcuts import render, redirect, get_object_or_404
from wishlist.models import Wishlist
from django.contrib.auth.decorators import login_required
from core.models import Product

# Create your views here.


@login_required(login_url="account_login")
def wish_summary(request):
    wishies = Wishlist.objects.filter(user=request.user)
    return render(request, "wishlist/wish.html", {"wishies": wishies})


@login_required(login_url="account_login")
def add(request, cat_slug, product_slug, pk):
    url = request.META.get("HTTP_REFERER")

    product = get_object_or_404(
        Product,
        category__slug=cat_slug,
        slug=product_slug,
        pk=pk,
    )

    wish = Wishlist.objects.filter(user=request.user, product_id=product.id)
    if wish.exists():
        return redirect(url)
    else:
        Wishlist.objects.create(user=request.user, product_id=product.id)
        return redirect(url)


@login_required(login_url="account_login")
def remove(request, cat_slug, product_slug, pk):
    product = get_object_or_404(
        Product,
        category__slug=cat_slug,
        slug=product_slug,
        pk=pk,
    )

    wish = Wishlist.objects.filter(user=request.user, product_id=product.id)

    if wish.exists():
        wish.delete()
        return redirect("wish-summary")
