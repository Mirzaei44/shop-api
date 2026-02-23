# Standard library import for precise decimal arithmetic (used for money calculations)
from decimal import Decimal

# Database transaction management (ensures atomic operations)
from django.db import transaction

# Database expression tools (used for efficient calculations inside DB)
from django.db.models import F, Sum, DecimalField, Value, Count
from django.db.models.functions import Coalesce

# Django REST Framework core tools
from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# Local app models and serializers
from .models import Product, Order, OrderItem
from .serializers import ProductSerializer, OrderSerializer

from django.shortcuts import get_object_or_404


# ---------------------------------------------------------
# Custom Permission
# ---------------------------------------------------------
# Allows read-only access for everyone,
# but restricts write operations to admin users only.
class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        # Allow safe methods (GET, HEAD, OPTIONS) for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        # Allow write operations only for admin users
        return request.user and request.user.is_staff


# ---------------------------------------------------------
# Serializer for Adding Items to an Order
# ---------------------------------------------------------
# Validates input data when adding a product to an order
class AddItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    qty = serializers.IntegerField(min_value=1, default=1)


# ---------------------------------------------------------
# Product ViewSet
# ---------------------------------------------------------
# Full CRUD operations for products
# Admins can create/update/delete
# Regular users can only read
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by("-id")
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]

    # Filtering support
    filterset_fields = ["is_active"]        # Example: ?is_active=true

    # Search support
    search_fields = ["name"]                # Example: ?search=laptop

    # Ordering support
    ordering_fields = ["id", "price", "created_at"]  # Example: ?ordering=price


# ---------------------------------------------------------
# Order ViewSet
# ---------------------------------------------------------
# Handles user-specific orders
# Only authenticated users can access
class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    # Users can only see their own orders
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by("-id")

    # Automatically attach logged-in user when creating an order
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


    # ---------------------------------------------------------
    # Add Item to Order
    # ---------------------------------------------------------
    @action(detail=True, methods=["post"])
    def items(self, request, pk=None):
        order = self.get_object()

        # Business rule: items can only be added to draft orders
        if order.status != "draft":
            return Response(
                {"detail": "You can only add items to a draft order."},
                status=status.HTTP_409_CONFLICT,
            )

        # Validate input
        input_ser = AddItemSerializer(data=request.data)
        input_ser.is_valid(raise_exception=True)
        product_id = input_ser.validated_data["product_id"]
        qty = input_ser.validated_data["qty"]

        # Check if product exists and is active
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        # Atomic transaction ensures concurrency safety
        with transaction.atomic():
            # Lock row to prevent race conditions
            item, created = OrderItem.objects.select_for_update().get_or_create(
                order=order,
                product=product,
                defaults={"qty": 0, "unit_price": product.price},
            )

            # Increase quantity safely using F expression
            item.qty = F("qty") + qty
            item.save(update_fields=["qty"])
            item.refresh_from_db()

        return Response(
            {
                "detail": "Item added" if created else "Item merged",
                "item_id": item.id,
                "qty": item.qty,
            },
            status=status.HTTP_201_CREATED,
        )


    # ---------------------------------------------------------
    # Remove or Decrease Item Quantity
    # ---------------------------------------------------------
    @action(detail=True, methods=["post"])
    def remove_item(self, request, pk=None):
        order = self.get_object()

        if order.status != "draft":
            return Response(
                {"detail": "You can only edit items on a draft order."},
                status=status.HTTP_409_CONFLICT,
            )

        item_id = request.data.get("item_id")
        qty = int(request.data.get("qty", 1))

        if not item_id:
            return Response({"detail": "item_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        if qty <= 0:
            return Response({"detail": "qty must be > 0"}, status=status.HTTP_400_BAD_REQUEST)

        item = get_object_or_404(OrderItem, id=item_id, order=order)

        # If removing all quantity, delete item
        if item.qty <= qty:
            item.delete()
            return Response({"detail": "Item removed (deleted)"}, status=status.HTTP_200_OK)

        # Otherwise decrease quantity
        item.qty -= qty
        item.save(update_fields=["qty"])
        return Response({"detail": "Item updated", "item_id": item.id, "qty": item.qty})


    # ---------------------------------------------------------
    # Submit Order
    # ---------------------------------------------------------
    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        order = self.get_object()
        if order.status != "draft":
            return Response({"detail": "Only draft orders can be submitted."},
                            status=status.HTTP_409_CONFLICT)

        order.status = "submitted"
        order.save(update_fields=["status"])
        return Response({"detail": "Order submitted", "order_id": order.id})


    # ---------------------------------------------------------
    # Pay Order (Concurrency-safe version)
    # ---------------------------------------------------------
    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        # Lock order row to prevent simultaneous payment attempts
        with transaction.atomic():
            order = (
                Order.objects.select_for_update()
                .filter(id=pk, user=request.user)
                .first()
            )

            if not order:
                return Response({"detail": "Order not found"},
                                status=status.HTTP_404_NOT_FOUND)

            if order.status != "submitted":
                return Response(
                    {"detail": "Only submitted orders can be paid."},
                    status=status.HTTP_409_CONFLICT,
                )

            order.status = "paid"
            order.save(update_fields=["status"])

        return Response({"detail": "Order paid", "order_id": order.id})


    # ---------------------------------------------------------
    # Cancel Order
    # ---------------------------------------------------------
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()

        if order.status == "paid":
            return Response({"detail": "Paid orders cannot be cancelled."},
                            status=status.HTTP_409_CONFLICT)

        if order.status == "cancelled":
            return Response({"detail": "Order already cancelled."},
                            status=status.HTTP_409_CONFLICT)

        order.status = "cancelled"
        order.save(update_fields=["status"])
        return Response({"detail": "Order cancelled", "order_id": order.id})


    # ---------------------------------------------------------
    # Calculate Total Price
    # ---------------------------------------------------------
    @action(detail=True, methods=["get"])
    def total(self, request, pk=None):
        order = self.get_object()

        # Calculate line total (qty * unit_price)
        line_total = F("qty") * F("unit_price")

        total = order.items.aggregate(
            total=Coalesce(
                Sum(line_total, output_field=DecimalField(max_digits=12, decimal_places=2)),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )["total"]

        return Response({"order_id": order.id,
                         "status": order.status,
                         "total": str(total)})


    # ---------------------------------------------------------
    # Order Summary (Advanced Aggregation)
    # ---------------------------------------------------------
    @action(detail=True, methods=["get"])
    def summary(self, request, pk=None):
        order = self.get_object()

        line_total = F("qty") * F("unit_price")

        agg = order.items.aggregate(
            total=Coalesce(
                Sum(line_total, output_field=DecimalField(max_digits=12, decimal_places=2)),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
            total_qty=Coalesce(Sum("qty"), 0),
            items_count=Count("id"),
        )

        return Response({
            "order_id": order.id,
            "status": order.status,
            "items_count": agg["items_count"],
            "total_qty": agg["total_qty"],
            "total": str(agg["total"]),
            "created_at": order.created_at,
        })