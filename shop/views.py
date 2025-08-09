from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend

from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import (
    Product, Category, Brand, Order, Customer,
    ProductVariant, OrderItem, ShippingAddress,
    Cart, CartItem, Wishlist
)
from .serializers import (
    ProductSerializer, CategorySerializer, BrandSerializer, OrderSerializer,
    CustomerSerializer, ProductVariantSerializer, OrderItemSerializer,
    ShippingAddressSerializer, CartSerializer, CartItemSerializer,
    WishlistSerializer
)

# Product ViewSet
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['name', 'category', 'brand']
    search_fields = ['name', 'description']

# Category ViewSet
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['name']
    search_fields = ['name']

# Brand ViewSet
class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['name']
    search_fields = ['name']

# Order ViewSet
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['customer', 'status']
    search_fields = ['status']

# Customer ViewSet
class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['name', 'email']
    search_fields = ['name', 'email']

# Product Variant ViewSet
class ProductVariantViewSet(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['product', 'color', 'size']
    search_fields = ['color', 'size']

# Order Item ViewSet
class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['order', 'product']
    search_fields = ['product__name']

# Shipping Address ViewSet
class ShippingAddressViewSet(viewsets.ModelViewSet):
    queryset = ShippingAddress.objects.all()
    serializer_class = ShippingAddressSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['customer', 'city', 'country']
    search_fields = ['city', 'country']

# Cart ViewSet
class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['customer']
    search_fields = ['customer__name']

# Cart Item ViewSet
class CartItemViewSet(viewsets.ModelViewSet):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['cart', 'product']
    search_fields = ['product__name']

# Wishlist ViewSet
class WishlistViewSet(viewsets.ModelViewSet):
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['customer', 'product']
    search_fields = ['product__name']

def get_customer_for_user(user):
    # return or create the Customer instance tied to the Django user
    customer, _ = Customer.objects.get_or_create(user=user)
    return customer

def compute_unit_price(product, variant):
    # product.get_price() method returns discount_price or price (if you added it)
    base = product.get_price() if hasattr(product, 'get_price') else product.price
    add = Decimal('0.00')
    if variant:
        add = variant.additional_price or Decimal('0.00')
    return (base + add).quantize(Decimal('0.01'))

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    """
    Payload: { "product_id": 1, "variant_id": 2 (optional), "quantity": 2 }
    """
    customer = get_customer_for_user(request.user)
    product_id = request.data.get('product_id')
    variant_id = request.data.get('variant_id', None)
    quantity = int(request.data.get('quantity', 1))

    product = get_object_or_404(Product, id=product_id)
    variant = None
    if variant_id:
        variant = get_object_or_404(ProductVariant, id=variant_id, product=product)

    cart, _ = Cart.objects.get_or_create(customer=customer)

    unit_price = compute_unit_price(product, variant)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        variant=variant,
        defaults={'quantity': quantity, 'unit_price': unit_price}
    )

    if not created:
        cart_item.quantity = cart_item.quantity + quantity
        # update unit_price in case price changed since originally added
        cart_item.unit_price = unit_price
        cart_item.save()

    serializer = CartSerializer(cart, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_cart(request):
    customer = get_customer_for_user(request.user)
    try:
        cart = Cart.objects.get(customer=customer)
    except Cart.DoesNotExist:
        return Response({"items": [], "total": "0.00"})
    serializer = CartSerializer(cart, context={'request': request})
    return Response(serializer.data)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_cart_item(request, item_id):
    """
    Payload: { "quantity": 3 }
    """
    customer = get_customer_for_user(request.user)
    cart_item = get_object_or_404(CartItem, id=item_id, cart__customer=customer)
    quantity = int(request.data.get('quantity', cart_item.quantity))
    if quantity <= 0:
        cart_item.delete()
        return Response({"message": "Item removed"}, status=status.HTTP_200_OK)
    cart_item.quantity = quantity
    cart_item.save()
    cart = cart_item.cart
    serializer = CartSerializer(cart, context={'request': request})
    return Response(serializer.data)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_cart(request, item_id):
    customer = get_customer_for_user(request.user)
    try:
        cart_item = CartItem.objects.get(id=item_id, cart__customer=customer)
    except CartItem.DoesNotExist:
        return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
    cart = cart_item.cart
    cart_item.delete()
    serializer = CartSerializer(cart, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clear_cart(request):
    customer = get_customer_for_user(request.user)
    try:
        cart = Cart.objects.get(customer=customer)
        cart.items.all().delete()
    except Cart.DoesNotExist:
        pass
    return Response({"message": "Cart cleared"}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkout(request):
    """
    Convert cart to order.
    Payload example:
    {
      "shipping": {
        "address":"123 Example St",
        "city":"Nairobi",
        "zip_code":"00100",
        "country":"Kenya"
      },
      "payment": { ... }  # optional: integrate with payment gateway later
    }
    """
    customer = get_customer_for_user(request.user)
    try:
        cart = Cart.objects.get(customer=customer)
    except Cart.DoesNotExist:
        return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

    items = cart.items.select_related('product', 'variant').all()
    if not items:
        return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

    # create order atomically
    with transaction.atomic():
        # compute total
        total = sum((it.unit_price * it.quantity) for it in items)

        order = Order.objects.create(
            customer=customer,
            total_amount=total,
            payment_status='unpaid',  # or 'pending' depending on flow
            order_status='pending'
        )

        # create OrderItem rows
        for it in items:
            OrderItem.objects.create(
                order=order,
                product=it.product,
                quantity=it.quantity,
                price=it.unit_price
            )

        # create shipping address if provided
        ship = request.data.get('shipping')
        if ship:
            ShippingAddress.objects.create(
                customer=customer,
                order=order,
                address=ship.get('address', ''),
                city=ship.get('city', ''),
                zip_code=ship.get('zip_code', ''),
                country=ship.get('country', '')
            )

        # clear cart
        cart.items.all().delete()

    # return basic order info (you may want an order serializer)
    return Response({"message": "Order created", "order_id": order.id}, status=status.HTTP_201_CREATED)
