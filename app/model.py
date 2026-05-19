from django.db import models
# ~ from django.contrib.auth.models import User
# ~ from service.models import Product

class Order(models.Model):
	# ~ user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_id = models.IntegerField()
    username = models.CharField(max_length=60)
    transaction_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ('Pending', 'Pending'),
            ('Processing', 'Processing'),
            ('Shipped', 'Shipped'),
            ('Delivered', 'Delivered'),
            ('Canceled', 'Canceled'),
        ],
        default='Pending',
    )

    def __str__(self):
        return f"Order {self.id} - {self.user_id}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_id = models.IntegerField(default=1)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    

    def __str__(self):
        return f"{self.quantity} of {self.product} for Order {self.order.id}"

