from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from cloudinary.models import CloudinaryField # Required for Render
from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache

# --- 1. Categories ---

class Category(models.Model):
    name = models.CharField(max_length=50) # Men, Women, Kids
    def __str__(self):
        return self.name

class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=50) # Top Wear, Bottom Wear

    def __str__(self):
        return f"{self.category.name} -> {self.name}"

class ProductType(models.Model):
    sub_category = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name='product_types')
    name = models.CharField(max_length=50) # Shirt, T-Shirt, Jeans

    def __str__(self):
        return f"{self.sub_category} -> {self.name}"

# --- 2. Product ---

class Product(models.Model):
    brand = models.CharField(max_length=100, default="Vilio") 
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    price = models.PositiveIntegerField(default=0)
    original_price = models.PositiveIntegerField(default=0, help_text="MRP")

    offer_enabled = models.BooleanField(
    default=False,
    verbose_name="Enable Auto Offer Timer"
)

    offer_started_at = models.DateTimeField(
    null=True,
    blank=True
)
    
    # Cloudinary for Render support
    image = CloudinaryField('image', folder='villi-shop/products/', null=True, blank=True)
    size_chart = CloudinaryField('image', folder='villi-shop/size_charts/', null=True, blank=True)
    
    rating = models.FloatField(default=0.0)
    reviews_count = models.IntegerField(default=0)
    
    fabric = models.CharField(max_length=100, blank=True, null=True, help_text="Example: 100% Cotton")
    fit = models.CharField(max_length=100, blank=True, null=True, help_text="Example: Slim Fit")
    care_instructions = models.TextField(blank=True, null=True, help_text="Wash care details")
    additional_info = models.TextField(blank=True, null=True, help_text="Product ki extra khasiyat")
    
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    sub_category = models.ForeignKey('SubCategory', on_delete=models.CASCADE)
    product_type = models.ForeignKey('ProductType', on_delete=models.SET_NULL, null=True, blank=True)
    
    has_variants = models.BooleanField(default=False, verbose_name="Does this product have Colors?")
    simple_stock = models.PositiveIntegerField(default=0, help_text="Only if NO color variants")
    simple_sizes = models.CharField(max_length=100, blank=True, help_text="S,M,L")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['is_active', 'sub_category']),
            models.Index(fields=['is_active', 'category']),
            models.Index(fields=['name', 'brand', 'is_active']),
        ]

    @property
    def has_discount(self):
        """Returns True if the product currently has a genuine active discount"""
        if not self.original_price or self.original_price <= 0:
            return False
        if self.offer_enabled and not self.offer_active:
            return False
        return self.original_price > self.current_price

    @property
    def discount_percentage(self):
        if self.has_discount and self.original_price > 0:
            return int(((self.original_price - self.current_price) / self.original_price) * 100)
        return 0

    @property
    def save_amount(self):
        """Calculates rupee savings between MRP and selling price"""
        if not self.has_discount:
            return 0
        return max(0, self.original_price - self.current_price)

    @property
    def offer_active(self):
        if (
           not self.offer_enabled
           or not self.offer_started_at
           or self.original_price <= self.price
        ):
           return False

        now = timezone.now()

        elapsed_seconds = (now - self.offer_started_at).total_seconds()

        cycle_seconds = 63 * 60   # 1 hour ON + 3 min OFF

        current_position = elapsed_seconds % cycle_seconds

        return current_position < 3600

    @property
    def current_offer_end_time(self): 
        if not self.offer_enabled or not self.offer_started_at:   
            return None

        now = timezone.now()

        elapsed_seconds = (now - self.offer_started_at).total_seconds()

        cycle_seconds = 63 * 60

        current_position = elapsed_seconds % cycle_seconds

        if current_position < 3600:
            remaining = 3600 - current_position
            return now + timedelta(seconds=remaining)

        return None
        
    @property
    def next_offer_change_time(self):
        """
        Offer chahe ON ho ya OFF, agla transition kab hoga — wo hamesha deta hai.
        Isse frontend hamesha next flip ka time jaanta hai, reload ki zaroorat nahi.
        """
        if not self.offer_enabled or not self.offer_started_at or self.original_price <= self.price:
            return None

        now = timezone.now()
        elapsed_seconds = (now - self.offer_started_at).total_seconds()
        cycle_seconds = 63 * 60
        on_seconds = 3600

        current_position = elapsed_seconds % cycle_seconds

        if current_position < on_seconds:
            remaining = on_seconds - current_position   # ON hai -> OFF hone tak
        else:
            remaining = cycle_seconds - current_position # OFF hai -> ON hone tak

        return now + timedelta(seconds=remaining)    
            

    @property
    def current_price(self):
        if self.offer_active:
            return self.price      # Offer mein: discounted price
        return self.original_price 

    @property
    def google_price(self):
        """Google Merchant ke liye hamesha consistent price"""
        return self.original_price  # Regular selling price

    @property
    def google_sale_price(self):
        """Offer active ho toh sale price, warna None"""
        if self.offer_active:
            return self.price
        return None

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.brand} - {self.name}"

class SimpleProductSizeStock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='simple_size_stocks')
    size_name = models.CharField(max_length=50) 
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - {self.size_name}"

# --- 3. Product Variants ---

class ProductColor(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='color_variants')
    color_name = models.CharField(max_length=50)
    # UPDATED TO CLOUDINARY
    color_image = CloudinaryField('image', folder='villi-shop/variants/')

    def __str__(self):
        return f"{self.product.name} - {self.color_name}"

class ColorSizeStock(models.Model):
    product_color = models.ForeignKey(ProductColor, on_delete=models.CASCADE, related_name='sizes')
    size_name = models.CharField(max_length=10) 
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product_color.color_name} - {self.size_name} (Stock: {self.stock})"

# --- 4. Extra Gallery Images ---

class ProductImage(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='images')
    # UPDATED TO CLOUDINARY
    image = CloudinaryField('image', folder='villi-shop/product_gallery/')

    def __str__(self):
        return f"Image for {self.product.name}"

    class Meta:
        verbose_name = "Product Gallery Image"
        verbose_name_plural = "Product Gallery Images"

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
    payment_method = models.CharField(max_length=20, default="COD") 
    payment_status = models.CharField(max_length=20, default="Pending") 
    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=300, null=True, blank=True)  # ← YE ADD KARO
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def can_cancel(self):
        if str(self.status).lower() == 'cancelled':
            return False
        if self.created_at:
            now = timezone.now()
            diff = now - self.created_at
            if diff.total_seconds() < 300:
                return True
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
        variant = ProductColor.objects.filter(product=self.product, color_name=self.color).first()
        if variant and variant.color_image:
            return variant.color_image.url
        if self.product.image:
            return self.product.image.url
        return "/static/images/no-image.png"

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50, default="") 
    last_name = models.CharField(max_length=50, default="")  
    mobile = models.CharField(max_length=15)
    address = models.TextField() 
    address_2 = models.CharField(max_length=255, blank=True, null=True) 
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)
    created_at  = models.DateTimeField(auto_now_add=True, null=True) 

    def __str__(self):
        return f"{self.first_name} {self.last_name}, {self.mobile}"

class Blog(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    author = models.CharField(max_length=100, default="Vilio Team") # Rebranded to Vilio
    content = models.TextField()
    # UPDATED TO CLOUDINARY
    image = CloudinaryField('image', folder='villi-shop/blog_images/')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


@receiver(post_save, sender=Product)
def clear_home_product_cache(sender, instance, **kwargs):
    cache.delete('home_display_products_v2')
    cache.delete('home_display_products_v3')
    cache.delete('home_banners')

# ===== LEAD CAPTURE MODEL =====
class Lead(models.Model):
    name        = models.CharField(max_length=100)
    email       = models.EmailField(blank=True, null=True)
    phone       = models.CharField(max_length=20, blank=True, null=True)
    message     = models.TextField(blank=True, null=True)
    source      = models.CharField(max_length=50, default='Contact Form')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'

    def __str__(self):
        return f"{self.name} — {self.email or self.phone or 'No contact'} ({self.created_at.strftime('%d %b %Y')})"

# ===== HERO BANNER MODEL =====
class Banner(models.Model):
    title = models.CharField(max_length=200, blank=True, null=True, help_text="e.g. URBAN LUXURY & OVERSIZED HOODIES")
    subtitle = models.CharField(max_length=300, blank=True, null=True, help_text="Short description or tagline")
    badge = models.CharField(max_length=100, blank=True, default="EXCLUSIVE DROP", help_text="e.g. NEW ARRIVAL, 40% OFF")
    button_text = models.CharField(max_length=50, default="SHOP COLLECTION")
    button_link = models.CharField(max_length=255, default="/category/men/")
    image = CloudinaryField('image', folder='villi-shop/banners/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="Lower numbers appear first")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-id']
        verbose_name = 'Hero Banner'
        verbose_name_plural = 'Hero Banners'

    def __str__(self):
        return self.title or f"Banner #{self.id}"

@receiver(post_save, sender=Banner)
def clear_banner_cache(sender, instance, **kwargs):
    cache.delete('home_banners')

# ===== CUSTOMER REVIEW & TESTIMONIAL MODEL =====
class CustomerReview(models.Model):
    name = models.CharField(max_length=120)
    city = models.CharField(max_length=120, default="India")
    product_name = models.CharField(max_length=200, blank=True, null=True, help_text="e.g. Linen-Blend Striped Shirt")
    rating = models.PositiveSmallIntegerField(default=5)
    review_title = models.CharField(max_length=250, blank=True, null=True)
    comment = models.TextField()
    is_verified = models.BooleanField(default=True, verbose_name="Verified Buyer")
    is_approved = models.BooleanField(default=True, verbose_name="Approved for display")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Customer Review'
        verbose_name_plural = 'Customer Reviews'

    def __str__(self):
        return f"{self.name} ({self.city}) - {self.rating}★"