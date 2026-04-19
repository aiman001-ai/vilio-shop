import csv
import re  # Pincode dhoondne ke liye
from django.http import HttpResponse
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from cloudinary.forms import CloudinaryFileField  # <--- NAYA IMPORT
from django import forms
from .models import (
    Product, ProductImage, Category, SubCategory, ProductType,
    ProductColor, ColorSizeStock, SimpleProductSizeStock,
    Cart, CartItem, Order, OrderItem, Address, Profile
)

# --- Cloudinary Form for Product (Image upload ke liye) ---
class ProductAdminForm(forms.ModelForm):
    image = CloudinaryFileField(options={'folder': 'products'}, required=False)
    size_chart = CloudinaryFileField(options={'folder': 'size_charts'}, required=False)
    
    class Meta:
        model = Product
        fields = '__all__'

# --- Cloudinary Form for ProductColor ---
class ProductColorAdminForm(forms.ModelForm):
    color_image = CloudinaryFileField(options={'folder': 'variants'}, required=False)
    
    class Meta:
        model = ProductColor
        fields = '__all__'

# --- Cloudinary Form for ProductImage ---
class ProductImageForm(forms.ModelForm):
    image = CloudinaryFileField(options={'folder': 'products'}, required=False)
    
    class Meta:
        model = ProductImage
        fields = '__all__'

# --- 1. SubCategory Management ---
@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category') 
    list_filter = ('category',)
    search_fields = ('name',)

# --- 2. Product Type Management ---
@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'sub_category')
    list_filter = ('sub_category',)
    search_fields = ('name',)

# --- 3. Product Gallery Images Inline (Cloudinary ke saath) ---
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    form = ProductImageForm  # <--- Cloudinary form use karo
    extra = 1

# --- 4. Simple Product Size & Stock Inline ---
class SimpleProductSizeStockInline(admin.TabularInline):
    model = SimpleProductSizeStock
    extra = 1
    fields = ('size_name', 'stock')

# --- 5. Size aur Stock rows (ProductColor ke andar) ---
class ColorSizeStockInline(admin.TabularInline):
    model = ColorSizeStock
    extra = 1
    fields = ('size_name', 'stock')

# --- 6. Product page par Colors section (Cloudinary ke saath) ---
class ProductColorInline(admin.StackedInline):
    model = ProductColor
    form = ProductColorAdminForm  # <--- Cloudinary form use karo
    extra = 1
    fields = ('color_name', 'color_image', 'manage_sizes_link')
    readonly_fields = ('manage_sizes_link',)
    show_change_link = True 

    def manage_sizes_link(self, obj):
        if obj.id:
            url = reverse('admin:app1_productcolor_change', args=[obj.id])
            return format_html(
                '<a href="{}" target="_blank" style="'
                'background-color: #417690; '
                'color: white; '
                'padding: 8px 15px; '
                'border-radius: 5px; '
                'text-decoration: none; '
                'font-weight: bold; '
                'display: inline-block; '
                'margin-top: 5px;">'
                '⚙️ Manage Sizes & Stock for {}'
                '</a>', 
                url, obj.color_name
            )
        return "Save the product first to manage sizes"

    manage_sizes_link.short_description = 'Sizes Control'

# --- 7. Product Color Admin (Cloudinary ke saath) ---
@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    form = ProductColorAdminForm  # <--- Cloudinary form use karo
    list_display = ['color_name', 'product']
    inlines = [ColorSizeStockInline]

# --- 8. Main Product Admin (Cloudinary ke saath) ---
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm  # <--- Cloudinary form use karo
    list_display = ['name', 'brand', 'price', 'get_full_category', 'has_variants', 'is_active']
    list_filter = ['category', 'sub_category', 'product_type', 'brand', 'is_active', 'has_variants']
    search_fields = ['name', 'brand']
    
    inlines = [ProductImageInline, SimpleProductSizeStockInline, ProductColorInline]

    def get_full_category(self, obj):
        path = f"{obj.category.name}"
        if obj.sub_category:
            path += f" -> {obj.sub_category.name}"
        if obj.product_type:
            path += f" -> {obj.product_type.name}"
        return path
    get_full_category.short_description = 'Full Category Path'

    fieldsets = (
        ("Basic Information", {
            'fields': (
                'brand', 'name', 'description', 
                'price', 'original_price', 'image', 'size_chart',
                'category', 
                'sub_category', 
                'product_type', 
                'is_active'
            )
        }),
        ("Product Specifications (Admin Only)", {
            'description': "Yahan Product ki Fabric, Fit aur washing instructions bharein.",
            'fields': (
                'fabric', 'fit', 'care_instructions', 'additional_info'
            )
        }),
        ("Product Variant Control", {
            'description': "अगर इस प्रोडक्ट में कलर्स हैं, तो नीचे 'Product Colors' भरें। अगर कलर्स नहीं हैं, तो 'Does this product have Colors?' को अनटिक रखें और 'Simple Product Size Stocks' भरें।",
            'fields': ('has_variants',), 
        }),
    )

    class Media:
        js = ('admin/js/vendor/jquery/jquery.js', 'js/admin_custom.js',)

# --- 9. Orders & Cart Management ---
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'color', 'size', 'quantity', 'price')

def export_to_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="shiprocket_final_ready.csv"'
    writer = csv.writer(response)
    
    writer.writerow([
        'Order_ID', 'Product_ID', 'Customer_Name', 'Customer_Email', 'Customer_Phone',
        'Shipping_Address', 'Shipping_Address_2', 'Shipping_City', 
        'Shipping_Pincode', 'Shipping_State', 'Shipping_Country',
        'Order_Status', 'Total_Amount', 'Payment_Method', 'Created_At'
    ])
    
    for obj in queryset:
        user = obj.user
        addr_obj = obj.address
        address_text = str(addr_obj) if addr_obj else ""
        
        first_item = obj.items.first()
        product_id = first_item.product.id if first_item and first_item.product else "N/A"

        phone = getattr(addr_obj, 'mobile', '') or getattr(addr_obj, 'phone', '')
        if not phone:
            profile = Profile.objects.filter(user=user).first()
            phone = getattr(profile, 'phone', '') or getattr(profile, 'mobile', '')
        if not phone:
            match = re.search(r'\d{10,12}', address_text)
            phone = match.group(0) if match else ""
        
        formatted_phone = f"'{phone}" if phone else "'9999999999"

        pincode = getattr(addr_obj, 'pincode', '')
        if not pincode:
            match = re.search(r'\b\d{6}\b', address_text)
            pincode = match.group(0) if match else ""

        city = getattr(addr_obj, 'city', '')
        state = getattr(addr_obj, 'state', '')

        if not city or not state:
            parts = [p.strip() for p in address_text.split(',') if p.strip()]
            if len(parts) >= 2:
                if not city: city = parts[-2]
                if not state: state = re.sub(r'\d+', '', parts[-1]).strip()

        pay_method = str(obj.payment_method).upper()
        final_pay = "Prepaid" if any(x in pay_method for x in ["ONLINE", "RAZORPAY", "PREPAID"]) else "COD"

        writer.writerow([
            obj.id,
            product_id,
            user.get_full_name() or user.username,
            user.email or f"{user.username}@gmail.com",
            formatted_phone, 
            address_text,
            "", 
            city or "Update City",
            pincode or "000000",
            state or "Update State",
            "India",
            obj.status,
            obj.total_amount,
            final_pay,
            obj.created_at.strftime("%d-%m-%Y %H:%M")
        ])
    
    return response

export_to_csv.short_description = "Shiprocket Perfect Export"

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'status', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    inlines = [OrderItemInline]
    actions = [export_to_csv]

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'color', 'size', 'quantity')

# --- Models Registration ---
admin.site.register(Category)
admin.site.register(Cart)
admin.site.register(Address)
admin.site.register(Profile)