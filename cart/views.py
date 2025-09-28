from django.shortcuts import redirect, get_object_or_404, render
from cart.forms import VariationForm, CouponForm
from django.utils.timezone import now
from django.http import JsonResponse
from django.contrib import messages

from cart.models import *
from core.models import *
from orders.models import OrderItem


def validiation_coupon(request, code, cart_obj):
    try:
        coupon = Coupon.objects.get(code=code)
        cart_items = CartItem.objects.filter(cart=cart_obj)
        total_price = (
            sum(item.get_product_price() for item in cart_items)
            if cart_items
            else request.session.get("total_price")
        )

        if cart_items.count() == 0 and "orderitem_id" not in request.session:
            messages.warning(request, "You Don't Have Any Item.")
            return None

        elif coupon.amount >= total_price:
            messages.warning(request, "Your Total Price is Less Than Coupon Amount.")
            return None

        elif coupon.end_date and now() > coupon.end_date:
            messages.warning(request, "This Coupon Code is Expired.")
            return None

        elif coupon.max_uses and coupon.used_count == coupon.max_uses:
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
                messages.success(request, "Your Coupon Added Succesfully!")

            return redirect(url)

        else:
            return redirect(url)


def add_and_buy(request, category_slug, product_slug, pk):
    product = get_object_or_404(
        Product, category__slug=category_slug, slug=product_slug, pk=pk
    )

    cart_obj, created = Cart.objects.get_or_new(request)
    cart_items = CartItem.objects.filter(cart=cart_obj, product=product)
    product_count = sum(item.quantity for item in cart_items)

    if request.method == "POST":
        action = request.POST.get("action")
        if not action:
            messages.warning(request, "Don't Mess")
            return redirect(request.META.get("HTTP_REFERER", "/"))

        form = VariationForm(request.POST, product=product)

        if not form.is_valid():
            messages.warning(request, "Please select valid variations")
            return redirect(request.META.get("HTTP_REFERER", "/"))

        if product_count >= product.stock:
            messages.warning(
                request, f'Only {product.stock} Left in Stock for "{product.name}"'
            )
            return redirect(request.META.get("HTTP_REFERER", "/"))

        color_id = request.POST.get("color")
        size_id = request.POST.get("size")

        try:
            color = (
                Variation.objects.get(id=color_id, active=True) if color_id else None
            )
            size = Variation.objects.get(id=size_id, active=True) if size_id else None

            size_price = size.price if size and size.price else 0
            color_price = color.price if color and color.price else 0
            base_price = product.discount_price or product.price
            total_price = base_price + size_price + color_price

            if action == "add_to_cart" or action == "+":
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
                return redirect(request.META.get("HTTP_REFERER", "/"))

            elif action == "buy_now":
                orderitem = OrderItem.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    product_id=product.id,
                    color=color,
                    size=size,
                    quantity=1,
                    product_price=total_price,
                )
                orderitem.save()
                request.session["orderitem_id"] = orderitem.id

                if request.user.is_authenticated:
                    return redirect("checkout")
                else:
                    return redirect("/accounts/login/?next=/orders/checkout/")

        except Variation.DoesNotExist:
            messages.warning(request, "The selected variation is not available")
            return redirect(request.META.get("HTTP_REFERER", "/"))

    return redirect(request.META.get("HTTP_REFERER", "/"))


def remove_from_cart(request, cartitem_pk):
    cart_obj, created = Cart.objects.get_or_new(request)
    cartitems = CartItem.objects.filter(cart=cart_obj, id=cartitem_pk)

    if cartitems.exists():
        cartitems.delete()
        return redirect("cart-summary")

    else:
        return redirect("cart-summar")


def minus_from_cart(request, cartitem_pk):
    cart_obj, created = Cart.objects.get_or_new(request)

    try:
        cartitems = CartItem.objects.get(cart=cart_obj, pk=cartitem_pk)

        if cartitems.quantity > 1:
            cartitems.quantity -= 1
            cartitems.save()
        else:
            cartitems.delete()
            return redirect("cart-summary")

    except CartItem.DoesNotExist:
        return redirect("cart-summary")


def cart_summary(request):
    return render(request, "cart/cart.html", {"couponform": CouponForm()})
