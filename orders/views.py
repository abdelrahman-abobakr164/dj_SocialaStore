from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from orders.forms import RefundForm, CheckoutForm
from django.contrib import messages
from django.db import transaction
from django.conf import settings
import requests
import logging
import json
from orders.tasks import send_mails_to_clients
from cart.forms import CouponForm
from core.models import Product
from orders.models import *
from cart.models import *
import paypalrestsdk
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)


def get_paypal_access_token():
    url = f"{settings.PAYPAL_BASE_URL}/v1/oauth2/token"
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US",
    }
    data = {"grant_type": "client_credentials"}

    response = requests.post(
        url,
        headers=headers,
        data=data,
        auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
    )

    if response.status_code == 200:
        return response.json()["access_token"]
    return None


def is_valid_form(values):
    valid = True
    for field in values:
        if field == "":
            valid = False
    return valid


@login_required(login_url="account_login")
def checkout(request):
    cart_obj, created = Cart.objects.get_or_new(request)
    cart_items = CartItem.objects.filter(cart=cart_obj).select_related(
        "product", "color", "size"
    )

    if not cart_items.exists() and "orderitem_id" not in request.session:
        return redirect("shop")

    for item in cart_items:
        if item.product.stock < item.quantity:
            messages.warning(
                request,
                f'Sorry, The Quantity of "{product.name}" has Run Out',
            )
            return redirect("shop")

    form = CheckoutForm()

    last_payment = (
        Payment.objects.filter(user=request.user).order_by("-created_at").first()
    )

    default_shipping_address = Address.objects.filter(
        user=request.user, default=True, address_type="Shipping"
    )
    default_billing_address = Address.objects.filter(
        user=request.user, default=True, address_type="Billing"
    )

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                products_ids = cart_items.values_list("product_id", flat=True)
                products = Product.objects.select_for_update().filter(
                    id__in=products_ids
                )
                product_dict = {p.id: p for p in products}
                for item in cart_items:
                    product = product_dict.get(item.id)
                    if item.product.stock < item.quantity:
                        messages.warning(
                            request,
                            f'Sorry, "{product.name}" has insufficient stock. Available: {product.stock}',
                        )
                        return redirect("cart-summary")

                order = Order()
                order.user = request.user
                order.total = request.session.get("total_price", 0)

                use_default_shipping = request.POST.get("use_default_shipping")
                set_default_shipping = form.cleaned_data.get(
                    "set_default_shipping", False
                )
                shipping_data = {
                    "first_name": form.cleaned_data.get("first_name"),
                    "last_name": form.cleaned_data.get("last_name"),
                    "email": form.cleaned_data.get("shipping_email"),
                    "phone": form.cleaned_data.get("shipping_phone"),
                    "address1": form.cleaned_data.get("shipping_address1"),
                    "address2": form.cleaned_data.get("address2", ""),
                    "city": form.cleaned_data.get("shipping_city"),
                    "zip": form.cleaned_data.get("shipping_zip", ""),
                    "address_type": "Shipping",
                    "user": request.user,
                }
                if use_default_shipping and default_shipping_address.exists():
                    shipping_address_qs = Address.objects.get(
                        user=request.user,
                        default=True,
                        address_type="Shipping",
                        id=use_default_shipping,
                    )
                    order.shipping_address = shipping_address_qs

                else:
                    if is_valid_form(
                        [
                            shipping_data["shipping_first_name"],
                            shipping_data["shipping_last_name"],
                            shipping_data["shipping_email"],
                            shipping_data["shipping_phone"],
                            shipping_data["shipping_address1"],
                            shipping_data["shipping_city"],
                        ]
                    ):
                        shipping_address = Address.objects.create(**shipping_data)
                        order.shipping_address = shipping_address

                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()

                    else:
                        messages.warning(
                            request, "Please Fill in Required Shipping Address Fields"
                        )
                        return redirect("checkout")

                same_shipping_address = form.cleaned_data.get(
                    "same_shipping_address", False
                )
                use_default_billing = request.POST.get("use_default_billing")
                set_default_billing = form.cleaned_data.get(
                    "set_default_billing", False
                )

                if same_shipping_address:

                    billing_address = Address.objects.create(
                        first_name=shipping_data["first_name"],
                        last_name=shipping_data["last_name"],
                        email=shipping_data["email"],
                        phone=shipping_data["phone"],
                        address1=shipping_data["address1"],
                        address2=shipping_data["address2"],
                        city=shipping_data["city"],
                        zip=shipping_data["zip"],
                        user=request.user,
                        address_type="Billing",
                    )

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
                    billing_data = {
                        "billing_first_name": form.cleaned_data.get(
                            "billing_first_name"
                        ),
                        "billing_last_name": form.cleaned_data.get("billing_last_name"),
                        "billing_email": form.cleaned_data.get("billing_email"),
                        "billing_phone": form.cleaned_data.get("billing_phone"),
                        "billing_address1": form.cleaned_data.get("billing_address1"),
                        "billing_address2": form.cleaned_data.get(
                            "billing_address2", ""
                        ),
                        "billing_city": form.cleaned_data.get("billing_city"),
                        "billing_zip": form.cleaned_data.get("billing_zip", ""),
                        "user": request.user,
                        "address_type": "Billing",
                    }

                    if is_valid_form(
                        [
                            billing_data["billing_first_name"],
                            billing_data["billing_last_name"],
                            billing_data["billing_email"],
                            billing_data["billing_phone"],
                            billing_data["billing_address1"],
                            billing_data["billing_city"],
                        ]
                    ):
                        billing_address = Address.objects.create(**billing_data)
                        billing_address.save()
                        order.billing_address = billing_address

                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()
                    else:
                        messages.warning(
                            request,
                            "Please fill in the required billing address fields",
                        )
                        return redirect("checkout")

                order.save()
                if "orderitem_id" in request.session:
                    OrderItem.objects.filter(
                        id=request.session.get("orderitem_id")
                    ).update(order=order)
                    del request.session["orderitem_id"]
                else:
                    order_items = []
                    for item in cart_items:
                        order_items.append(
                            OrderItem(
                                user=request.user,
                                order=order,
                                product=item.product,
                                quantity=item.quantity,
                                color=item.color,
                                size=item.size,
                                product_price=item.get_product_price(),
                            )
                        )
                    if order_items:
                        OrderItem.objects.bulk_create(order_items)

                    cart_items.delete()

                payment_option = form.cleaned_data.get("payment_option")
                if payment_option == "Stripe":
                    return redirect(
                        "payment",
                        payment_option="Stripe",
                        order_number=order.order_number,
                    )

                elif payment_option == "PayPal":
                    return redirect(
                        "payment",
                        payment_option="PayPal",
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
            for field, errors in form.errors.items():
                for error in errors:
                    messages.warning(request, f"{field}: {error}")
            return redirect("checkout")

    context = {
        "form": form,
        "couponform": CouponForm(),
        "last_payment": last_payment,
        "default_shipping_address": default_shipping_address,
        "default_billing_address": default_billing_address,
    }
    return render(request, "orders/checkout.html", context)


@login_required(login_url="account_login")
def payment(request, payment_option, order_number):

    if not Order.objects.filter(order_number=order_number, is_ordered=False).exists():
        messages.warning(request, "You Don't Have an Order")
        return redirect("shop")

    if payment_option not in ["Stripe", "CashOnDelivery", "PayPal"]:
        messages.error(request, "Not Supported Payment Option")
        return redirect("checkout")

    try:
        order_obj = Order.objects.select_related(
            "shipping_address", "billing_address"
        ).get(order_number=order_number, user=request.user, is_ordered=False)
    except Order.DoesNotExist:
        messages.error(request, "Order Not Found")
        return redirect("shop")

    order_items = OrderItem.objects.filter(
        order=order_obj, user=request.user
    ).select_related("product", "color", "size")

    if payment_option == "CashOnDelivery":
        if request.method == "POST":
            try:
                with transaction.atomic():
                    products_ids = order_items.values_list("product_id", flat=True)
                    products = Product.objects.select_for_update().filter(
                        id__in=products_ids
                    )
                    product_dict = {p.id: p for p in products}

                    for item in order_items:
                        product = product_dict.get(item.product.id)
                        if not product:
                            messages.error(
                                request, f"Product {item.product.name} not found"
                            )
                            return redirect(request.META.get("HTTP_REFERER", "shop"))

                        if product.stock < item.quantity:
                            messages.warning(
                                request,
                                f'Sorry, "{product.name}" has insufficient stock. Available: {product.stock}',
                            )
                            return redirect(request.META.get("HTTP_REFERER"))

                        product.stock -= item.quantity
                        product.bestseller += 1

                    Product.objects.bulk_update(
                        list(product_dict.values()), ["stock", "bestseller"]
                    )

                    Payment.objects.create(
                        user=request.user,
                        order=order_obj,
                        status=True,
                        amount=order_obj.total,
                        method="CashOnDelivery",
                    )
                    if "applied_coupon" in request.session:
                        try:
                            coupon = Coupon.objects.get(
                                amount=request.session["applied_coupon"]
                            )
                            coupon.used_count += 1
                            coupon.save()
                        except Coupon.DoesNotExist:
                            pass
                        finally:
                            del request.session["applied_coupon"]

                    order_obj.status = "Pending"
                    order_obj.is_ordered = True
                    order_obj.save()

                    send_mails_to_clients.delay(
                        f"COD Payment Confirmation {order_obj.total}",
                        f"Payment of ${order_obj.total} was successful, Order id ({order_obj.order_number}).",
                        request.user.email,
                    )

                    messages.success(request, "Order placed successfully!")
                    return redirect("success", order_number=order_obj.order_number)

            except Exception as e:
                messages.error(request, f"An error occurred: {e}")
                return redirect(
                    "payment", payment_option=payment_option, order_number=order_number
                )

        context = {
            "order": order_obj,
            "order_items": order_items,
            "payment_option": payment_option,
        }
    else:
        request.session["order_id"] = str(order_obj.order_number)

        context = {
            "order": order_obj,
            "order_items": order_items,
            "payment_option": payment_option,
            "stripe_public_key": settings.STRIPE_PUBLISHABLE_KEY,
            "paypal_client_id": settings.PAYPAL_CLIENT_ID,
        }

    return render(request, "orders/payment.html", context)


@login_required
@require_http_methods(["POST"])
def create_paypal_order(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    if order.is_ordered:
        return JsonResponse({"error": "Order already paid"}, status=400)

    access_token = get_paypal_access_token()
    if not access_token:
        return JsonResponse({"error": "Failed to authenticate with PayPal"}, status=500)

    items = []
    for item in order.items.all():
        items.append(
            {
                "name": item.product.name[:127],
                "unit_amount": {
                    "currency_code": "USD",
                    "value": str(item.product_price),
                },
                "quantity": str(item.quantity),
            }
        )

    url = f"{settings.PAYPAL_BASE_URL}/v2/checkout/orders"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "reference_id": str(order.order_number),
                "description": f"Order #{order.order_number}",
                "amount": {
                    "currency_code": "USD",
                    "value": str(order.total),
                    "breakdown": {
                        "item_total": {
                            "currency_code": "USD",
                            "value": str(order.total),
                        }
                    },
                },
                "items": items,
            }
        ],
        "application_context": {
            "brand_name": "Your Store Name",
            "landing_page": "BILLING",
            "user_action": "PAY_NOW",
            "return_url": f"{settings.SITE_URL}/payment/success/{order.order_number}",
            "cancel_url": f"{settings.SITE_URL}/payment/failed/{order.order_number}",
        },
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 201:
        return JsonResponse(response.json())
    else:
        return JsonResponse(
            {"error": "Failed to create PayPal order", "details": response.json()},
            status=500,
        )


@login_required
@require_http_methods(["POST"])
def capture_paypal_order(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    try:
        data = json.loads(request.body)
        paypal_order_id = data.get("orderID")
        order_data = data.get("orderData", {})
    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": f"Invalid request: {str(e)}"}, status=400
        )

    if not paypal_order_id:
        return JsonResponse(
            {"status": "error", "message": "Missing PayPal order ID"}, status=400
        )

    if order_data and order_data.get("status") == "COMPLETED":
        order.is_ordered = True
        order.status = "Pending"
        order.save()

        try:
            capture_id = order_data["purchase_units"][0]["payments"]["captures"][0][
                "id"
            ]
        except (KeyError, IndexError, TypeError):
            capture_id = paypal_order_id

        Payment.objects.update_or_create(
            order=order,
            defaults={
                "user": request.user,
                "payment_id": capture_id,
                "status": True,
                "amount": order.total,
                "method": "PayPal",
            },
        )

        send_mails_to_clients.delay(
            f"PayPal Payment Confirmation {order.total}",
            f"Thank you for your purchase. Your order ID is {order_number}.",
            order.user.email,
        )

        return JsonResponse(
            {"status": "success", "message": "Payment completed successfully"}
        )
    else:
        return JsonResponse(
            {
                "status": "error",
                "message": "Payment not completed or order data missing",
            },
            status=400,
        )


@require_POST
@csrf_exempt
def create_checkout_session(request, order_number):
    try:
        order = Order.objects.get(order_number=order_number, is_ordered=False)
        order_items = OrderItem.objects.filter(order=order).select_related("product")

        line_items = [
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": item.product.name,
                        "images": [request.build_absolute_uri(item.product.img.url)],
                    },
                    "unit_amount": max(
                        0,
                        int(item.get_product_price() * 100),
                    ),
                },
                "quantity": item.quantity,
            }
            for item in order_items
        ]

        session_kwargs = dict(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url=request.build_absolute_uri(
                f"/orders/success/{order.order_number}"
            ),
            cancel_url=request.build_absolute_uri(
                f"/orders/failed/{order.order_number}"
            ),
            metadata={
                "order_number": order.order_number,
                "applied_coupon": request.session.get('applied_coupon', {}).get('code'),
            },
        )

        session = stripe.checkout.Session.create(**session_kwargs)
        return JsonResponse({"id": session.id})

    except Order.DoesNotExist:
        return JsonResponse({"error": "Order not found"}, status=404)
    except stripe.StripeError as e:
        logger.error("Stripe error for order %s: %s", order_number, e)
        return JsonResponse({"error": str(e)}, status=502)
    except Exception as e:
        logger.exception(
            "Unexpected error creating checkout session for order %s", order_number
        )
        return JsonResponse({"error": "Internal server error"}, status=500)


@require_POST
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    webhook_secret = settings.STRIPE_WEBHOOK_KEY

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError as e:
        logger.warning(f"Stripe webhook invalid payload: {e}")
        return HttpResponse(status=400)
    except stripe.SignatureVerificationError as e:
        logger.warning(f"Stripe webhook invalid signature: {e}")
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})
        applied_coupon = metadata.get("applied_coupon")
        order_number = metadata.get("order_number")

        if not order_number:
            logger.error("Stripe webhook: missing order_number in metadata.")
            return HttpResponse(status=400)

        try:
            with transaction.atomic():
                order = Order.objects.select_for_update().get(
                    order_number=order_number, is_ordered=False
                )
                order_items = OrderItem.objects.filter(order=order).select_related(
                    "product"
                )
                product_dict = {}
                for item in order_items:
                    product = product_dict.setdefault(item.product.id, item.product)
                    product.stock -= item.quantity
                    product.bestseller += 1

                Product.objects.bulk_update(
                    list(product_dict.values()), ["stock", "bestseller"]
                )

                if applied_coupon:
                    Coupon.objects.filter(code=applied_coupon).update(
                        used_count=models.F("used_count") + 1
                    )
                    del applied_coupon

                order.status = "Paid"
                order.is_ordered = True
                order.save()

                payment, created = Payment.objects.get_or_create(
                    payment_id=session["payment_intent"],
                    defaults={
                        "user": order.user,
                        "order": order,
                        "status": True,
                        "amount": order.total,
                        "method": "Stripe",
                    },
                )

                if created:
                    send_mails_to_clients.delay(
                        f"Stripe Payment Confirmation {order.total}",
                        f"Thank you for your purchase. Your order ID is {order_number}.",
                        order.user.email,
                    )

        except Order.DoesNotExist:
            messages.info(request, f"No Order with This ID: {order_number} .")
            return JsonResponse({"status": "order_not_found"}, status=200)
        except Exception as e:
            logger.warning(
                f"Stripe webhook: no pending order found for order_number={order_number}"
            )
            logger.exception(
                f"Stripe webhook: unexpected error for order_number={order_number}: {e}"
            )
            return HttpResponse(status=500)
    return JsonResponse({"status": "success"})


@login_required(login_url="account_login")
def delete_from_order(request, payment_option, order_number):

    try:
        order_obj = Order.objects.get(
            user=request.user, is_ordered=False, order_number=order_number
        )
        try:
            orderitem = OrderItem.objects.filter(
                order=order_obj, user=request.user, product__stock__lt=1
            )

            if order_obj.items.count() == 1:
                orderitem.delete()
                order_obj.delete()
                return redirect(
                    "payment", payment_option=payment_option, order_number=order_number
                )
            elif orderitem.count() == 1:
                orderitem.delete()
                return redirect(
                    "payment", payment_option=payment_option, order_number=order_number
                )
            else:
                order_obj.delete()
                return redirect("shop")

        except OrderItem.DoesNotExist:
            messages.error(request, "Item Does Not Exist")
            return redirect(
                "payment", payment_option=payment_option, order_number=order_number
            )
    except Order.DoesNotExist:
        messages.error(request, "Order Does Not Exist")
        return redirect("shop")


@login_required(login_url="account_login")
def request_refund(request, order_number):
    if request.method == "POST":
        try:
            order = get_object_or_404(Order, order_number=order_number)
            payment = get_object_or_404(Payment, order=order)
            if payment.method == "Stripe":
                send_mails_to_clients.delay(
                    "Requested Refund",
                    f"You Can Refund Your Order From This Link Below \n http://127.0.0.1:8000/orders/refund/{uuid.uuid4()}/{order_number}/ Click Here.",
                    request.user.email,
                )

                return redirect("order-detail", order_number=order_number)
            else:
                return redirect("order-detail", order_number=order_number)

        except Order.DoesNotExist:
            pass
    else:
        messages.error(request, "Wrong Request")


@login_required(login_url="account_login")
def refund_payment(request, refund_number, order_number):
    forms = RefundForm()
    try:
        order = get_object_or_404(
            Order, order_number=order_number, status__in=["Paid", "Delivered"]
        )
        payment = get_object_or_404(Payment, order=order)

        if Refund.objects.filter(order=order).exists():
            messages.info(request, "Your Order is being considered")
            return redirect("order-detail", order_number=order_number)

        if payment.method == "Stripe":
            if request.method == "POST":
                form = RefundForm(request.POST, request.FILES)
                if form.is_valid():
                    refund_model = Refund.objects.create(
                        user=request.user,
                        order=order,
                        email=form.cleaned_data["email"],
                        image=form.cleaned_data["image"],
                        reason=form.cleaned_data["reason"],
                        payment=payment,
                        refund_id=f"ref_{refund_number}",
                        amount=int(order.total * 100) / 100,
                        status="PENDING",
                    )

                    order.status = "Refund Requested"
                    order.save()

                    send_mails_to_clients.delay(
                        "Refund Was Send",
                        f"We Recieved The Refunded We Well Check Your Order Soon. Refund Id {refund_model.refund_id}.",
                        form.cleaned_data["email"],
                    )

                    messages.success(request, f"Refund Requested Successfully!")
                    return redirect("order-detail", order_number=order_number)

                else:
                    messages.error(request, form.errors.as_text())

            return render(
                request, "orders/refund.html", {"order": order, "form": forms}
            )
        else:
            return redirect("order-detail", order_number=order_number)
    except Order.DoesNotExist:
        return redirect("order-detail", order_number=order_number)


@login_required(login_url="account_login")
def success(request, order_number):
    try:
        order = Order.objects.get(order_number=order_number)
        return render(request, "orders/success.html", {"order": order})
    except Order.DoesNotExist:
        return redirect("order-list")


@login_required(login_url="account_login")
def failed(request, order_number):
    try:
        order = Order.objects.get(order_number=order_number)
        return render(request, "orders/failed.html", {"order": order})
    except Order.DoesNotExist:
        return redirect("order-list")


@login_required(login_url="account_login")
def order_detail(request, order_number):
    order = (
        Order.objects.select_related("shipping_address")
        .prefetch_related("payment")
        .get(order_number=order_number)
    )
    order_items = OrderItem.objects.filter(
        order=order, user=request.user
    ).select_related("product", "color", "size")

    form = CheckoutForm()

    context = {
        "order": order,
        "form": form,
        "order_items": order_items,
    }
    return render(request, "orders/order-detail.html", context)


@login_required(login_url="account_login")
def order_list(request):
    orders = (
        Order.objects.filter(user=request.user)
        .select_related("shipping_address")
        .prefetch_related("refunds")
    )
    return render(request, "orders/order-list.html", {"orders": orders})


@login_required(login_url="account_login")
def uncomplete_orders(request, order_number):
    url = request.META.get("HTTP_REFERER")
    if request.method == "POST":
        try:
            order = Order.objects.get(
                order_number=order_number,
                status="Uncomplete",
                user=request.user,
            )
            payment_option = request.POST.get("payment_option")

            if "payment_option" not in request.POST:
                messages.warning(
                    request, "You Must To Select One Of Those Fields, Don't Mess"
                )
                return redirect(url)
            elif payment_option not in ["Stripe", "CashOnDelivery", "PayPal"]:
                messages.error(request, "Wrong Payment Option, Don't Mess")
                return redirect(url)
            else:
                return redirect(
                    "payment", payment_option=payment_option, order_number=order_number
                )
        except Order.DoesNotExist:
            messages.error(request, "Order Does Not Exist")
            return redirect("order-list")


@login_required(login_url="account_login")
def order_canceled(request, order_number):
    try:
        order = Order.objects.get(order_number=order_number)
        if request.method == "POST":
            order.status = "Canceled"
            order.save()
            messages.success(request, "Your Order Has Been Canceled")
            return redirect("order-list")
    except Order.DoesNotExist:
        messages.error(request, "Order Does Not Exist")
        return redirect("order-list")
    return render(request, "orders/order-canceled.html", {"order": order})
