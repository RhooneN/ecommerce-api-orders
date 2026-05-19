from django.db import models
import uuid
from django.db.models import Sum, F
from decimal import Decimal

class Order(models.Model):
    user_id = models.IntegerField()
    username = models.CharField(max_length=60)
    signature = models.UUIDField(
        default=uuid.uuid4,   
        editable=False,      
        unique=True          
    )
    total = models.DecimalField(max_digits=10, decimal_places=2)  # FROZEN total
    notes = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ('Pending', 'Pending'),
            ('Processing', 'Processing	'),
            ('Shipped', 'Shipped'),
            ('Confirmed', 'Confirmed'),
            ('Canceled', 'Canceled'),
        ],
        default='Pending',
    )

    def __str__(self):
        return f"Order {self.id} - {self.user_id}"
         
    def calculate_total(self):
        """Calculate total from order items"""
        if hasattr(self, 'items'):
            # Using Django's aggregation for efficiency
            result = self.items.aggregate(
                total=Sum(F('subtotal'))
            )
            return result['total'] or Decimal('0.00')
        return Decimal('0.00')
    
    def save(self, *args, **kwargs):
        # Only calculate total if the order exists AND items exist
        if self.pk:
            try:
                if not self.total or self.total == Decimal("0.00"):
                    total = self.calculate_total()
                    if total is not None:
                        self.total = total
            except Exception as e:
                import logging
                logging.warning(f"Skipping total calculation for Order {self.pk}: {e}")
        super().save(*args, **kwargs)

	
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_id = models.IntegerField()
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2) 
    

    def __str__(self):
        return f"{self.quantity} of {self.product_id} for Order {self.order.id}"
        
            
    def calculate_total(self):
        """Calculate total from order items"""
        
        # Using Django's aggregation for efficiency
        result = self.quantity * self.price
        return result or Decimal('0.00')
        
    
    def save(self, *args, **kwargs):
        """Auto-calculate total before saving if not set"""
        if not self.subtotal:
            self.subtotal = self.calculate_total()
        super().save(*args, **kwargs)
