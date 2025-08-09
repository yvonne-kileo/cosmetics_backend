from django.contrib import admin
from .models import (
    Category, Brand, Product, ProductVariant,
    Customer, Order, OrderItem, ShippingAddress,
    Cart, CartItem, Wishlist
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'brand', 'price')
    list_filter = ('category', 'brand')
    search_fields = ('name',)

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'variant_type', 'variant_value')
    list_filter = ('variant_type',)

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'address')
    search_fields = ('user__username', 'phone')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('customer', 'order_date', 'status')
    list_filter = ('status', 'order_date')
    search_fields = ('id', 'transaction_id', 'customer__name')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')
    list_filter = ('order',)


@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ('customer', 'order', 'address', 'city', 'zip_code')
    search_fields = ('address', 'city')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('customer', 'created_at')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity')


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('customer', 'product')

