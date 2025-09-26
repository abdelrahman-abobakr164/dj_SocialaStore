from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.contrib import messages

from accounts.models import Contact
from orders.models import Address
from accounts.forms import AddressForm, UserForm

User = get_user_model()


@login_required
def settings(request):
    return render(request, "accounts/settings.html")


@login_required
def my_account(request):
    user = User.objects.get(username=request.user.username)
    if request.method == "POST":
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your Information Has Been Updated Successfully!')
            return redirect("my-account")
    else:
        form = UserForm(instance=user)
    return render(request, "accounts/my-account.html", {"profile": user, 'form':form})


@login_required
def my_address(request):
    shipping_address = Address.objects.filter(
        user=request.user, address_type="Shipping", default=True
    ).last()
    billing_address = Address.objects.filter(
        user=request.user, address_type="Billing", default=True
    ).last()

    shipping_form = AddressForm(prefix="shipping", instance=shipping_address)
    billing_form = AddressForm(prefix="billing", instance=billing_address)

    if request.method == "POST":
        ShippingForm = AddressForm(
            request.POST, instance=shipping_address, prefix="shipping"
        )
        BillingForm = AddressForm(
            request.POST, instance=billing_address, prefix="billing"
        )

        if ShippingForm.is_valid() and BillingForm.is_valid():
            ShippingObj = ShippingForm.save(commit=False)
            ShippingObj.user = request.user
            ShippingObj.default = True
            ShippingObj.address_type = "Shipping"
            ShippingObj.save()

            if "same_shipping_address" in request.POST:
                billing_obj, created = Address.objects.update_or_create(
                    user=request.user,
                    address_type="Billing",
                    defaults={
                        "default": True,
                        "first_name": ShippingObj.first_name,
                        "last_name": ShippingObj.last_name,
                        "phone": ShippingObj.phone,
                        "email": ShippingObj.email,
                        "address1": ShippingObj.address1,
                        "address2": ShippingObj.address2,
                        "city": ShippingObj.city,
                        "zipcode": ShippingObj.zipcode,
                    },
                )

            else:
                Address.objects.filter(
                    user=request.user, address_type="Billing", default=True
                ).update(default=False)

                billing_obj = BillingForm.save(commit=False)
                billing_obj.user = request.user
                billing_obj.default = True
                billing_obj.address_type = "Billing"
                billing_obj.save()
        else:
            messages.error(request, f"Error.")
            return redirect("my-address")

        messages.success(request, "Your Address were Saved Successfully!")
        return redirect("my-address")

    return render(
        request,
        "accounts/my-address.html",
        {"shipping": shipping_form, "billing": billing_form},
    )


def contact_us(request):
    if request.method == "POST":
        email = request.POST.get("email")
        message = request.POST.get("message")
        Contact.objects.create(email=email, message=message)
        return redirect("contact-us")
    return render(request, "accounts/contact-us.html")
