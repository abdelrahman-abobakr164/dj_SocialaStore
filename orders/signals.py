from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import OrderItem


@receiver(user_logged_in)
def add_id_after_login(sender, request, user, **kwargs):
    if "orderitem_id" in request.session:
        order_id = request.session.get("orderitem_id")
        orderitem = OrderItem.objects.get(id=order_id)
        orderitem.user = user
        orderitem.save()
