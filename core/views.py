from django.shortcuts import redirect, render, get_object_or_404
from django.core.paginator import EmptyPage, PageNotAnInteger
from django.db.models import Prefetch, Q, Count
from django.core.paginator import Paginator
from django.core.cache import cache
from django.contrib import messages
from django.http import QueryDict
from decimal import Decimal

from cart.forms import VariationForm
from orders.models import OrderItem
from core.forms import ReviewForm
from core.models import *


def index(request):
    recently_products_cat = []
    if "recently_products" in request.session:
        recently_products_cat = Product.objects.select_related("category").filter(
            category__name__in=request.session["recently_products"]
        )
    trending_products = Product.objects.filter(bestseller__gte=10).order_by(
        "-bestseller"
    )[:9]

    if trending_products:
        categories = []
        seen_cat = set()
        for product in trending_products:
            cat = product.category
            if cat not in seen_cat:
                seen_cat.add(cat)
                cat.is_new_arrival = False
                categories.append(cat)

        max_length = 3 - len(categories)

        if max_length > 0:
            recent_categories = Category.objects.exclude(name__in=seen_cat)[:max_length]
            for cat in recent_categories:
                cat.is_new_arrival = True
                categories.append(cat)

    else:
        categories = list(Category.objects.all()[:3])

    context = {
        "trending_products": trending_products,
        "categories": categories,
        "recently_viewed": recently_products_cat,
    }
    return render(request, "core/index.html", context)


def shop(request, color=None):
    products = Product.objects.select_related("category", "brand").order_by(
        "-created_at"
    )
    categories = Category.objects.annotate(categories_count=Count("categories"))
    brands = Brand.objects.annotate(brands_count=Count("brands"))
    color_variations = list(
        set(
            Variation.objects.filter(key="color", active=True).values_list(
                "value", flat=True
            )
        )
    )
    size_variations = list(
        set(
            Variation.objects.filter(key="size", active=True).values_list(
                "value", flat=True
            )
        )
    )

    params = request.GET.copy()
    clean_params = QueryDict(mutable=True)
    for key, value in params.items():
        if value and value.strip():
            clean_params[key] = value

    if len(clean_params) != len(params):
        if clean_params:
            return redirect(f"{request.path}?{clean_params.urlencode()}")
        else:
            return redirect(request.path)

    selected_categories = clean_params.getlist(key="category_")
    selected_brands = clean_params.getlist("brand_")
    selected_size = clean_params.getlist("size_")
    sort_by = clean_params.get("sort_by")
    min_price = clean_params.get("min_price")
    max_price = clean_params.get("max_price")
    search = clean_params.get("query")
    page = request.GET.get("page")

    if color:
        products = (
            Product.objects.prefetch_related(
                Prefetch(
                    "variations",
                    queryset=Variation.objects.filter(
                        key="color", value=color, active=True
                    ),
                    to_attr="color_variations",
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
            products = (
                Product.objects.prefetch_related(
                    Prefetch(
                        "variations",
                        queryset=Variation.objects.filter(
                            key="size", value=i, active=True
                        ),
                        to_attr="sizies_query",
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
        products = (
            Product.objects.filter(Q(category__name__in=selected_categories))
            .select_related("category")
            .order_by("-created_at")
        )

    if selected_brands:
        products = (
            Product.objects.filter(Q(brand__name__in=selected_brands))
            .select_related("brand")
            .order_by("-created_at")
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
        "brands": brands,
        "categories": categories,
        "page_obj": page_obj,
        "color_variations": color_variations,
        "size_variations": size_variations,
        "custom_page_range": custom_page_range,
        "group_end": group_end,
        "total_pages": total_pages,
        "sort_by": sort_by,
        "selected_size": selected_size,
        "selected_categories": selected_categories,
        "selected_brands": selected_brands,
    }

    return render(request, "core/shop.html", context)


def product_detail(request, category_slug, slug, pk):
    try:
        cache_key = f"Product{pk}"
        product = cache.get(cache_key)
        if not product:
            product = get_object_or_404(
                Product.objects.select_related("category")
                .prefetch_related("gallary", "products")
                .annotate(reviews_count=Count("products")),
                category__slug=category_slug,
                slug=slug,
                pk=pk,
            )
            cache.set(cache_key, product, timeout=60 * 15)

        varform = VariationForm(product=product)

        if request.user.is_authenticated:
            orderitem = OrderItem.objects.filter(
                user=request.user, product=product
            ).exists()
        else:
            orderitem = None

        if "recently_products" in request.session:
            if product.category.name in request.session["recently_products"]:
                request.session["recently_products"].remove(product.category.name)

            request.session["recently_products"].append(product.category.name)

            if len(request.session["recently_products"]) > 4:
                request.session["recently_products"].pop(0)

        else:
            request.session["recently_products"] = [product.category.name]

        request.session.modified = True
        context = {
            "product": product,
            "form": ReviewForm(),
            "varform": varform,
            "orderitem": orderitem,
        }

        return render(request, "core/detail.html", context)
    except Product.DoesNotExist:
        return redirect("shop")


def product_review(request, category_slug, slug, pk):
    product = get_object_or_404(
        Product.objects.select_related("category", "category__slug"),
        category__slug=category_slug,
        slug=slug,
        pk=pk,
    )
    if request.method == "POST":
        try:
            form = ReviewForm(request.POST)
            if form.is_valid():
                Review.objects.update_or_create(
                    user=request.user,
                    product=product,
                    defaults={
                        "rating": form.cleaned_data["rating"],
                        "review": form.cleaned_data["review"],
                    },
                )
                messages.success(
                    request, "Your Review has been Submitted Successfully!"
                )
                return redirect(
                    "product-detail", product.category.slug, product.slug, product.pk
                )
            else:
                messages.error(request, f"Please Fill in The Required Fields")
                return redirect(
                    "product-detail", product.category.slug, product.slug, product.pk
                )
        except Exception as e:
            messages.error(request, f"{e}")
            return redirect(
                "product-detail", product.category.slug, product.slug, product.pk
            )
    return redirect("product-detail", product.category.slug, product.slug, product.pk)


def handler_404(request, exception):
    return render(request, "404.html", status=404)


def handler_500(request):
    return render(request, "500.html", status=500)
