from django.db import models
from django.contrib.auth.models import User

# CATEGORY MODEL
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

# BRAND MODEL
class Brand(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

# PRODUCT MODEL
class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    discount_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_price(self):
        return self.discount_price if self.discount_price else self.price

# PRODUCT VARIANTS MODEL (size, color, etc.)
class ProductVariant(models.Model):
    VARIANT_CHOICES = [
        ('Size', 'Size'),
        ('Color', 'Color'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    variant_type = models.CharField(max_length=50, choices=VARIANT_CHOICES)
    variant_value = models.CharField(max_length=50)
    additional_price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.product.name} - {self.variant_type}: {self.varaiant_value}"

# CUSTOMER MODEL
class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.user.username

# ORDER MODEL
class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    order_date = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=100, null=True)
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return str(self.id)

# ORDER ITEM MODEL
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)


    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

# SHIPPING ADDRESS MODEL
class ShippingAddress(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.address
class Cart(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart {self.id} - {self.customer.user.username}"

    def total(self):
        items = self.items.all()
        total = Decimal('0.00')
        for i in items:
            total += i.unit_price * i.quantity
        return total

    def items_count(self):
        return sum(i.quantity for i in self.items.all())


    

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey('ProductVariant', on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    # store the unit price at the time the item is added to cart (to avoid price drift)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    
class Wishlist(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.customer.user.username} ♥ {self.product.name}"


