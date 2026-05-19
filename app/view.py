from rest_framework import generics, status
from rest_framework.viewsets import ViewSet
from shared.simple_permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly, IsAdmin
from rest_framework.response import Response
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer, UOrderSerializer
# ~ from shopping_cart.models import Cart, CartItem
# ~ from shopping_cart.serializers import CartSerializer
from rest_framework.decorators import action

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from .models import Order

class OrderStatusUpdateView(APIView):
    permission_classes = [AllowAny]  # Allow payment service to update
    
    def patch(self, request, order_number):
        """Update order status - called by payment service"""
        try:
            # Get the order
            order = get_object_or_404(Order, order_number=order_number)
            
            # Get new status from request
            new_status = request.data.get('status')
            notes = request.data.get('notes', '')
            
            # Validate status
            valid_statuses = [choice[0] for choice in Order.ORDER_STATUS_CHOICES]
            if new_status not in valid_statuses:
                return Response(
                    {"error": f"Invalid status. Valid options: {valid_statuses}"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update order
            old_status = order.status
            order.status = new_status
            if notes:
                order.notes = f"{order.notes}\n{notes}" if order.notes else notes
            order.save()
            
            return Response({
                'success': True,
                'message': f'Order status updated from {old_status} to {new_status}',
                'order_number': str(order.order_number),
                'old_status': old_status,
                'new_status': new_status
            })
            
        except Exception as e:
            return Response(
                {"error": f"Failed to update order status: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import requests
from django.conf import settings
from .models import Order, OrderItem
from decimal import Decimal

class OrderListCreateView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = []

    def get_queryset(self):
        # ✅ FIXED: Use request.user correctly
        print(self.request.user)
        print(self.request)
        print(dir(self.request.user))
        print(dir(self.request))
        return Order.objects.filter(user_id=self.request.user.id)

    def create(self, request, *args, **kwargs):
        try:
            # ✅ FIXED: Get session key correctly
            session_key = request.session.session_key
            print(session_key)
            # ✅ FIXED: Proper API call to cart service
            cart_response = requests.get(
                f"{settings.CART_SERVICE_URL}/cart/",
                params={'session_key': session_key},
                headers={'Authorization': f'Bearer {settings.CART_SERVICE_TOKEN}'},
                timeout=5
            )
            
            if cart_response.status_code != 200:
                return Response(
                    {"error": "Could not fetch cart"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            cart_data = cart_response.json()
            
            if not cart_data.get('items'):
                return Response(
                    {"error": "Your cart is empty"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ✅ Create order
            order = Order.objects.create(
                user_id=request.user_id,  # ✅ FIXED: Pass user object, not ID
                total_amount=Decimal('0.00')
            )
            
            total_amount = Decimal('0.00')
            
            # ✅ Create order items
            for item in cart_data['items']:
                # ✅ Get current product price (important!)
                product_price = self._get_product_price(item['product_id'])
                
                order_item = OrderItem.objects.create(
                    order=order,
                    product_id=item['product_id'],
                    product_name=item.get('name', f'Product {item["product_id"]}'),
                    quantity=item['quantity'],
                    price=product_price,
                    subtotal=product_price * item['quantity']
                )
                
                total_amount += order_item.subtotal
            
            # ✅ Update order total
            order.total_amount = total_amount
            order.save()
            
            # ✅ Clear cart (optional)
            self._clear_cart(session_key)
            
            serializer = OrderSerializer(order)
            return Response(
                {"message": "Order placed successfully", "order": serializer.data},
                status=status.HTTP_201_CREATED
            )
            
        except requests.RequestException as e:
            return Response(
                {"error": "Cart service unavailable", "details": str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            return Response(
                {"error": "Failed to create order", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _get_product_price(self, product_id):
        """Get current product price from product service"""
        try:
            response = requests.get(
                f"{settings.PRODUCT_SERVICE_URL}/products/{product_id}/",
                timeout=3,
                headers={'Authorization': f'Bearer {settings.PRODUCT_SERVICE_TOKEN}'}
            )
            if response.status_code == 200:
                product_data = response.json()
                return Decimal(str(product_data.get('price', 0)))
        except:
            pass
        return Decimal('0.00')  # Fallback price

    def _clear_cart(self, session_key):
        """Clear the cart after order creation"""
        try:
            response = requests.delete(
                f"{settings.CART_SERVICE_URL}/cart/empty/",
                json={'session_key': session_key},
                headers={'Authorization': f'Bearer {settings.CART_SERVICE_TOKEN}'},
                timeout=3
            )
            return response.status_code == 200
        except:
            return False

class OrderRetrieveView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user_id=self.request.user_id, username=self.request.username)


class OrderDeleteView(generics.DestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user_id=self.request.user_id, username=self.request.username, statut="Pending")


class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user_id=self.request.user_id, username=self.request.username)


class OrderCancelView(generics.UpdateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        r = Order.objects.filter(user_id=self.request.user_id, status='Pending')
        print(r)
        print(self.request)
        return r
    
    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        print(instance)
        instance.status = 'Canceled'
        instance.save()
        return Response({"message": "Order cancelled successfully"}, status=status.HTTP_200_OK)


class AdminOrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]
    queryset = Order.objects.all()


class AdminOrderStatusUpdateView(generics.UpdateAPIView):
    serializer_class = UOrderSerializer
    permission_classes = [IsAdminUser]
    queryset = Order.objects.all()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        new_status = request.data.get("status")
        if new_status not in ["Pending", "Processing", "Shipped", "Delivered", "Canceled"]:
            return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)
        instance.status = new_status
        instance.save()
        return Response({"message": "Order status updated successfully"}, status=status.HTTP_200_OK)

