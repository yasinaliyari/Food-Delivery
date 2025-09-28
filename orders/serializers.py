from rest_framework import serializers
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
