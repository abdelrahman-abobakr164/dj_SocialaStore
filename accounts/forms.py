from django import forms
from phonenumber_field.formfields import PhoneNumberField
from orders.models import Address
from django.contrib.auth import get_user_model

User = get_user_model()


class UserForm(forms.ModelForm):
    phone = PhoneNumberField(region='EG')

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "phone",
            "username",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs["class"] = "form-control"
            self.fields[field].widget.attrs["placeholder"] = field.capitalize().replace(
                "_", " "
            )


class AddressForm(forms.ModelForm):
    phone = PhoneNumberField(required=True)

    class Meta:
        model = Address
        fields = [
            "first_name",
            "last_name",
            "phone",
            "email",
            "address1",
            "address2",
            "city",
            "zipcode",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs["class"] = "form-control"
            self.fields[field].widget.attrs["placeholder"] = field.capitalize().replace(
                "_", " "
            )
