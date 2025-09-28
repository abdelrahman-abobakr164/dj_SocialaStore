from orders.models import OrderItem
from wishlist.models import Wishlist
from cart.models import *


def CartHandling(request):

    if "superuser" in request.path:
        return {}
    else:
        CartCount = 0
        WishCount = 0
        total_price = 0

        if (
            "orders" not in request.path
            and "accounts" not in request.path
            and "orderitem_id" in request.session
        ):
            OrderItem.objects.filter(id=request.session.get("orderitem_id")).delete()
            del request.session["orderitem_id"]

        if "orderitem_id" in request.session:
            BuyNow = OrderItem.objects.filter(id=request.session.get("orderitem_id"))
            cartitems = None
        else:
            cart_obj, created = Cart.objects.get_or_new(request)
            cartitems = CartItem.objects.filter(cart=cart_obj)
            BuyNow = None

        list_obj, created = Wishlist.objects.get_or_new(request, product=None)

        if request.user.is_authenticated:
            wishlist = Wishlist.objects.filter(user=request.user)
        else:
            wishlist = Wishlist.objects.filter(id=request.session.get("list_id"))
        for item in wishlist:
            WishCount += item.product.count()

        if cartitems or BuyNow:
            for item in cartitems or BuyNow:
                CartCount += item.quantity
                total_price += item.get_product_price()

        request.session["total_price"] = float(total_price)

        if "applied_coupon" in request.session:
            request.session["total_price"] = float(total_price) - float(
                request.session["applied_coupon"]
            )

        if not cartitems and CartCount == 0 and not BuyNow:
            if "total_price" in request.session:
                del request.session["total_price"]
            if "applied_coupon" in request.session:
                del request.session["applied_coupon"]

        context = {
            "WishCount": WishCount,
            "wishies": wishlist,
            "CartCount": CartCount,
            "total_price": total_price,
            "cartitems": cartitems,
            "BuyNow": BuyNow,
        }
        return context
