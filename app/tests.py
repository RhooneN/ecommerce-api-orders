from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Order
from django.conf import settings
User = get_user_model()
from datetime import datetime, timedelta
import jwt

def make_token(user):
    # ~ print("wesss", dir(user))
    # ~ print("super", getattr(user, "is_staff", False))
    payload = {
        "user_id": user.id,
        "username": user.username,
        "is_admin": getattr(user, "is_staff", False),
        "exp": datetime.now() + timedelta(hours=1),
    }
    print("payload", payload)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    
class OrderAPITestCase(APITestCase):
    def authenticate(self, user):
        token = make_token(user)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')


    def setUp(self):
		
        # Create local test users
        self.user = User.objects.create_user(username="testuser", password="password123")
        self.admin = User.objects.create_superuser(username="admin", password="admin123")
        
        # Auth clients
        self.client.login(username="testuser", password="password123")
        self.admin_client = self.client_class()   # fresh client
        self.admin_client.login(username="admin", password="admin123")
        
        self.order = Order.objects.create(user_id=self.user.id, status="Pending", total=22)
        
    def test_create_order(self):
        """
        Create order without depending on Cart/Product service.
        Just use user_id and status.
        """
        self.authenticate(self.user)
        # ~ data = {"user_id": self.user.id, "status": "Shipped"}
        response = self.client.post("/orders/")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)

    def test_get_user_orders(self):
        """
        Ensure a user can only see their orders.
        """
        self.authenticate(self.user)
        order = self.order
        response = self.client.get("/orders/user/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], order.id)

    def test_cancel_order(self):
        """
        Cancel an existing order.
        """
        self.authenticate(self.user)
        order = self.order

        response = self.client.put(
            f"/orders/{order.id}/cancel/", {"status": "Canceled"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.refresh_from_db()
        self.assertEqual(order.status, "Canceled")

    def test_admin_can_see_all_orders(self):
        """
        Admin should see every order.
        """
        self.authenticate(self.admin)
        order = self.order
        print("order", order)
        

        response = self.admin_client.get("/admin/orders/")
        print("response", response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
    def test_admin_can_see_all_orders2(self):
        """
        Admin should see every order.
        """
        self.authenticate(self.admin)
        order = self.order
        print("order", order)
        

        response = self.admin_client.get("/orders/")
        print("response", response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_admin_can_update_order_status(self):
        """
        Admin updates an order status.
        """
        self.authenticate(self.admin)
        order = self.order

        response = self.admin_client.patch(
            f"/admin/orders/{order.id}", {"status": "Shipped"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.refresh_from_db()
        self.assertEqual(order.status, "Shipped")
        
    def test_admin_can_update_order_status2(self):
        """
        Admin updates an order status.
        """
        self.authenticate(self.admin)
        order = self.order

        response = self.admin_client.patch(
            f"/orders/{order.id}", {"status": "Shipped"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.refresh_from_db()
        self.assertEqual(order.status, "Shipped")
