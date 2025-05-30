from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

CATEGORY_CHOICES = [
    ('Fashion & Apparel', 'Fashion & Apparel'),
    ('Electronics', 'Electronics'),
    ('Home & Living', 'Home & Living'),
    ('Food & Beverages', 'Food & Beverages'),
    ('Beauty & Personal Care', 'Beauty & Personal Care'),
    ('Toys, Kids & Baby', 'Toys, Kids & Baby'),
    ('Tools & Hardware', 'Tools & Hardware'),
    ('Automotive', 'Automotive'),
    ('Sports & Outdoors', 'Sports & Outdoors'),
    ('Gaming', 'Gaming'),
    ('Books & Stationery', 'Books & Stationery'),
]

class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES, default='Home & Living')
    stock = models.PositiveIntegerField()
    image = models.FileField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)

    payment_method = models.ForeignKey(
        'PaymentMethod',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='orders'
    )
    delivery_service = models.ForeignKey(
        'DeliveryService',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='orders'
    )
    delivery_address = models.CharField(max_length=255, blank=True, null=True)
    delivery_postal_code = models.CharField(max_length=20, blank=True, null=True)
    delivery_country = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Order {self.id} by {self.user}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')

    def __str__(self):
        # Assuming User model has email field, otherwise change accordingly
        return f"{self.user.email}'s cart"  


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def total_price(self):
        return self.product.price * self.quantity


class PaymentMethod(models.Model):
    PAYMENT_CHOICES = [
        ('paypal', 'PayPal'),
        ('cod', 'Cash on Delivery'),
        ('Square', 'Square'),
        

        # Add more payment options as needed
    ]

    name = models.CharField(max_length=50, choices=PAYMENT_CHOICES, unique=True)
    details = models.TextField(blank=True, null=True)

    def __str__(self):
        return dict(self.PAYMENT_CHOICES).get(self.name, self.name)


class DeliveryService(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    estimated_delivery_time = models.CharField(max_length=100)  # e.g. "3-5 days"
    address = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.name
