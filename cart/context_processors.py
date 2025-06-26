from wishlist.models import Wishlist
from cart.models import *


def CartHandling(request):

    if "admin" in request.path:
        return {}
    else:
        CartCount = 0
        total_price = 0

        cart_obj, created = Cart.objects.get_or_new(request)
        cartitems = CartItem.objects.filter(cart=cart_obj)

        WishCount = (
            Wishlist.objects.filter(user=request.user).count()
            if request.user.is_authenticated
            else 0
        )

        if not cartitems.exists():
            if "total_price" in request.session:
                del request.session["total_price"]
            if "applied_coupon" in request.session:
                del request.session["applied_coupon"]

        for item in cartitems:
            CartCount += item.quantity
            total_price += item.get_product_price()

        request.session["total_price"] = float(total_price)

        if "applied_coupon" in request.session:
            request.session["total_price"] = float(total_price) - float(
                request.session["applied_coupon"]
            )

        context = {
            "WishCount": WishCount,
            "CartCount": CartCount,
            "total_price": total_price,
            "cartitems": cartitems,
        }
        return context
