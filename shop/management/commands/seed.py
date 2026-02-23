from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from faker import Faker
import random
from decimal import Decimal

from shop.models import Product, Order, OrderItem

fake = Faker()


class Command(BaseCommand):
    help = "Seed fake data (users, products, orders, items)"

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=5)
        parser.add_argument("--products", type=int, default=20)
        parser.add_argument("--orders", type=int, default=20)
        parser.add_argument("--max-items", type=int, default=4)

    def handle(self, *args, **options):
        User = get_user_model()

        users_n = options["users"]
        products_n = options["products"]
        orders_n = options["orders"]
        max_items = options["max_items"]

        # --- users
        users = []
        for i in range(users_n):
            username = f"user{i+1}"
            u, created = User.objects.get_or_create(username=username)
            if created:
                u.set_password("password123")
                u.save()
            users.append(u)

        # --- admin user (optional)
        admin, created = User.objects.get_or_create(username="admin")
        if created:
            admin.set_password("admin123")
            admin.is_staff = True
            admin.is_superuser = True
            admin.save()

        # --- products
        products = []
        for _ in range(products_n):
            p = Product.objects.create(
                name=fake.unique.word().title(),
                price=Decimal(str(round(random.uniform(5, 2000), 2))),
                is_active=True,
            )
            products.append(p)

        # --- orders + items
        statuses = ["draft", "submitted", "paid", "cancelled"]

        for _ in range(orders_n):
            user = random.choice(users)
            status = random.choice(statuses)

            order = Order.objects.create(
                user=user,
                status=status,
                created_at=timezone.now(),
            )

            items_count = random.randint(1, max_items)
            chosen_products = random.sample(products, k=min(items_count, len(products)))

            for prod in chosen_products:
                qty = random.randint(1, 5)
                OrderItem.objects.create(
                    order=order,
                    product=prod,
                    qty=qty,
                    unit_price=prod.price,
                )

        self.stdout.write(self.style.SUCCESS("✅ Seed completed"))
        self.stdout.write("Users: user1..userN (password: password123)")
        self.stdout.write("Admin: admin (password: admin123)")