from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import (
    Category, Brand, Product, ProductVariant,
    Customer, Order, OrderItem, ShippingAddress,
    Cart, CartItem, Wishlist
)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = '__all__'

class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True, source='productvariant_set')

    class Meta:
        model = Product
        fields = '__all__'

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'

class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    orderitem_set = OrderItemSerializer(many=True, read_only=True)
    shippingaddress_set = ShippingAddressSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = '__all__'

class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = '__all__'

class CartSerializer(serializers.ModelSerializer):
    cartitem_set = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = '__all__'

class WishlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = '__all__'
        
# Mini serializer for product
class ProductMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'image']  # Choose the most useful fields

# Product Variant Serializer
class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'name', 'price', 'stock']

# Cart Item Serializer
class CartItemSerializer(serializers.ModelSerializer):
    product = ProductMiniSerializer()
    variant = ProductVariantSerializer()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'variant', 'quantity']

# Cart Serializer
class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True)

    class Meta:
        model = Cart
        fields = ['id', 'items']

class CustomerLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        user = authenticate(email=email, password=password)

        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("Account is inactive.")

        data['user'] = user
        return data
  