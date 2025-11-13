from core.models import *


def navbar(request):
    if "superuser" in request.path:
        return {}
    else:
        trending_products = Product.objects.filter(bestseller__gt=0).order_by(
            "-bestseller"
        )[:9]

        if trending_products:
            trending = True
            for trending_category in trending_products:
                SliderCategories = Category.objects.filter(
                    name=(trending_category.category.name)
                )[:3]
        else:
            trending = False
            SliderCategories = Category.objects.all()[:3]

        categories = Category.objects.all()

        brands = Brand.objects.all()
        color_variations = list(
            set(
                Variation.objects.filter(key="color", active=True)
                .select_related("product")
                .values_list("value", flat=True)
            )
        )

        size_variations = list(
            set(
                Variation.objects.filter(key="size", active=True)
                .select_related("product")
                .values_list("value", flat=True)
            )
        )

        context = {
            "trending_products": trending_products,
            "trending": trending,
            "SliderCategories": SliderCategories,
            "categories": categories,
            "brands": brands,
            "color_variations": color_variations,
            "size_variations": size_variations,
        }
        return context
