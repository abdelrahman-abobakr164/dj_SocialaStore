from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404, render
from cart.forms import VariationForm, CouponForm
from django.utils.timezone import now
from django.contrib import messages

from cart.models import *
from core.models import *


def _json_or_redirect(request, data, url, status=200):
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(data, status=status)
    else:
        if not data.get("success"):
            messages.warning(request, data.get("message", "An error occurred."))
        return redirect(url)


def validiation_coupon(request, code, cart_obj):
    try:
        coupon = Coupon.objects.get(code=code)
        cart_items = CartItem.objects.filter(cart=cart_obj)

        if cart_items.count() == 0:
            messages.error(request, "You Don't Have Any Item")
            return None

        elif not coupon.is_active:
            messages.warning(request, "This Coupon Code is Not Active Yet.")
            return None

        elif coupon.amount >= sum(item.get_product_price() for item in cart_items):
            messages.error(request, "Your Total Price is Less Than Coupon Amount")
            return None

        elif coupon.minimum_purchase_amount >= sum(
            item.get_product_price() for item in cart_items
        ):
            messages.error(request, "Yoursss Total Price is Less Than Coupon Amount")
            return None

        elif coupon.end_date and now() > coupon.end_date:
            messages.warning(request, "This Coupon Code is Expired.")
            return None

        elif coupon.max_uses and coupon.used_count >= coupon.max_uses:
            messages.warning(request, "This Coupon Code Has Been Ended.")
            return None

        return coupon

    except Coupon.DoesNotExist:
        messages.error(request, "Invlalid Coupon Code")
        None


def apply_coupon(request):
    url = request.META.get("HTTP_REFERER")
    cart_obj, created = Cart.objects.get_or_new(request)
    cart_items = CartItem.objects.filter(cart=cart_obj)

    total_price = sum(item.get_product_price() for item in cart_items)

    if request.method == "POST":
        form = CouponForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data.get("code")
            coupon_code = validiation_coupon(request, code, cart_obj)

            if coupon_code:
                request.session["total_price"] = float(total_price - coupon_code.amount)

                request.session["applied_coupon"] = float(coupon_code.amount)

                return redirect(url)

            else:
                return redirect(url)

        else:
            messages.error(request, "This Field is Required")
            return redirect(url)


def add_to_cart(request, category_slug, product_slug, pk):
    url = request.META.get("HTTP_REFERER")
    product = get_object_or_404(
        Product, category__slug=category_slug, slug=product_slug, pk=pk
    )

    cart_obj, created = Cart.objects.get_or_new(request)
    cart_items = CartItem.objects.filter(cart=cart_obj, product=product)
    product_count = sum(item.quantity for item in cart_items)

    if request.method == "POST":
        if product_count >= product.stock:
            messages.warning(request, "There is no Quantity available for this product")
            return redirect(url)

        form = VariationForm(request.POST, product=product)
        if form.is_valid():

            color_id = form.cleaned_data.get("color")
            size_id = form.cleaned_data.get("size")

            color = (
                Variation.objects.get(
                    product=product, id=color_id, key="color", active=True
                )
                if color_id
                else None
            )

            size = (
                Variation.objects.get(
                    product=product, id=size_id, key="size", active=True
                )
                if size_id
                else None
            )

            size_price = size.price if size and size.price else 0
            color_price = color.price if color and color.price else 0
            base_price = product.discount_price or product.price
            total_price = base_price + size_price + color_price

            cartitems = CartItem.objects.filter(
                cart=cart_obj,
                product=product,
                color=color,
                size=size,
            ).first()

            if cartitems:
                cartitems.price += total_price
                cartitems.quantity += 1
                cartitems.save()
            else:
                CartItem.objects.create(
                    cart=cart_obj,
                    product=product,
                    color=color,
                    size=size,
                    price=total_price,
                )
            messages.success(request, "Product Added To Cart!")

    return redirect(url)


def remove_from_cart(request, cartitem_pk):
    cart_obj, created = Cart.objects.get_or_new(request)
    cartitems = CartItem.objects.filter(cart=cart_obj, id=cartitem_pk)

    if cartitems.exists():
        cartitems.delete()
    return redirect(request.META.get("HTTP_REFERER"))


def minus_from_cart(request, cartitem_pk):
    cart_obj, created = Cart.objects.get_or_new(request)
    cartitems = CartItem.objects.get(cart=cart_obj, pk=cartitem_pk)

    if cartitems.quantity > 1:
        cartitems.quantity -= 1
        cartitems.save()

    else:
        cartitems.delete()

    return redirect(request.META.get("HTTP_REFERER"))


def cart_summary(request):
    couponform = CouponForm()
    if request.method == "POST":
        cart_item_id = request.POST.get("cart_item_id")
        if cart_item_id:
            try:
                cart_item = CartItem.objects.get(pk=cart_item_id)
                size_price = (
                    cart_item.size.price
                    if cart_item.size and cart_item.size.price
                    else 0
                )
                color_price = (
                    cart_item.color.price
                    if cart_item.color and cart_item.color.price
                    else 0
                )

                if cart_item.product.discount_price:
                    total_price = (
                        cart_item.product.discount_price + size_price + color_price
                    )

                else:
                    total_price = cart_item.product.price + size_price + color_price

                cart_item.price += total_price
                cart_item.quantity += 1
                cart_item.save()
                return redirect("cart-summary")
            except CartItem.DoesNotExist:
                return redirect("cart-summary")

    return render(request, "cart/cart.html", {"couponform": couponform})
