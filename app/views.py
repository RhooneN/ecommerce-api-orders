from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from shared.simple_permissions import IsAuth,  IsAuthenticatedOrReadOnly, IsAdmin, IsAdminOrReadOnly
from rest_framework.response import Response
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer, UOrderSerializer

import requests
from django.conf import settings
from decimal import Decimal

from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.http import JsonResponse

import logging
logger = logging.getLogger(__name__)

def health(request):
    return JsonResponse({"status": "ok"})

class OrderStatusUpdateView(APIView):
    permission_classes = [IsAuth]
    serializer_class = OrderSerializer
    
    def patch(self, request, signature):
        """Update order status - called by payment service"""
        try:
            # Get the order
            order = get_object_or_404(Order, signature=signature)
            
            # Get new status from request
            new_status = request.Get.get('status')
            notes = request.GET.get('notes', '')
            # Validate status
            valid_statuses = [choice[0] for choice in Order._meta.get_field('status').choices]
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
                'signature': str(order.signature),
                'old_status': old_status,
                'new_status': new_status
            })
            
        except Exception as e:
            return Response(
                {"error": f"Failed to update order status: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OrderListCreateView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuth]
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.auth_header = self.request.headers.get("Authorization")
    
        
    def get_queryset(self):
        if getattr(self.request.user, "is_admin", False) is True:
            return Order.objects.all()
        return Order.objects.filter(user_id=self.request.user.user_id)

    def create(self, request, *args, **kwargs):
        print("auth header 22", self.auth_header)
        try:
             user_id=self.request.user.user_id
             username=self.request.user.username
             cart_response = requests.get(
                    f"{settings.CART_SERVICE_URL}/cart/",
                    headers={'Authorization':  f'{self.auth_header}'},
                    timeout=(2, 5)	
            )
            
             if cart_response.status_code != 200:
                    logger.error(f"Failed to fetch cart  because")
                    return Response(
                    {"error": "Could not fetch cart"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
             cart_data = cart_response.json()
            
             if not cart_data.get('items'):
                    print("cart data", cart_data)
                    return Response(
                    {"error": "Your cart is empty"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ✅ Create order
             total = Decimal('0.00')
             order = Order.objects.create(user_id=self.request.user.user_id, total=total)
          
                # ✅ Create order items
             if not order:
                    logger.error(f"Failed to create order  ")
                    return Response(
                     {"error": "order not loaded"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
             for item in cart_data['items']:
                    product_price = item["price"]
                
                    order_item = OrderItem.objects.create(
                    order=order,
                    product_id=item['product_id'],
                    quantity=item['quantity'],	
                    price=product_price
                )
             order.save()
             requests.get(
                f"{settings.CART_SERVICE_URL}/cart/empty/",
                headers={'Authorization': f'Bearer {self.auth_header}'},
                timeout=(2, 5)	
            )
            
             serializer = OrderSerializer(order, context={'request': request})
             
             return Response(
                {"message": "Order placed successfully", "order": serializer.data},
                status=status.HTTP_201_CREATED
            )
            
        except requests.RequestException as e:
            logger.error(f"Failed to create order  because{e}")
            return Response(
                {"error": "Cart service unavailable", "details": str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Failed to create order  because {str(e)}")
            return Response(
                {"error": "Failed to create order", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
   
class OrderDetailAdminView(generics.RetrieveUpdateDestroyAPIView):
    """Admin-only order management"""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer    
    permission_classes = [IsAdmin]  
        
class OrderDeleteView(generics.DestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuth]

    def get_queryset(self):
        return Order.objects.filter(user_id=self.request.user.user_id, username=self.request.user.username, statut="Pending")


class OrderCancelView(generics.UpdateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuth]

    def get_queryset(self):
        r = Order.objects.filter(user_id=self.request.user.user_id, status='Pending')
        return r
    
    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        print(instance)
        instance.status = 'Canceled'
        instance.save()
        return Response({"message": "Order canceled successfully"}, status=status.HTTP_200_OK)



from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import api_view

def cancel(self):
	pass
class OrderRetrieveView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve a single order using its UUID.
    Only the owner (or an admin) can access it.
    """
    serializer_class = UOrderSerializer
    permission_classes = [IsAuth]
    lookup_field = "signature"  # DRF will look for `uuid` in the URL

    def get_object(self):
        print("User in request:", self.request.user)
        print("Auth header:", self.request.headers.get('Authorization'))

        order_uuid = self.kwargs.get(self.lookup_field)
        if not order_uuid:
            raise ValidationError({"detail": "Missing UUID in request."})

        # Base query — user can only access their own order
        queryset = Order.objects.filter(user_id=self.request.user.user_id)

        # If user is admin, allow access to all orders
        if getattr(self.request.user, "is_staff", False):
            queryset = Order.objects.all()

        return get_object_or_404(queryset, signature=order_uuid)
        
    def perform_update(self, request, *args, **kwargs):
        instance = self.get_object()
        print(instance)
        instance.status = 'Canceled'
        instance.save()
        return Response({"message": "Order canceled successfully"}, status=status.HTTP_200_OK)
        
    # ~ def perform_destroy(
