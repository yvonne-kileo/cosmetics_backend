from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductViewSet, CategoryViewSet, BrandViewSet, OrderViewSet, CustomerViewSet,
    ProductVariantViewSet, OrderItemViewSet, ShippingAddressViewSet,
    CartViewSet, CartItemViewSet, WishlistViewSet,
    add_to_cart, view_cart, update_cart_item, remove_from_cart, clear_cart, checkout
)

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'brands', BrandViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'customers', CustomerViewSet)
router.register(r'variants', ProductVariantViewSet)
router.register(r'order-items', OrderItemViewSet)
router.register(r'shipping-addresses', ShippingAddressViewSet)
router.register(r'carts', CartViewSet)
router.register(r'cart-items', CartItemViewSet)
router.register(r'wishlists', WishlistViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('cart/add/', add_to_cart, name='cart-add'),
    path('cart/', view_cart, name='cart-view'),
    path('cart/item/<int:item_id>/', update_cart_item, name='cart-item-update'),
    path('cart/item/<int:item_id>/remove/', remove_from_cart, name='cart-item-remove'),
    path('cart/clear/', clear_cart, name='cart-clear'),
    path('cart/checkout/', checkout, name='cart-checkout'),
]
