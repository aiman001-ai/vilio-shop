from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify

# --- 1. Categories ---
from django.db import models
from django.utils import timezone
from datetime import timedelta

class Category(models.Model):
    name = models.CharField(max_length=50) # Men, Women, Kids
    def __str__(self):
        return self.name

class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=50) # जैसे: Top Wear, Bottom Wear

    def __str__(self):
        return f"{self.category.name} -> {self.name}"

class ProductType(models.Model):
    sub_category = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name='product_types')
    name = models.CharField(max_length=50) # जैसे: Shirt, T-Shirt, Jeans

    def __str__(self):
        return f"{self.sub_category} -> {self.name}"

class Product(models.Model):
    brand = models.CharField(max_length=100, default="Vilio") # Aapne Vilio rebrand kiya tha
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    price = models.PositiveIntegerField(default=0)
    original_price = models.PositiveIntegerField(default=0, help_text="MRP")
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    size_chart = models.ImageField(upload_to='size_charts/', null=True, blank=True)
    
    rating = models.FloatField(default=0.0)
    reviews_count = models.IntegerField(default=0)
    
    fabric = models.CharField(max_length=100, blank=True, null=True, help_text="Example: 100% Cotton")
    fit = models.CharField(max_length=100, blank=True, null=True, help_text="Example: Slim Fit")
    care_instructions = models.TextField(blank=True, null=True, help_text="Wash care details")
    additional_info = models.TextField(blank=True, null=True, help_text="Product ki extra khasiyat")
    
    # Hierarchy
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    sub_category = models.ForeignKey(SubCategory, on_delete=models.CASCADE)
    product_type = models.ForeignKey(ProductType, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Variants & Stock
    has_variants = models.BooleanField(default=False, verbose_name="Does this product have Colors?")
    simple_stock = models.PositiveIntegerField(default=0, help_text="Only if NO color variants")
    simple_sizes = models.CharField(max_length=100, blank=True, help_text="S,M,L")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    @property
    def discount_percentage(self):
        if self.original_price and self.original_price > self.price:
            return int(((self.original_price - self.price) / self.original_price) * 100)
        return 0

    # ==========================================
    # CLOUDINARY ERROR FIX (NAME ATTRIBUTE)
    # ==========================================
    def save(self, *args, **kwargs):
        # Jab hum admin se save karte hain, tab CloudinaryImage object 
        # kabhi kabhi 'name' property kho deta hai. Ye code usse bypass karega.
        try:
            for field_name in ['image', 'size_chart']:
                field = getattr(self, field_name)
                if field and hasattr(field, '_file') and field._file:
                    if not hasattr(field, 'name') or field.name is None:
                        field.name = field.file.name
        except Exception:
            pass
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.brand} - {self.name}"


class SimpleProductSizeStock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='simple_size_stocks')
    size_name = models.CharField(max_length=50) # जैसे: S, M, L, XL
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - {self.size_name}"


# --- 3. Product Variants (New Nested System) ---
class ProductColor(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='color_variants')
    color_name = models.CharField(max_length=50)
    color_image = models.ImageField(upload_to='variants/')

    def __str__(self):
        return f"{self.product.name} - {self.color_name}"

class ColorSizeStock(models.Model):
    product_color = models.ForeignKey(ProductColor, on_delete=models.CASCADE, related_name='sizes')
    size_name = models.CharField(max_length=10) # S, M, L, XL
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product_color.color_name} - {self.size_name} (Stock: {self.stock})"

# --- 4. Extra Gallery Images ---
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')

# --- 5. User, Cart & Order Models ---
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)
    otp = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    color = models.CharField(max_length=50, null=True, blank=True) 
    size = models.CharField(max_length=10, null=True, blank=True)   
    quantity = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.product.price * self.quantity

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.TextField()
    total_amount = models.IntegerField()
    status = models.CharField(max_length=20, default="Pending")
    
    # --- NAYE FIELDS JO ADD KIYE HAIN ---
    payment_method = models.CharField(max_length=20, default="COD") # COD ya ONLINE
    payment_status = models.CharField(max_length=20, default="Pending") # Pending, Paid, Failed
    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    # ------------------------------------

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def can_cancel(self):
        from django.utils import timezone
        
        # 1. Check if status is Cancelled (Case insensitive)
        if str(self.status).lower() == 'cancelled':
            return False

        # 2. Time calculation logic
        if self.created_at:
            now = timezone.now()
            diff = now - self.created_at
            # 300 seconds = 5 minutes
            if diff.total_seconds() < 300:
                return True
        
        # Ye wala return ab function ke andar hai (indentation check karein)
        return False

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    color = models.CharField(max_length=50, null=True, blank=True)
    size = models.CharField(max_length=10, null=True, blank=True)
    quantity = models.IntegerField()
    price = models.IntegerField()

    def get_variant_image(self):
        # Updated to use ProductColor instead of ProductVariant
        variant = ProductColor.objects.filter(product=self.product, color_name=self.color).first()
        if variant and variant.color_image:
            return variant.color_image.url
        if self.product.image:
            return self.product.image.url
        return "/static/images/no-image.png"

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50, default="") # Naya
    last_name = models.CharField(max_length=50, default="")  # Naya
    mobile = models.CharField(max_length=15)
    address = models.TextField() # Street Address
    address_2 = models.CharField(max_length=255, blank=True, null=True) # Naya (Apartment/Suite)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.first_name} {self.last_name}, {self.mobile}"


class Blog(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    author = models.CharField(max_length=100, default="Cheapify Team")
    content = models.TextField()
    image = models.ImageField(upload_to='blog_images/')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
