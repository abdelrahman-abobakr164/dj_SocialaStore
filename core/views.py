from django.shortcuts import render, get_object_or_404
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

    paginator = Paginator(
        products,
        1,
        error_messages={
            "no_results": "No products found on this page",
            "invalid_page": "Invalid page number",
            "page_not_an_integer": "Page number must be an integer",
            "empty_page": "This page is empty",
        },
    )

    page = request.GET.get("p", 1)
    try:
        page_obj = paginator.get_page(page)
    except (ValueError, TypeError):
        page_obj = paginator.get_page(1)

    if "recently_products" in request.session:
        recently_products_cat = products.filter(
            category__name__in=request.session["recently_products"]
        )

    else:
        recently_products_cat = []

    context = {
        "products": page_obj,
        "recently_viewed": recently_products_cat,
    }
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
        if product.category.name in request.session["recently_products"]:
            request.session["recently_products"].remove(product.category.name)

        recent_view = Product.objects.filter(
            category__name__in=request.session["recently_products"]
        )

        request.session["recently_products"].append(product.category.name)

        if len(request.session["recently_products"]) > 4:
            request.session["recently_products"].pop(0)

    else:
        request.session["recently_products"] = [product.category.name]
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


def shop(request, category=None, brand=None, color=None, size=None, page=0):
    products = Product.objects.all()

    if color:
        color_variations = Variation.objects.filter(
            key="color", value=color, active=True
        )
        products = (
            Product.objects.prefetch_related(
                Prefetch(
                    "variations", queryset=color_variations, to_attr="color_variations"
                )
            )
            .filter(
                variations__key="color",
                variations__value=color,
                variations__active=True,
            )
            .distinct()
        )

    if size:
        size_variations = Variation.objects.filter(key="size", value=size, active=True)
        products = (
            Product.objects.prefetch_related(
                Prefetch(
                    "variations", queryset=size_variations, to_attr="size_variations"
                )
            )
            .filter(
                variations__key="size",
                variations__value=size,
                variations__active=True,
            )
            .distinct()
        )

    if category:
        products = products.filter(category__slug=category)

    if brand:
        products = products.filter(brand__slug=brand)

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
            (Q(name__icontains=search) | Q(category__name__icontains=search))
        )

    paginator = Paginator(
        products,
        1,
        error_messages={
            "no_results": "No products found on this page",
            "invalid_page": "Invalid page number",
            "page_not_an_integer": "Page number must be an integer",
            "empty_page": "This page is empty",
        },
    )

    page_number = request.GET.get("p", 1)
    try:
        page_obj = paginator.get_page(page_number)
    except (ValueError, TypeError):
        page_obj = paginator.get_page(1)

    return render(
        request,
        "core/shop.html",
        {
            "products": page_obj,
            "current_filters": {
                "category": category,
                "brand": brand,
                "color": color,
                "size": size,
                "search": search,
                "price_from": Pfrom,
                "price_to": Pto,
            },
        },
    )


def handler_404(request, exception):
    return render(request, "404.html", status=404)


def handler_500(request):
    return render(request, "500.html", status=500)
