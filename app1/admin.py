import csv
import re  # Pincode dhoondne ke liye
from django.http import HttpResponse
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html  # <-- यह इम्पोर्ट करना ज़रूरी है
from .models import (
    Product, ProductImage, Category, SubCategory, ProductType,
    ProductColor, ColorSizeStock, SimpleProductSizeStock,
    Cart, CartItem, Order, OrderItem, Address, Profile
)

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

# --- 3. Product Gallery Images Inline ---
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

# --- 4. NEW: Simple Product Size & Stock Inline (एक ही रो में) ---
class SimpleProductSizeStockInline(admin.TabularInline):
    model = SimpleProductSizeStock
    extra = 1
    fields = ('size_name', 'stock') # ये दोनों को एक ही लाइन में लाएगा

# --- 5. Size aur Stock rows (ProductColor ke andar) ---
class ColorSizeStockInline(admin.TabularInline):
    model = ColorSizeStock
    extra = 1
    fields = ('size_name', 'stock')

# --- 6. Product page par Colors section ---
class ProductColorInline(admin.StackedInline):
    model = ProductColor
    extra = 1
    # 'manage_sizes_link' को fields में जोड़ें
    fields = ('color_name', 'color_image', 'manage_sizes_link')
    readonly_fields = ('manage_sizes_link',)
    show_change_link = True 

    def manage_sizes_link(self, obj):
        if obj.id:
            # यह URL उस पर्टिकुलर कलर के एडिट पेज पर ले जाएगा
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

# --- 7. Product Color Admin ---
@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ['color_name', 'product']
    inlines = [ColorSizeStockInline]

# --- 8. Main Product Admin ---
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'price', 'get_full_category', 'has_variants', 'is_active']
    list_filter = ['category', 'sub_category', 'product_type', 'brand', 'is_active', 'has_variants']
    search_fields = ['name', 'brand']
    
    # यहाँ SimpleProductSizeStockInline को भी शामिल कर लिया है
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
        # --- NAYA SECTION YAHAN ADD KIYA HAI ---
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
    
    # 🚀 UPDATE: Header mein Product_Name, Size, aur Color ke columns add kar diye hain
    writer.writerow([
        'Order_ID', 'Product_ID', 'Product_Name', 'Size', 'Color', 'Quantity', 
        'Customer_Name', 'Customer_Email', 'Customer_Phone',
        'Shipping_Address', 'Shipping_Address_2', 'Shipping_City', 
        'Shipping_Pincode', 'Shipping_State', 'Shipping_Country',
        'Order_Status', 'Total_Amount', 'Payment_Method', 'Created_At'
    ])
    
    for obj in queryset:
        # 1. Base Data
        user = obj.user
        addr_obj = obj.address  # Linked Address Model
        address_text = str(addr_obj) if addr_obj else ""

        # 3. SUPER DYNAMIC PHONE (100% UNTOUCHED)
        phone = getattr(addr_obj, 'mobile', '') or getattr(addr_obj, 'phone', '')
        if not phone:
            profile = Profile.objects.filter(user=user).first()
            phone = getattr(profile, 'phone', '') or getattr(profile, 'mobile', '')
        if not phone:
            match = re.search(r'\d{10,12}', address_text)
            phone = match.group(0) if match else ""
        
        formatted_phone = f"'{phone}" if phone else "'9999999999"

        # 4. SUPER DYNAMIC PINCODE (100% UNTOUCHED)
        pincode = getattr(addr_obj, 'pincode', '')
        if not pincode:
            match = re.search(r'\b\d{6}\b', address_text)
            pincode = match.group(0) if match else ""

        # 5. DYNAMIC CITY & STATE (100% UNTOUCHED)
        city = getattr(addr_obj, 'city', '')
        state = getattr(addr_obj, 'state', '')

        if not city or not state:
            parts = [p.strip() for p in address_text.split(',') if p.strip()]
            if len(parts) >= 2:
                if not city: city = parts[-2]
                if not state: state = re.sub(r'\d+', '', parts[-1]).strip()

        # 6. Payment Method Fix (100% UNTOUCHED)
        pay_method = str(obj.payment_method).upper()
        final_pay = "Prepaid" if any(x in pay_method for x in ["ONLINE", "RAZORPAY", "PREPAID"]) else "COD"

        # 🚀 STEP 7: ORDER ITEMS LOOP (Har item ka Size, Color aur Qty nikalne ke liye)
        order_items = obj.items.all()
        
        if order_items.exists():
            for item in order_items:
                product_id = item.product.id if item.product else "N/A"
                product_name = item.product.name if item.product else "N/A"
                item_size = item.size if item.size else "Default"
                item_color = item.color if item.color else "Default"
                item_qty = item.quantity if hasattr(item, 'quantity') else 1

                writer.writerow([
                    obj.id,
                    product_id,
                    product_name,      # Naya Column 🚀
                    item_size,         # Naya Column 🚀
                    item_color,        # Naya Column 🚀
                    item_qty,          # Naya Column 🚀
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
        else:
            # Fallback: Agar kisi wajah se order me koi item na mile, toh row fir bhi generate ho taaki record miss na ho
            writer.writerow([
                obj.id,
                "N/A", "No Items", "N/A", "N/A", 0,
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
    actions = [export_to_csv]  # Yahan action add ho gaya

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'color', 'size', 'quantity')



# --- Models Registration ---
admin.site.register(Category)
admin.site.register(Cart)
admin.site.register(Address)
admin.site.register(Profile)