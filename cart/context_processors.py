from orders.models import OrderItem
from wishlist.models import Wishlist
from cart.models import Cart, CartItem

import logging

logger = logging.getLogger(__name__)


def cart_handling(request):

    if "superuser" in request.path:
        return {}
    try:

        cleanup_orderitem_session(request)

        buy_now = (
            get_buy_now_item(request) if "orderitem_id" in request.session else None
        )
        cartitems = None if buy_now else get_cart_items(request)

        wishlist = get_wishlist(request)

        wish_count = sum(item.product.count() for item in wishlist)

        items = buy_now or cartitems or []

        cart_count = sum(item.quantity for item in items)
        total_price = sum(item.get_product_price() for item in items)

        coupon_discount = request.session.get("applied_coupon")
        total_price = (
            float(total_price) - float(coupon_discount["amount"])
            if "applied_coupon" in request.session
            else total_price
        )
        request.session["total_price"] = float(total_price)

        if not items:
            if not any(path in request.path for path in ("orders", "accounts")):
                request.session.pop("total_price", None)
                request.session.pop("applied_coupon", None)
        else:
            request.session["total_price"] = float(total_price)
            request.session.modified = True

        return {
            "wish_count": wish_count,
            "wishies": wishlist,
            "cart_count": cart_count,
            "total_price": total_price,
            "cartitems": cartitems,
            "buy_now": buy_now,
        }

    except Exception:
        logger.exception("cart_handling context processor failed")
        return {}


def cleanup_orderitem_session(request):
    if "orderitem_id" not in request.session:
        return

    if not any(path in request.path for path in ("orders", "accounts")):
        orderitem_id = request.session.pop("orderitem_id", None)
        if orderitem_id:
            OrderItem.objects.filter(id=orderitem_id).delete()


def get_buy_now_item(request):
    orderitem_id = request.session.get("orderitem_id")
    if not orderitem_id:
        return None

    return OrderItem.objects.filter(id=orderitem_id).select_related(
        "product", "size", "color"
    )


def get_cart_items(request):
    cart_obj, created = Cart.objects.get_or_new(request)
    return CartItem.objects.filter(cart=cart_obj).select_related(
        "product", "size", "color"
    )


def get_wishlist(request):
    Wishlist.objects.get_or_new(request, product=None)

    if request.user.is_authenticated:
        return Wishlist.objects.filter(user=request.user)

    list_id = request.session.get("list_id")
    return Wishlist.objects.filter(id=list_id) if list_id else Wishlist.objects.none()
