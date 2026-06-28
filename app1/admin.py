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

# --- Autocomplete Mandatory Registration Engine ---
# In teeno models me search_fields hona compulsory hai kyunki ProductAdmin me autocomplete_fields use ho rha hai
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category') 
    list_filter = ('category',)
    search_fields = ('name',)

@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'sub_category')
    list_filter = ('sub_category',)
    search_fields = ('name',)


# --- Product Inlines Setup ---
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class SimpleProductSizeStockInline(admin.TabularInline):
    model = SimpleProductSizeStock
    extra = 1
    fields = ('size_name', 'stock') # Dono ek hi row me render honge

class ColorSizeStockInline(admin.TabularInline):
    model = ColorSizeStock
    extra = 1
    fields = ('size_name', 'stock')


# --- Product Colors Section Control ---
class ProductColorInline(admin.StackedInline):
    model = ProductColor
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


@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ['color_name', 'product']
    search_fields = ['color_name', 'product__name'] # Search capacity enhanced
    inlines = [ColorSizeStockInline]


# --- Main Product Core Admin (RAM Optimized Layout) ---
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # 1. List View Tweaks
    list_display = [
    'name',
    'brand',
    'price',
    'original_price',
    'offer_end_time',
    'offer_status',
    'get_full_category',
    'has_variants',
    'is_active'
]
    list_filter = ['is_active', 'has_variants', 'brand']
    
    # Autocomplete config mapping smoothly now
    autocomplete_fields = ['category', 'sub_category', 'product_type']
    search_fields = ['name', 'brand']
    list_per_page = 20  # RAM saturation security boundaries
    
    inlines = [ProductImageInline, SimpleProductSizeStockInline, ProductColorInline]

    # 2. SQL N+1 Query Optimization
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('category', 'sub_category', 'product_type')

    # 3. Dynamic Path Loader (No Database Overhead)
    def get_full_category(self, obj):
        path = f"{obj.category.name}" if obj.category else "No Category"
        if obj.sub_category:
            path += f" -> {obj.sub_category.name}"
        if obj.product_type:
            path += f" -> {obj.product_type.name}"
        return path
    get_full_category.short_description = 'Full Category Path'

    def offer_status(self, obj):
        if obj.offer_active:
            return "✅ Active"
            return "❌ Expired"

    offer_status.short_description = "Offer"
    
            
    # 4. Detailed Sections Fieldsets
    fieldsets = (
        ("Basic Information", {
            'fields': (
                'brand', 'name', 'description', 
                'price', 'original_price', 'offer_end_time', 'image', 'size_chart',
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


# --- Orders & Cart Engine Context ---
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'color', 'size', 'quantity', 'price')


# --- Shiprocket Core CSV Generator Action ---
def export_to_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="shiprocket_final_ready.csv"'
    writer = csv.writer(response)
    
    writer.writerow([
        'Order_ID', 'Product_ID', 'Product_Name', 'Size', 'Color', 'Quantity', 
        'Customer_Name', 'Customer_Email', 'Customer_Phone',
        'Shipping_Address', 'Shipping_Address_2', 'Shipping_City', 
        'Shipping_Pincode', 'Shipping_State', 'Shipping_Country',
        'Order_Status', 'Total_Amount', 'Payment_Method', 'Created_At'
    ])
    
    for obj in queryset:
        user = obj.user
        addr_obj = obj.address 
        address_text = str(addr_obj) if addr_obj else ""

        # Phone extraction configuration
        phone = getattr(addr_obj, 'mobile', '') or getattr(addr_obj, 'phone', '')
        if not phone:
            profile = Profile.objects.filter(user=user).first()
            phone = getattr(profile, 'phone', '') or getattr(profile, 'mobile', '')
        if not phone:
            match = re.search(r'\d{10,12}', address_text)
            phone = match.group(0) if match else ""
        
        formatted_phone = f"'{phone}" if phone else "'9999999999"

        # Pincode parsing rules
        pincode = getattr(addr_obj, 'pincode', '')
        if not pincode:
            match = re.search(r'\b\d{6}\b', address_text)
            pincode = match.group(0) if match else ""

        # City / State extraction arrays
        city = getattr(addr_obj, 'city', '')
        state = getattr(addr_obj, 'state', '')

        if not city or not state:
            parts = [p.strip() for p in address_text.split(',') if p.strip()]
            if len(parts) >= 2:
                if not city: city = parts[-2]
                if not state: state = re.sub(r'\d+', '', parts[-1]).strip()

        pay_method = str(obj.payment_method).upper()
        final_pay = "Prepaid" if any(x in pay_method for x in ["ONLINE", "RAZORPAY", "PREPAID"]) else "COD"

        order_items = obj.items.all()
        
        if order_items.exists():
            for item in order_items:
                product_id = item.product.id if item.product else "N/A"
                product_name = item.product.name if item.product else "N/A"
                item_size = item.size if item.size else "Default"
                item_color = item.color if item.color else "Default"
                item_qty = item.quantity if hasattr(item, 'quantity') else 1

                writer.writerow([
                    obj.id, product_id, product_name, item_size, item_color, item_qty,
                    user.get_full_name() or user.username,
                    user.email or f"{user.username}@gmail.com",
                    formatted_phone, address_text, "", 
                    city or "Update City", pincode or "000000", state or "Update State",
                    "India", obj.status, obj.total_amount, final_pay,
                    obj.created_at.strftime("%d-%m-%Y %H:%M")
                ])
        else:
            writer.writerow([
                obj.id, "N/A", "No Items", "N/A", "N/A", 0,
                user.get_full_name() or user.username,
                user.email or f"{user.username}@gmail.com",
                formatted_phone, address_text, "", 
                city or "Update City", pincode or "000000", state or "Update State",
                "India", obj.status, obj.total_amount, final_pay,
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


# --- Remaining Standard Model Registrations ---
# (Note: Category registration removed from here and decorated at the top class level successfully)
admin.site.register(Cart)
admin.site.register(Address)
admin.site.register(Profile)