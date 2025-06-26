from django import forms
from core.models import Variation


class VariationForm(forms.Form):

    def __init__(self, *args, **kwargs):
        product = kwargs.pop("product")
        super().__init__(*args, **kwargs)

        color = Variation.objects.filter(product=product, key="color")
        if color.exists():
            self.fields["color"] = forms.ChoiceField(
                choices=[(v.id, v.value) for v in color],
                widget=forms.RadioSelect(attrs={"class": "variation-radio"}),
                required=True,
            )
            self.color_prices = {
                str(v.id): float(v.price) if v.price else None for v in color
            }

        size = Variation.objects.filter(product=product, key="size")
        if size.exists():
            self.fields["size"] = forms.ChoiceField(
                choices=[(v.id, v.value) for v in size],
                widget=forms.RadioSelect(attrs={"class": "variation-radio"}),
                required=True,
            )
            self.size_prices = {
                str(v.id): float(v.price) if v.price else None for v in size
            }


class CouponForm(forms.Form):
    code = forms.CharField(
        max_length=10,
        required=True,
        widget=forms.TextInput(
            attrs={"placeholder": "Coupon Code..", "class": "input-code form-control h60 p-3"}
        ),
    )

