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
        return OrderSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_staff:
            return qs
        return qs.filter(user=user)

    def perform_create(self, serializer):
        serializer.save()

    def create(self, request, *args, **kwargs):
        write_serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        write_serializer.is_valid(raise_exception=True)
        order = write_serializer.save()

        read_serializer = OrderSerializer(order, context={"request": request})
        headers = self.get_success_headers(read_serializer.data)
        return Response(
            read_serializer.data, status=http_status.HTTP_201_CREATED, headers=headers
        )

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
