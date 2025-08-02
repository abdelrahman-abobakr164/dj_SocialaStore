from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required


from accounts.models import Contact


User = get_user_model()


@login_required
def settings(request):
    return render(request, "account/settings.html")


@login_required
def my_account(request):
    user = User.objects.get(username=request.user.username)
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        file = request.FILES.get("file")
        last_name = request.POST.get("last_name")
        phone = request.POST.get("phone")

        user.first_name = first_name
        user.last_name = last_name
        user.phone = phone
        user.save()

        if file:
            user.img = file
            user.save()

        return redirect("my-account")
    return render(request, "account/my_account.html", {"profile": user})


def contact_us(request):
    if request.method == "POST":
        email = request.POST.get("email")
        message = request.POST.get("message")
        Contact.objects.create(email=email, message=message)
        return redirect("contact-us")
    return render(request, "account/contact_us.html")
