import json
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from orders.forms import RefundForm, CheckoutForm
from django.core.mail import send_mail
from django.contrib import messages
from cart.forms import CouponForm
from django.conf import settings
import logging

from core.models import Product
from orders.models import *
from cart.models import *

import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)


def is_valid_form(values):
    valid = True
    for field in values:
        if field == "":
            valid = False
    return valid


@login_required(login_url="account_login")
def checkout(request):
    cart_obj, created = Cart.objects.get_or_new(request)
    cart_items = CartItem.objects.filter(cart=cart_obj)

    if not cart_items.exists():
        messages.info(request, "You Don't Have Orders")
        return redirect("shop")

    form = CheckoutForm()
    couponform = CouponForm()

    last_payment = Payment.objects.filter(user=request.user)
    if last_payment.exists():
        last_payment.latest("created_at")

    default_shipping_address = Address.objects.filter(
        user=request.user, default=True, address_type="Shipping"
    )
    default_billing_address = Address.objects.filter(
        user=request.user, default=True, address_type="Billing"
    )

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():

            order = Order.objects.create(
                user=request.user, total=request.session.get("total_price")
            )

            use_default_billing = request.POST.get("use_default_billing")
            use_default_shipping = request.POST.get("use_default_shipping")
            set_default_billing = form.cleaned_data.get("set_default_billing")

            if use_default_shipping:
                shipping_address_qs = Address.objects.get(
                    user=request.user,
                    default=True,
                    address_type="Shipping",
                    id=use_default_shipping,
                )
                order.shipping_address = shipping_address_qs

            else:
                shipping_first_name = form.cleaned_data.get("shipping_first_name")
                shipping_last_name = form.cleaned_data.get("shipping_last_name")
                shipping_email = form.cleaned_data.get("shipping_email")
                shipping_phone = form.cleaned_data.get("shipping_phone")
                shipping_address1 = form.cleaned_data.get("shipping_address1")
                shipping_address2 = form.cleaned_data.get("shipping_address2")
                shipping_city = form.cleaned_data.get("shipping_city")
                shipping_zip = form.cleaned_data.get("shipping_zip")

                if is_valid_form(
                    [
                        shipping_first_name,
                        shipping_last_name,
                        shipping_email,
                        shipping_phone,
                        shipping_address1,
                        shipping_city,
                    ]
                ):
                    shipping_address = Address.objects.create(
                        user=request.user,
                        first_name=shipping_first_name,
                        last_name=shipping_last_name,
                        email=shipping_email,
                        phone=shipping_phone,
                        address1=shipping_address1,
                        address2=shipping_address2,
                        city=shipping_city,
                        zipcode=shipping_zip,
                        address_type="Shipping",
                    )
                    shipping_address.save()

                    order.shipping_address = shipping_address

                    set_default_shipping = form.cleaned_data.get("set_default_shipping")
                    if set_default_shipping:
                        shipping_address.default = True
                        shipping_address.save()

                else:
                    messages.error(
                        request, "Please Fill in Required Shipping Address Fields"
                    )
                    return redirect("checkout")

            same_shipping_address = form.cleaned_data.get("same_shipping_address")
            if same_shipping_address:

                billing_address = Address.objects.create(
                    user=request.user,
                    first_name=shipping_first_name,
                    last_name=shipping_last_name,
                    email=shipping_email,
                    phone=shipping_phone,
                    address1=shipping_address1,
                    address2=shipping_address2,
                    city=shipping_city,
                    zipcode=shipping_zip,
                    address_type="Billing",
                )
                billing_address.save()

                order.billing_address = billing_address
                if set_default_billing:
                    billing_address.default = True
                    billing_address.save()

            elif use_default_billing:
                billing_address_qs = Address.objects.get(
                    user=request.user,
                    default=True,
                    address_type="Billing",
                    id=use_default_billing,
                )
                order.billing_address = billing_address_qs

            else:
                billing_first_name = form.cleaned_data.get("billing_first_name")
                billing_last_name = form.cleaned_data.get("billing_last_name")
                billing_email = form.cleaned_data.get("billing_email")
                billing_phone = form.cleaned_data.get("billing_phone")
                billing_address1 = form.cleaned_data.get("billing_address1")
                billing_address2 = form.cleaned_data.get("billing_address2")
                billing_city = form.cleaned_data.get("billing_city")
                billing_zip = form.cleaned_data.get("billing_zip")

                if is_valid_form(
                    [
                        billing_first_name,
                        billing_last_name,
                        billing_email,
                        billing_phone,
                        billing_address1,
                        billing_city,
                    ]
                ):
                    billing_address = Address.objects.create(
                        user=request.user,
                        first_name=billing_first_name,
                        last_name=billing_last_name,
                        email=billing_email,
                        phone=billing_phone,
                        address1=billing_address1,
                        address2=billing_address2,
                        city=billing_city,
                        zipcode=billing_zip,
                        address_type="Billing",
                    )

                    billing_address.save()
                    order.billing_address = billing_address

                    if set_default_billing:
                        billing_address.default = True
                        billing_address.save()
                else:
                    messages.error(
                        request,
                        "Please fill in the required billing address fields",
                    )
                    return redirect("checkout")

            order.save()

            for item in cart_items:
                orderItem = OrderItem()
                orderItem.user_id = request.user.id
                orderItem.order_id = order.id
                orderItem.product_id = item.product.id
                orderItem.quantity = item.quantity
                orderItem.color = item.color
                orderItem.size = item.size
                orderItem.product_price = item.get_product_price()
                orderItem.save()

            cart_items.delete()

            payment_option = form.cleaned_data.get("payment_option")
            if payment_option == "Stripe":
                return redirect(
                    "payment",
                    payment_option="Stripe",
                    order_number=order.order_number,
                )

            elif payment_option == "CashOnDelivery":
                return redirect(
                    "payment",
                    payment_option="CashOnDelivery",
                    order_number=order.order_number,
                )

            else:
                messages.erorr(request, "Invalid payment option selected")
                return redirect("checkout")

        else:
            messages.error(request, "Please fill in the required Fields")
            return redirect("checkout")

    context = {
        "form": form,
        "couponform": couponform,
        "last_payment": last_payment,
        "default_shipping_address": default_shipping_address,
        "default_billing_address": default_billing_address,
    }
    return render(request, "orders/checkout.html", context)


@login_required(login_url="account_login")
def payment(request, payment_option, order_number):

    if Order.objects.filter(order_number=order_number, is_ordered=False).count() == 0:
        messages.warning(request, "You Don't Have an Order")
        return redirect("shop")

    order_obj = get_object_or_404(Order, order_number=order_number)
    request.session["order_id"] = str(order_obj.order_number)

    orderitems = OrderItem.objects.filter(order=order_obj)

    if payment_option in ["Stripe", "CashOnDelivery"]:
        if payment_option == "CashOnDelivery" and request.method == "POST":
            Payment.objects.create(
                user=request.user,
                order_id=order_obj.id,
                status=True,
                amount=order_obj.total,
                method="CashOnDelivery",
            )

            for item in orderitems:
                product = Product.objects.get(id=item.product.id)
                product.stock -= item.quantity
                product.save()

            if "applied_coupon" in request.session:
                coupon = Coupon.objects.get(amount=request.session["applied_coupon"])
                coupon.used_count += 1
                coupon.save()
                request.session["applied_coupon"].delete()

            order_obj.status = "Paid"
            order_obj.is_ordered = True
            order_obj.save()

            send_mail(
                subject="Cahs On Delivery Payment Confirmation",
                message=f"Payment of ${order_obj.total} was successful, Order id ({order_obj.order_number}).",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[request.user.email],
            )
            return redirect("success", order_number=order_obj.order_number)

    else:
        messages.error(request, "Not Supported Payment Option")

    context = {
        "order": order_obj,
        "payment_option": payment_option,
        "stripe_public_key": settings.STRIPE_PUBLISHABLE_KEY,
    }

    return render(request, "orders/payment.html", context)


@csrf_exempt
def create_checkout_session(request, order_number):
    if request.method == "POST":
        try:
            order = Order.objects.get(order_number=order_number, is_ordered=False)
            order_items = OrderItem.objects.filter(order=order)

            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": item.product.name,
                                "images": [
                                    request.build_absolute_uri(item.product.img.url)
                                ],
                            },
                            "unit_amount": int(item.get_product_price() * 100),
                        },
                        "quantity": item.quantity,
                    }
                    for item in order_items
                ],
                mode="payment",
                success_url=f"{request.build_absolute_uri(f'/orders/success/{order.order_number}')}",
                cancel_url=f"{request.build_absolute_uri(f'/orders/failed/{order.order_number}')}",
                metadata={"order_number": order.order_number},
            )
            return JsonResponse({"id": session.id})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)


@login_required(login_url="account_login")
def request_refund(request, order_number):
    if request.method == "POST":
        send_mail(
            "Requested Refund",
            f"You Can Refund Your Order From This Link Below http://127.0.0.1:8000/orders/refund/{order_number} Click Here",
            settings.EMAIL_HOST_USER,
            [request.user.email],
            fail_silently=False,
        )

        return redirect("order-detail", order_number=order_number)
    return redirect("order-detail", order_number=order_number)


@login_required(login_url="account_login")
def refund_payment(request, order_number):
    form = RefundForm()
    order = get_object_or_404(Order, order_number=order_number)
    if request.method == "POST":
        form = RefundForm(request.POST)
        if form.is_valid():
            try:
                payment = get_object_or_404(Payment, order=order)

                refund_model = Refund.objects.create(
                    user=request.user,
                    order=order,
                    email=form.cleaned_data["email"],
                    image=form.cleaned_data["image"],
                    reason=form.cleaned_data["reason"],
                    payment=payment,
                    refund_id=f"ref_{uuid.uuid4()}",
                    amount=int(order.total * 100) / 100,
                    status="PENDING",
                )

                order.status = "Refunded"
                order.save()

                send_mail(
                    "Refund Was Send",
                    f"We Recieved The Refunded We Well Check Your Order Soon. Refund Id {refund_model.refund_id}",
                    settings.EMAIL_HOST_USER,
                    recipient_list=[form.cleaned_data["email"]],
                    fail_silently=False,
                )

                messages.success(request, f"The Refund Sent.")
                return redirect("order-detail", order_number=order_number)

            except Order.DoesNotExist:
                return JsonResponse(
                    {"status": "error", "message": "Order Does Not Exist"}, status=404
                )

            except stripe.error.StripeError as e:
                messages.error(
                    request, f"Stripe refund failed. Please try again later. {e}"
                )
                return redirect("order-detail", order_number=order_number)

        else:
            messages.error(request, "Invalid form data")
            return redirect("order-detail", order_number=order_number)

    return render(request, "orders/refund.html", {"order": order, "form": form})


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    webhook_secret = "whsec_GnmNhv3KnathMR1pVUmhlYx1VeIyCm49"

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError as e:
        messages.error(request, f"Invalid payload {e}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        messages.error(request, f"Invalid signature {e}")
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        order_number = session.get("metadata", {}).get("order_number")

        try:
            order = Order.objects.get(order_number=order_number, is_ordered=False)
            order_items = OrderItem.objects.filter(order=order)

            for item in order_items:
                product = Product.objects.get(id=item.product.id)
                product.stock -= item.quantity
                product.save()

            if "applied_coupon" in request.session:
                coupon = Coupon.objects.get(amount=request.session["applied_coupon"])
                coupon.used_count += 1
                coupon.save()
                request.session["applied_coupon"].delete()

            order.status = "Paid"
            order.is_ordered = True
            order.save()

            Payment.objects.create(
                user=order.user,
                order=order,
                payment_id=session["payment_intent"],
                status=True,
                amount=session["amount_total"] / 100,
                method="Stripe",
            )

            send_mail(
                subject="Stripe Payment",
                message=f"Thank you for your payment. Your order ID is {order_number}.",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[order.user.email],
                fail_silently=False,
            )

        except Order.DoesNotExist:
            messages.error(request, f"Order with ID {order_number} not found.")
    return JsonResponse({"status": "success"})


@login_required(login_url="account_login")
def success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, "orders/success.html", {"order": order})


@login_required(login_url="account_login")
def failed(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, "orders/failed.html", {"order": order})


@login_required(login_url="account_login")
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    payment = None
    if order.is_ordered == True:
        payment = Payment.objects.get(order=order)

    form = CheckoutForm()

    context = {"order": order, "form": form, "payment": payment}
    return render(request, "orders/order-detail.html", context)


@login_required(login_url="account_login")
def order_list(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, "orders/order-list.html", {"orders": orders})


@login_required(login_url="account_login")
def incomplete_orders(request):
    if request.method == "POST":
        payment_option = request.POST.get("payment_option")
        order_number = request.POST.get("order_number")
        return redirect(
            "payment", payment_option=payment_option, order_number=order_number
        )


@login_required(login_url="account_login")
def order_canceled(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if request.method == "POST":
        ordersitems = OrderItem.objects.filter(user=request.user, order=order)
        for i in ordersitems:
            ps = Product.objects.get(id=i.product.id)
            ps.stock += 1
            ps.save()

        order.is_ordered = False
        order.status = "Canceled"
        order.save()
        messages.success(request, "Your Order Has Been Canceled")
        return redirect("order-list")
    return render(request, "orders/order-canceled.html", {"order": order})
