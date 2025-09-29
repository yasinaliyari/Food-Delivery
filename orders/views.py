from rest_framework import viewsets, mixins
from rest_framework.decorators import action
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
        return qs if user.is_staff else qs.filter(user=user)

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
        permission_classes=[IsAuthenticated],
    )
    def set_status(self, request, pk=None):
        order = self.get_object()
        if not (
            request.user.is_staff or getattr(request.user, "role", None) == "seller"
        ):
            return Response(
                {"detail": "Only admin or seller van change status"},
                status=http_status.HTTP_403_FORBIDDEN,
            )
        serializer = OrderStatusUpdateSerializer(
            order, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(OrderSerializer(order).data, status=http_status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["post"],
        url_path="cancel",
        permission_classes=[IsAuthenticated],
    )
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.user != request.user and not request.user.is_staff:
            return Response(
                {"detail": "You can only cancel your own order"},
                status=http_status.HTTP_403_FORBIDDEN,
            )
        if order.status != Order.STATUS_PENDING:
            return Response(
                {"detail": "Only pending orders can be canceled"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        order.status = Order.STATUS_CANCELED
        order.save(update_fields=["status"])
        return Response(OrderSerializer(order).data, status=http_status.HTTP_200_OK)
