from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.text import slugify
from django.conf import settings
from django.utils.crypto import get_random_string
# ==========================
# CUSTOM USER
# ==========================
class User(AbstractUser):
    email = models.EmailField(max_length=191, unique=True)
    phone_number = models.CharField(max_length=15, blank=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.username


# ==========================
# USER PROFILE
# ==========================
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    building_name = models.CharField(max_length=40, blank=True)
    address_line_1 = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(upload_to='userprofile/', blank=True, null=True)
    city = models.CharField(max_length=20, blank=True)
    state = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.user.username


# ==========================
# CATEGORY
# ==========================
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=191, unique=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ==========================
# PRODUCT
# ==========================
class Product(models.Model):
    STOCK_CHOICES = (
        ('in_stock', 'In Stock'),
        ('out_of_stock', 'Out of Stock'),
    )

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=191, unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    brand = models.CharField(max_length=255, default="Kanthimantra")
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_status = models.CharField(max_length=20, choices=STOCK_CHOICES, default='in_stock')
    thumbnail = models.ImageField(upload_to='products/thumbnails/', blank=True, null=True)
    video = models.FileField(upload_to='products/videos/', blank=True, null=True)
    quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            count = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{count}"
                count += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# ==========================
# PRODUCT IMAGE
# ==========================
class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField(upload_to="products/")
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return self.product.name


# ==========================
# WISHLIST
# ==========================
class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'product')


# ==========================
# ADDRESS
# ==========================
class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=15)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return self.full_name


# ==========================
# OTP
# ==========================
class OTP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(minutes=5)


# ==========================
# CART
# ==========================
class Cart(models.Model):
    user = models.OneToOneField(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name="cart"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart - {self.user}"


class CartItem(models.Model):
    cart = models.ForeignKey( Cart,related_name="items",on_delete=models.CASCADE)

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def sub_total(self):
        return self.product.price * self.quantity
    def __str__(self):
        return f"{self.product.name} ({self.quantity})"

# ==========================
# ORDER
# ==========================
# class Order(models.Model):
#     STATUS = (
#         ('pending', 'Pending'),
#         ('paid', 'Paid'),
#         ('shipped', 'Shipped'),
#         ('delivered', 'Delivered'),
#         ('cancelled', 'Cancelled'),
#     )

#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     address = models.ForeignKey(
#         Address,
#         on_delete=models.PROTECT,
#         null=True,
#         blank=True
#     )
#     payment_id = models.CharField(max_length=100, blank=True, null=True)
#     payment_method = models.CharField(max_length=50, blank=True, null=True)
#     invoice_number = models.CharField(max_length=50, unique=True, blank=True, null=True)

#     status = models.CharField(max_length=20, choices=STATUS, default='pending')
#     total_amount = models.DecimalField(max_digits=10, decimal_places=2)
#     created_at = models.DateTimeField(default=timezone.now)

#     def __str__(self):
#         return f"Order #{self.id}"


class Order(models.Model):
    STATUS = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address = models.ForeignKey(
        'Address',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    invoice_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)

    ordered_at = models.DateTimeField(default=timezone.now) 

    class Meta:
        ordering = ['-created_at']  # latest orders first

    def __str__(self):
        return f"Order #{self.id} - {self.invoice_number or 'No Invoice'}"

    def save(self, *args, **kwargs):
        # Auto-generate invoice number if not set
        if not self.invoice_number:
            random_str = get_random_string(6).upper()
            self.invoice_number = f"INV{self.id or random_str}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    def subtotal(self):
        return self.price * self.quantity