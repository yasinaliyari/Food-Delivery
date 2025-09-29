from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers
from orders.models import OrderItem, Order
from products.models import Product

User = get_user_model()


class OrderItemWriteSerializer(serializers.Serializer):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.select_related("category", "seller").all(),
        source="product",
    )
    quantity = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        product = attrs["product"]
        qty = attrs["quantity"]
        if product.stock < qty:
            raise serializers.ValidationError(
                f"Insufficient stock for '{product.name}'.Available: {product.stock}"
            )
        return attrs


class OrderItemReadSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    category = serializers.CharField(source="product.category.name", read_only=True)
    seller = serializers.CharField(source="product.seller.username", read_only=True)
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_name",
            "category",
            "seller",
            "quantity",
            "price",
            "line_total",
        ]

    def get_line_total(self, obj):
        return obj.price * obj.quantity


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemReadSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "user", "status", "total_price", "created_at", "items"]
        read_only_fields = ["id", "user", "total_price", "created_at"]


class OrderCreateSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False, write_only=True
    )
    items = OrderItemWriteSerializer(many=True)

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user
        is_admin = bool(user.is_staff)

        if "user_id" in attrs and not is_admin:
            raise serializers.ValidationError("You are not allowed to set user_id")
        if not is_admin and getattr(user, "role", None) != "customer":
            raise serializers.ValidationError("Only customers can create orders")

        items = attrs.get("items", [])
        if not items:
            raise serializers.ValidationError("Order must contain at least one item")
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request_user = self.context["request"].user
        target_user = (
            validated_data.pop("user_id", None) if "user_id" in validated_data else None
        )
        order_user = target_user or request_user

        items_data = validated_data["items"]

        order = Order.objects.create(
            user=order_user, status=Order.STATUS_PENDING, total_price=0
        )
        total = 0

        for item in items_data:
            product = item["product"]
            qty = item["quantity"]

            product.refresh_from_db()

            if product.stock < qty:
                raise serializers.ValidationError(
                    f"Insufficient stock for '{product.name}'. Available: {product.stock}"
                )
            product.stock -= qty
            product.save(update_fields=["stock"])
            oi = OrderItem.objects.create(
                order=order, product=product, quantity=qty, price=product.price
            )
            total += oi.line_total

        order.total_price = total
        order.save(update_fields=["total_price"])
        return order


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["status"]

    def validate_status(self, value):
        if value not in dict(Order.STATUS_CHOICES):
            raise serializers.ValidationError("Invalid status")
        return value

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user
        new_status = attrs["status"]
        order = self.instance
        current = order.status

        allowed_admin = {
            Order.STATUS_PENDING: {Order.STATUS_PROCESSING, Order.STATUS_CANCELED},
            Order.STATUS_PROCESSING: {Order.STATUS_SHIPPED, Order.STATUS_CANCELED},
            Order.STATUS_SHIPPED: {Order.STATUS_DELIVERED},
            Order.STATUS_DELIVERED: set(),
            Order.STATUS_CANCELED: set(),
        }
        allowed_seller = {
            Order.STATUS_PENDING: {Order.STATUS_PROCESSING},
            Order.STATUS_PROCESSING: {Order.STATUS_SHIPPED},
            Order.STATUS_SHIPPED: set(),
            Order.STATUS_DELIVERED: set(),
            Order.STATUS_CANCELED: set(),
        }
        if user.is_staff:
            allowed = allowed_admin.get(current, set())
        elif getattr(user, "role", None) == "seller":
            allowed = allowed_seller.get(current, set())
        else:
            raise serializers.ValidationError(
                "You are not allowed to change order status"
            )

        if new_status not in allowed:
            raise serializers.ValidationError(
                f"Transition {current} => {new_status} is not allowed for your role"
            )
        return attrs
