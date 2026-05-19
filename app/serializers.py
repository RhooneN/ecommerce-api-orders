from rest_framework import serializers
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.SerializerMethodField()
    class Meta:
        model = OrderItem
        fields = ['id', 'product_id', 'quantity', 'price', 'subtotal']

    def get_subtotal(self, obj):
            return obj.subtotal
        
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()
    # ~ session_key =serializers.CharField()

    class Meta:
        model = Order
        fields = ["url", "user_id", "username", "notes", "status", "total", "items", "signature"]
        extra_kwargs = {"total": {"read_only": True}}
      

    def get_total(self, obj):
        return obj.total
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and not getattr(request.user, "is_admin", False) is True:
            self.fields.pop("user_id")
            self.fields.pop("username")
            self.fields.pop("notes")
            self.fields.pop("status")
            self.fields.pop("url")

class UOrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()
    class Meta:
        model = Order
        fields = ['id', 'status', 'created_at', 'items', 'total']
        extra_kwargs = {"total": {"read_only": True}}
        # ~ extra_kwargs = {"user_id": {"read_only": True}}
        extra_kwargs = {"id": {"read_only": True}}
        extra_kwargs = {"item": {"read_only": True}}
        extra_kwargs = {"total": {"read_only": True}}

    def get_total(self, obj):
        return obj.total
