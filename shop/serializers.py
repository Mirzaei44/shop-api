from rest_framework import serializers
from .models import Product, Order, OrderItem


class ProductSerializer(serializers.ModelSerializer):
    # Basic serializer for product listing and detail views
    class Meta:
        model = Product
        fields = ["id", "name", "price", "is_active", "created_at"]


class OrderItemCreateSerializer(serializers.Serializer):
    # Used specifically when adding a product to an order
    product_id = serializers.IntegerField()
    qty = serializers.IntegerField(min_value=1)

    def validate_product_id(self, value):
        # Ensure the product exists and is active before adding to order
        try:
            product = Product.objects.get(id=value, is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found or inactive.")
        return value


class OrderItemSerializer(serializers.ModelSerializer):
    # Nested product representation inside an order
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "qty", "unit_price"]


class OrderSerializer(serializers.ModelSerializer):
    # Orders include nested items (read-only)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "status", "created_at", "items"]