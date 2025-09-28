from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework import status as http_status

from orders.models import Order
from orders.permissions import IsOwnerOrAdmin
from orders.serializers import (
    OrderCreateSerializer,
    OrderStatusUpdateSerializer,
    OrderSerializer,
)


class OrderViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
):
    queryset = Order.objects.prefetch_related("items__product", "items").select_related(
        "user"
    )
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "orders"

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        if self.action == "partial_update" and self.request.path.endswith("/status/"):
            return OrderStatusUpdateSerializer
        return OrderSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_staff:
            return qs
        return qs.filter(user=user)

    def perform_create(self, serializer):
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        if not request.path.endswith("/status/"):
            return super().partial_update(request, *args, **kwargs)

        if not request.user.is_staff:
            raise PermissionDenied("Only admin can update order status")
        return super().partial_update(request, *args, **kwargs)

    @action(
        detail=True,
        methods=["patch"],
        url_path="status",
        permission_classes=[IsAdminUser],
    )
    def set_status(self, request, pk=None):
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(OrderSerializer(order).data, status=http_status.HTTP_200_OK)
