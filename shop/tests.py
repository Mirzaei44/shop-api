from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

from .models import Product


User = get_user_model()


class ShopAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin", password="pass", is_staff=True)
        self.user1 = User.objects.create_user(username="u1", password="pass")
        self.user2 = User.objects.create_user(username="u2", password="pass")

        self.admin_token = Token.objects.create(user=self.admin)
        self.user1_token = Token.objects.create(user=self.user1)
        self.user2_token = Token.objects.create(user=self.user2)

        self.p1 = Product.objects.create(name="Laptop", price="1200.00", is_active=True)

    def auth(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def clear_auth(self):
        self.client.credentials()

    # 1) محصولات GET آزاد (ReadOnly)
    def test_products_get_is_public(self):
        self.clear_auth()
        r = self.client.get("/api/products/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    # 2) ساخت محصول فقط برای admin
    def test_products_post_requires_admin(self):
        # بدون توکن => 401 یا 403 (بسته به تنظیمات)
        self.clear_auth()
        r = self.client.post("/api/products/", {"name": "X", "price": "10.00"}, format="json")
        self.assertIn(r.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

        # یوزر عادی => 403
        self.auth(self.user1_token)
        r = self.client.post("/api/products/", {"name": "Y", "price": "11.00"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

        # ادمین => 201
        self.auth(self.admin_token)
        r = self.client.post("/api/products/", {"name": "Z", "price": "12.00"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    # 3) هر یوزر فقط order های خودش رو می‌بینه
    def test_user_sees_only_own_orders(self):
        # user1 یک order
        self.auth(self.user1_token)
        o1 = self.client.post("/api/orders/", {}, format="json").data["id"]

        # user2 یک order
        self.auth(self.user2_token)
        o2 = self.client.post("/api/orders/", {}, format="json").data["id"]

        # user1 فقط o1 رو ببینه
        self.auth(self.user1_token)
        r = self.client.get("/api/orders/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        # چون pagination داریم، دیتا داخل results هست
        results = r.data.get("results", r.data)
        ids = [x["id"] for x in results]

        self.assertIn(o1, ids)
        self.assertNotIn(o2, ids)

    # 4) بعد از submit دیگه نتونی item اضافه کنی
    def test_cannot_add_items_after_submit(self):
        self.auth(self.user1_token)
        order_id = self.client.post("/api/orders/", {}, format="json").data["id"]

        r = self.client.post(
            f"/api/orders/{order_id}/items/",
            {"product_id": self.p1.id, "qty": 1},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        r = self.client.post(f"/api/orders/{order_id}/submit/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        r = self.client.post(
            f"/api/orders/{order_id}/items/",
            {"product_id": self.p1.id, "qty": 1},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_409_CONFLICT)

    # 5) summary endpoint کار کنه و total درست بده
    def test_summary_endpoint(self):
        self.auth(self.user1_token)
        order_id = self.client.post("/api/orders/", {}, format="json").data["id"]

        self.client.post(
            f"/api/orders/{order_id}/items/",
            {"product_id": self.p1.id, "qty": 3},
            format="json",
        )

        r = self.client.get(f"/api/orders/{order_id}/summary/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["order_id"], order_id)
        self.assertEqual(r.data["total_qty"], 3)
        # 3 * 1200 = 3600
        self.assertIn(str(r.data["total"]), ["3600", "3600.00"])