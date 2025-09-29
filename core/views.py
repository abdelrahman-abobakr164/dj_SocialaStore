from django.shortcuts import redirect, render, get_object_or_404
from django.core.paginator import EmptyPage, PageNotAnInteger
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.http import JsonResponse
from django.contrib import messages
from decimal import Decimal

from cart.forms import VariationForm
from orders.models import OrderItem
from core.forms import ReviewForm
from core.models import *


def index(request):
    if "recently_products" in request.session:
        recently_products_cat = Product.objects.filter(
            category__name__in=request.session["recently_products"]
        )
    else:
        recently_products_cat = []

    return render(
        request, "core/index.html", {"recently_viewed": recently_products_cat}
    )


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
                        "review": form.cleaned_data.get("review"),
                    },
                )

                return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse(
        {"success": False, "error": "Please Fill in The Required Fields"}, status=400
    )


def shop(request, color=None):
    products = Product.objects.all().order_by("-created_at")

    selected_categories = request.GET.getlist("category_")
    selected_brands = request.GET.getlist("brand_")
    selected_size = request.GET.getlist("size_")
    sort_by = request.GET.get("sort_by")
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    page = request.GET.get("page")
    search = request.GET.get("query")

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
        ).order_by("-created_at")

    if selected_size:
        for i in selected_size:
            sizies_query = Variation.objects.filter(key="size", value=i, active=True)
            if sizies_query.exists():
                products = (
                    Product.objects.prefetch_related(
                        Prefetch(
                            "variations", queryset=sizies_query, to_attr="sizies_query"
                        )
                    )
                    .filter(
                        variations__key="size",
                        variations__value=i,
                        variations__active=True,
                    )
                    .distinct()
                ).order_by("-created_at")

    if selected_categories:
        products = Product.objects.filter(
            Q(category__name__in=selected_categories)
        ).order_by("-created_at")

    if selected_brands:
        products = Product.objects.filter(Q(brand__name__in=selected_brands)).order_by(
            "-created_at"
        )

    if sort_by:
        if sort_by == "price-descending":
            products = Product.objects.order_by("-price")
        elif sort_by == "price-ascending":
            products = Product.objects.order_by("price")
        elif sort_by == "date-ascending":
            products = Product.objects.order_by("created_at")
        elif sort_by == "date-descending":
            products = Product.objects.order_by("-created_at")

    if min_price or max_price:
        price_query = Q()
        if min_price:
            price_query &= Q(price__gte=Decimal(min_price)) | Q(
                discount_price__gte=Decimal(min_price)
            )

        if max_price:
            price_query &= Q(price__lte=Decimal(max_price)) | Q(
                discount_price__lte=Decimal(max_price)
            )

        products = products.filter(price_query)

    if search:
        products = products.filter(
            (Q(name__icontains=search) | Q(category__name__icontains=search))
        ).order_by("-created_at")

    paginator = Paginator(products, 1)

    try:
        page_obj = paginator.get_page(page)
    except ZeroDivisionError:
        messages.warning(request, "Invalid Filter")
        return redirect("shop")
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)

    current_page = page_obj.number
    total_pages = paginator.num_pages
    group_size = 3
    group_start = ((current_page - 1) // group_size) * group_size + 1
    group_end = min(group_start + group_size - 1, total_pages)
    custom_page_range = range(group_start, group_end + 1)

    context = {
        "page_obj": page_obj,
        "custom_page_range": custom_page_range,
        "group_end": group_end,
        "total_pages": total_pages,
        "sort_by": sort_by,
        "selected_size": selected_size,
        "selected_categories": selected_categories,
        "selected_brands": selected_brands,
    }

    return render(request, "core/shop.html", context)


def handler_404(request, exception):
    return render(request, "404.html", status=404)


def handler_500(request):
    return render(request, "500.html", status=500)
