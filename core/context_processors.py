from core.models import *


def navbar(request):
    categories = Category.objects.all()[:2]
    brands = Brand.objects.all()
    color_variations = (
        Variation.objects.filter(key="color", active=True)
        .values_list("value", flat=True)
        .distinct()
    )

    size_variations = (
        Variation.objects.filter(key="size", active=True)
        .values_list("value", flat=True)
        .distinct()
    )

    context = {
        "categories": categories,
        "brands": brands,
        "variations": color_variations,
        "size_variations": size_variations,
    }
    return context
