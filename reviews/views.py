from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.throttling import ScopedRateThrottle
from reviews.models import Review
from reviews.permissions import IsOwnerOrAdminWithTimeWindow
from reviews.serializers import ReviewSerializer


class ReviewViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    queryset = Review.objects.select_related("user", "product").all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrAdminWithTimeWindow]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "reviews"

    def get_queryset(self):
        qs = super().get_queryset()
        product = self.request.query_params.get("product")
        user = self.request.query_params.get("user")
        if product:
            qs = qs.filter(product=product)
        if user:
            qs = qs.filter(user_id=user)
        return qs
