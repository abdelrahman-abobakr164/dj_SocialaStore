from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.http import JsonResponse
from cart.forms import VariationForm
from orders.models import OrderItem
from core.forms import ReviewForm
from decimal import Decimal
from core.models import *


def index(request):
    products = Product.objects.order_by("-created_at")
    paginator = Paginator(products, 1)
    page = request.GET.get("p")
    page_obj = paginator.get_page(page)

    if "recently_products" in request.session:
        recently_products_cat = products.filter(
            category__slug__in=request.session["recently_products"]
        )

    else:
        recently_products_cat = []

    context = {"products": page_obj, "recently_viewed": recently_products_cat}
    return render(request, "core/index.html", context)


def product_detail(request, category_slug, slug, pk):
    product = get_object_or_404(Product, category__slug=category_slug, slug=slug, pk=pk)

    form = ReviewForm()
    varform = VariationForm(product=product)
    filter_products = Product.objects.filter(
        category__name=product.category.name
    ).exclude(pk=pk)

    if request.user.is_authenticated:
        orderitem = OrderItem.objects.filter(user=request.user, product=product)
    else:
        orderitem = None

    if "recently_products" in request.session:
        if product.category.slug in request.session["recently_products"]:
            request.session["recently_products"].remove(product.category.slug)

        recent_view = Product.objects.filter(
            category__slug__in=request.session["recently_products"]
        )

        request.session["recently_products"].append(product.category.slug)

        if len(request.session["recently_products"]) > 4:
            request.session["recently_products"].pop(0)

    else:
        request.session["recently_products"] = [product.category.slug]
        recent_view = []

    request.session.modified = True

    context = {
        "product": product,
        "products": filter_products,
        "form": form,
        "varform": varform,
        "orderitem": orderitem,
    }

    return render(request, "core/detail.html", context)


def product_review(request, category_slug, slug, pk):
    product = get_object_or_404(Product, category__slug=category_slug, slug=slug, pk=pk)

    if request.method == "POST":
        try:
            form = ReviewForm(request.POST)

            if form.is_valid():
                Review.objects.update_or_create(
                    user=request.user,
                    product=product,
                    defaults={
                        "rating": form.cleaned_data.get("rating"),
                        "subject": form.cleaned_data.get("subject"),
                        "review": form.cleaned_data.get("review"),
                    },
                )

                return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse(
        {"success": False, "error": "Please Fill in The Required Fields"}, status=400
    )


def shop(request, cat_slug=None, brand_slug=None, color_slug=None, size_slug=None):
    products = Product.objects.all()

    if color_slug:
        color_variations = Variation.objects.filter(
            key="color", value=color_slug, active=True
        )
        products = (
            Product.objects.prefetch_related(
                Prefetch(
                    "variations", queryset=color_variations, to_attr="color_variations"
                )
            )
            .filter(
                variations__key="color",
                variations__value=color_slug,
                variations__active=True,
            )
            .distinct()
        )

    if size_slug:
        size_variations = Variation.objects.filter(
            key="size", value=size_slug, active=True
        )
        products = (
            Product.objects.prefetch_related(
                Prefetch(
                    "variations", queryset=size_variations, to_attr="size_variations"
                )
            )
            .filter(
                variations__key="size",
                variations__value=size_slug,
                variations__active=True,
            )
            .distinct()
        )

    if cat_slug:
        products = products.filter(category__slug=cat_slug)

    if brand_slug:
        products = products.filter(brand__slug=brand_slug)

    search = request.GET.get("s")
    Pfrom = request.GET.get("from", 0.00)
    Pto = request.GET.get("to", 0.00)

    if Pfrom:
        Pfrom = Decimal(Pfrom)

    if Pto:
        Pto = Decimal(Pto)

    products = products.filter(
        Q(price__gte=Pfrom) | Q(discount_price__gte=Pfrom) if Pfrom else Q(),
        Q(price__lte=Pto) | Q(discount_price__lte=Pfrom) if Pto else Q(),
    )

    if search:
        products = products.filter(
            (Q(name__icontains=search) | Q(category__name__icontains=search)),
        )

    paginator = Paginator(
        products,
        4,
        error_messages={"no_results": "Page does not exist"},
    )
    page_number = request.GET.get("p")
    page_obj = paginator.get_page(page_number)

    return render(request, "core/shop.html", {"products": page_obj})


def handler_404(request, exception):
    return render(request, "404.html", status=404)


def handler_500(request):
    return render(request, "500.html", status=500)
