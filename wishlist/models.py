from django.db import models
from django.conf import settings
from core.models import Product


class WishManager(models.Manager):
    def get_or_new(self, request, product=None):
        list_id = request.session.get("list_id")
        list_obj = None
        created = False

        if request.user.is_authenticated:
            user_list = self.get_queryset().filter(user=request.user).first()
            if list_id:
                try:
                    session_list = self.get_queryset().get(id=list_id)
                    if user_list and session_list.id != user_list.id:
                        session_list_loop = self.get_queryset().filter(id=list_id)
                        for wish in session_list_loop:
                            for item in wish.product.all():
                                exist_list = self.get_queryset().filter(
                                    user=request.user, product__id=item.id
                                )
                                if not exist_list.exists():
                                    user_list.product.add(item)
                                    user_list.save()

                        if session_list.user is None:
                            session_list.delete()

                        list_obj = user_list

                    elif not user_list:
                        session_list.user = request.user
                        session_list.product.add(product)
                        session_list.save()
                        list_obj = session_list

                    else:
                        user_list.product.add(product)
                        user_list.save()
                        list_obj = user_list

                except self.model.DoesNotExist:
                    if user_list:
                        user_list.product.add(product)
                        user_list.save()
                        list_obj = user_list
                    else:
                        create_obj = self.model.objects.create(user=request.user)
                        if product:
                            list_obj.product.add(product)
                        list_obj = create_obj
                        created = True
            else:
                if user_list:
                    user_list.product.add(product)
                    user_list.save()
                    list_obj = user_list
                else:
                    create_obj = self.model.objects.create(user=request.user)
                    if product:
                        create_obj.product.add(product)
                    list_obj = create_obj
                    created = True
            request.session["list_id"] = list_obj.id

        else:
            if list_id:
                try:
                    list_obj = self.get_queryset().get(id=list_id)
                    list_obj.product.add(product)
                    list_obj.save()
                except self.model.DoesNotExist:
                    list_obj = self.model.objects.create(id=list_id)
                    list_obj.product.add(product)
                    created = True
                    request.session["list_id"] = list_obj.id
            else:
                list_obj = self.model.objects.create(id=list_id)
                list_obj.product.add(product)
                created = True
                request.session["list_id"] = list_obj.id

        return list_obj, created


class Wishlist(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_index=True,
    )
    product = models.ManyToManyField(Product, related_name="pwish", blank=True)

    objects = WishManager()

    def __str__(self):
        return f"{self.id} - {self.user}"
