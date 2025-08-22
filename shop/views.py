from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Product, Category, Brand, Order, Customer,
    ProductVariant, OrderItem, ShippingAddress,
    Cart, CartItem, Wishlist
)
from .serializers import (
    ProductSerializer, CategorySerializer, BrandSerializer, OrderSerializer,
    CustomerSerializer, ProductVariantSerializer, OrderItemSerializer,
    ShippingAddressSerializer, CartSerializer, CartItemSerializer,
    WishlistSerializer, CustomerLoginSerializer
)


# --------------------------
# Utility functions
# --------------------------

def get_customer_for_user(user):
    """
    Return the Customer instance related to the authenticated user.
    Handles both cases:
      - request.user is already a Customer (if Customer is AUTH_USER_MODEL)
      - request.user is a normal User and Customer has FK/OneToOne to User
    """
    if user is None:
        return None

    # If request.user is already a Customer instance
    if isinstance(user, Customer):
        return user

    # Otherwise try to get or create a Customer linked to the user
    customer, _ = Customer.objects.get_or_create(user=user)
    return customer


def _get_refresh_for_user(obj):
    """
    Helper to create a RefreshToken for either a User or a Customer object.
    Tries object directly, then tries object.user (if present).
    """
    try:
        return RefreshToken.for_user(obj)
    except Exception:
        if hasattr(obj, "user"):
            return RefreshToken.for_user(obj.user)
        raise


def compute_unit_price(product, variant):
    base = getattr(product, "get_price", lambda: product.price)()
    add = Decimal("0.00")
    if variant:
        add = getattr(variant, "additional_price", Decimal("0.00")) or Decimal("0.00")
    return (base + add).quantize(Decimal("0.01"))


# --------------------------
# Auth Endpoints (JWT)
# --------------------------

@api_view(["POST"])
def register_customer(request):
    serializer = CustomerSerializer(data=request.data)
    if serializer.is_valid():
        customer = serializer.save()
        try:
            refresh = _get_refresh_for_user(customer)
        except Exception:
            return Response({"error": "Unable to create token for user."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "message": "Customer registered successfully",
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "customer": CustomerSerializer(customer).data
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def login_customer(request):
    serializer = CustomerLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data.get("user")
        if not user:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = _get_refresh_for_user(user)
        except Exception:
            return Response({"error": "Unable to create token for user."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        customer = get_customer_for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "customer": CustomerSerializer(customer).data
        })

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# --------------------------
# ViewSets (Public + Protected)
# --------------------------

class BaseModelViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]


class ProductViewSet(BaseModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filterset_fields = ["name", "category", "brand"]
    search_fields = ["name", "description"]

    def get_permissions(self):
        # public: list/retrieve. protected: create/update/delete
        return [AllowAny()] if self.action in ["list", "retrieve"] else [IsAuthenticated()]


class CategoryViewSet(BaseModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filterset_fields = ["name"]
    search_fields = ["name"]


class BrandViewSet(BaseModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    filterset_fields = ["name"]
    search_fields = ["name"]


class OrderViewSet(BaseModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filterset_fields = ["customer", "status"]
    search_fields = ["status"]


class CustomerViewSet(BaseModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filterset_fields = ["name", "email"]
    search_fields = ["name", "email"]


class ProductVariantViewSet(BaseModelViewSet):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer
    filterset_fields = ["product", "color", "size"]
    search_fields = ["color", "size"]


class OrderItemViewSet(BaseModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    filterset_fields = ["order", "product"]
    search_fields = ["product__name"]


class ShippingAddressViewSet(BaseModelViewSet):
    queryset = ShippingAddress.objects.all()
    serializer_class = ShippingAddressSerializer
    filterset_fields = ["customer", "city", "country"]
    search_fields = ["city", "country"]


class CartViewSet(BaseModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    filterset_fields = ["customer"]
    search_fields = ["customer__name"]


class CartItemViewSet(BaseModelViewSet):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    filterset_fields = ["cart", "product"]
    search_fields = ["product__name"]


class WishlistViewSet(BaseModelViewSet):
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer
    filterset_fields = ["customer", "product"]
    search_fields = ["product__name"]


# --------------------------
# Cart Endpoints (Protected)
# --------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    """
    Payload: { "product_id": 1, "variant_id": 2 (optional), "quantity": 2 }
    """
    customer = get_customer_for_user(request.user)
    if not customer:
        return Response({"error": "Customer not found"}, status=status.HTTP_400_BAD_REQUEST)

    product_id = request.data.get("product_id")
    if not product_id:
        return Response({"error": "product_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        quantity = int(request.data.get("quantity", 1))
    except (ValueError, TypeError):
        return Response({"error": "quantity must be an integer"}, status=status.HTTP_400_BAD_REQUEST)

    product = get_object_or_404(Product, id=product_id)

    variant_id = request.data.get("variant_id")
    variant = None
    if variant_id:
        variant = get_object_or_404(ProductVariant, id=variant_id, product=product)

    cart, _ = Cart.objects.get_or_create(customer=customer)
    unit_price = compute_unit_price(product, variant)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        variant=variant,
        defaults={"quantity": quantity, "unit_price": unit_price}
    )

    if not created:
        cart_item.quantity += quantity
        cart_item.unit_price = unit_price
        cart_item.save()

    serializer = CartSerializer(cart, context={"request": request})
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def view_cart(request):
    customer = get_customer_for_user(request.user)
    if not customer:
        return Response({"items": [], "total": "0.00"})
    cart = Cart.objects.filter(customer=customer).first()
    if not cart:
        return Response({"items": [], "total": "0.00"})
    serializer = CartSerializer(cart, context={"request": request})
    return Response(serializer.data)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_cart_item(request, item_id):
    customer = get_customer_for_user(request.user)
    cart_item = get_object_or_404(CartItem, id=item_id, cart__customer=customer)
    try:
        quantity = int(request.data.get("quantity", cart_item.quantity))
    except (ValueError, TypeError):
        return Response({"error": "quantity must be an integer"}, status=status.HTTP_400_BAD_REQUEST)

    if quantity <= 0:
        cart_item.delete()
        return Response({"message": "Item removed"}, status=status.HTTP_200_OK)

    cart_item.quantity = quantity
    cart_item.save()
    serializer = CartSerializer(cart_item.cart, context={"request": request})
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def remove_from_cart(request, item_id):
    customer = get_customer_for_user(request.user)
    cart_item = get_object_or_404(CartItem, id=item_id, cart__customer=customer)
    cart = cart_item.cart
    cart_item.delete()
    serializer = CartSerializer(cart, context={"request": request})
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def clear_cart(request):
    customer = get_customer_for_user(request.user)
    cart = Cart.objects.filter(customer=customer).first()
    if cart:
        cart.items.all().delete()
    return Response({"message": "Cart cleared"}, status=status.HTTP_200_OK)


# --------------------------
# Checkout Endpoint (Protected)
# --------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def checkout(request):
    customer = get_customer_for_user(request.user)
    if not customer:
        return Response({"error": "Customer not found"}, status=status.HTTP_400_BAD_REQUEST)

    cart = Cart.objects.filter(customer=customer).first()
    if not cart or not cart.items.exists():
        return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        total = sum((it.unit_price * it.quantity) for it in cart.items.select_related("product", "variant").all())

        order = Order.objects.create(
            customer=customer,
            total_amount=total,
            payment_status="unpaid",
            order_status="pending"
        )

        for it in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=it.product,
                quantity=it.quantity,
                price=it.unit_price
            )

        shipping = request.data.get("shipping")
        if shipping:
            ShippingAddress.objects.create(
                customer=customer,
                order=order,
                address=shipping.get("address", ""),
                city=shipping.get("city", ""),
                zip_code=shipping.get("zip_code", ""),
                country=shipping.get("country", "")
            )

        cart.items.all().delete()

    return Response({"message": "Order created", "order_id": order.id}, status=status.HTTP_201_CREATED)

