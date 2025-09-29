from rest_framework import serializers
from orders.models import Order
from reviews.models import Review


class ReviewSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Review._meta.get_field("product").remote_field.model.objects.all(),
        source="product",
        write_only=True,
    )
    user = serializers.StringRelatedField(read_only=True)
    product = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "user",
            "product",
            "product_id",
            "rating",
            "comment",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "product", "created_at", "updated_at"]

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user
        product = attrs.get("product") or getattr(self.instance, "product", None)

        if request.method == "POST":
            delivered = Order.objects.filter(
                user=user, status=Order.STATUS_DELIVERED, items__product=product
            ).exists()
            if not delivered and not user.is_staff:
                raise serializers.ValidationError(
                    "You can review a product only after it is delivered"
                )
        return attrs

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
