from django import forms
from phonenumber_field.formfields import PhoneNumberField

PAYMENT_CHOICES = (
    ("Stripe", "Stripe"),
    ("CashOnDelivery", "CashOnDelivery"),
)


class CheckoutForm(forms.Form):
    shipping_first_name = forms.CharField(required=False)
    shipping_last_name = forms.CharField(required=False)
    shipping_email = forms.EmailField(required=False)
    shipping_phone = PhoneNumberField(required=False)
    shipping_address1 = forms.CharField(required=False)
    shipping_address2 = forms.CharField(required=False)
    shipping_city = forms.CharField(required=False)
    shipping_zip = forms.CharField(required=False)

    billing_first_name = forms.CharField(required=False)
    billing_last_name = forms.CharField(required=False)
    billing_email = forms.EmailField(required=False)
    billing_phone = PhoneNumberField(required=False)
    billing_address1 = forms.CharField(required=False)
    billing_address2 = forms.CharField(required=False)
    billing_city = forms.CharField(required=False)
    billing_zip = forms.CharField(required=False)

    set_default_shipping = forms.BooleanField(required=False)
    use_default_shipping = forms.BooleanField(required=False)

    set_default_billing = forms.BooleanField(required=False)
    use_default_billing = forms.BooleanField(required=False)
    same_shipping_address = forms.BooleanField(required=False)

    payment_option = forms.ChoiceField(
        widget=forms.RadioSelect, choices=PAYMENT_CHOICES
    )


class RefundForm(forms.Form):
    order_number = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control mb-3",
                "autocomplete": "off",
                "id": "id_order_number",
                "placeholder": "Copy The Order Number Here",
            }
        ),
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "form-control mb-3", "placeholder": "Email Address"}
        ),
    )

    image = forms.ImageField(
        required=True, widget=forms.FileInput(attrs={"class": "form-control mb-3"})
    )

    reason = forms.ChoiceField(
        choices=[
            ("Damaged Item", "Damaged Item"),
            ("Wrong Item Delivered", "Wrong Item Delivered"),
            ("other", "Other"),
        ],
        required=True,
        widget=forms.Select(attrs={"class": "form-control mb-3"}),
    )
