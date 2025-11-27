from orders.models import OrderItem
from wishlist.models import Wishlist
from cart.models import *


def CartHandling(request):

    if "superuser" in request.path:
        return {}

    CartCount = 0
    WishCount = 0
    total_price = 0
    cartitems = None
    BuyNow = None

    cleanup_orderitem_session(request)

    if "orderitem_id" in request.session:
        BuyNow = get_buy_now_item(request)
    else:
        cartitems = get_cart_items(request)

    wishlist = get_wishlist(request)
    WishCount = sum(item.product.count() for item in wishlist)

    items_to_count = BuyNow or cartitems
    if items_to_count:
        CartCount = sum(item.quantity for item in items_to_count)
        total_price = sum(item.get_product_price() for item in items_to_count)

    request.session["total_price"] = float(total_price)

    if "applied_coupon" in request.session:
        coupon_discount = float(request.session["applied_coupon"])
        request.session["total_price"] = float(total_price) - coupon_discount

    if not cartitems and not BuyNow and CartCount == 0:
        request.session.pop("total_price", None)
        request.session.pop("applied_coupon", None)

    context = {
        "WishCount": WishCount,
        "wishies": wishlist,
        "CartCount": CartCount,
        "total_price": total_price,
        "cartitems": cartitems,
        "BuyNow": BuyNow,
    }
    return context


def cleanup_orderitem_session(request):
    if "orderitem_id" not in request.session:
        return

    excluded_paths = ("orders", "accounts")
    if not any(path in request.path for path in excluded_paths):
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
