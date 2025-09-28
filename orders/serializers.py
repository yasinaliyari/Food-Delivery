from django.db.transaction import atomic
from rest_framework import serializers
from orders.models import OrderItem, Order
from products.models import Product


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
    items = OrderItemWriteSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Order must contain at least on item")
        return value

    @atomic
    def create(self, validated_data):
        user = self.context["request"].user
        item_data = validated_data["items"]
        order = Order.objects.create(
            user=user, status=Order.STATUS_PENDING, total_price=0
        )
        total = 0

        for item in item_data:
            product = item["product"]
            qty = item["quantity"]

            product.refresh_from_db()

            if product.stock < qty:
                raise serializers.ValidationError(
                    f"Insufficient stock for '{product.name}'. Available: {product.stock}"
                )
            product.stock -= qty
            product.save(update_fields=["stock"])

            order_item = OrderItem.objects.create(
                order=order, product=product, quantity=qty, price=product.price
            )

            total += order_item.line_total

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
