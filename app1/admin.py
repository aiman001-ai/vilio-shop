import csv
import json
import re  # Pincode dhoondne ke liye
from django.http import HttpResponse, JsonResponse
from django.contrib import admin
from django.urls import reverse, path
from django.utils import timezone
from django.utils.html import format_html  # <-- यह इम्पोर्ट करना ज़रूरी है
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    Product, ProductImage, Category, SubCategory, ProductType,
    ProductColor, ColorSizeStock, SimpleProductSizeStock,
    Cart, CartItem, Order, OrderItem, Address, Profile, Lead, Banner, CustomerReview
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
    change_list_template = "admin/app1/productcolor/change_list.html"
    list_display = [
        'color_preview',
        'product_link',
        'color_badge',
        'stock_inline_editor',
        'total_stock_display',
        'row_actions'
    ]
    search_fields = ['color_name', 'product__name', 'product__brand']
    list_filter = ['product__brand', 'product__category']
    list_per_page = 100  # Show all product colors on one single page
    inlines = [ColorSizeStockInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'product__category').prefetch_related('sizes')

    def color_preview(self, obj):
        if obj.color_image:
            try:
                url = obj.color_image.url
                return format_html(
                    '<img src="{}" style="width: 38px; height: 38px; object-fit: cover; border-radius: 6px; border: 1px solid #cbd5e1; box-shadow: 0 1px 3px rgba(0,0,0,0.1);" alt="{}">',
                    url, obj.color_name
                )
            except Exception:
                pass
        return format_html('<div style="width: 38px; height: 38px; background: #f1f5f9; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 10px; color: #94a3b8; border: 1px dashed #cbd5e1;">No Img</div>')
    color_preview.short_description = "Image"

    def product_link(self, obj):
        product_url = reverse('admin:app1_product_change', args=[obj.product.id])
        brand_name = obj.product.brand or 'VILIO'
        cat_name = obj.product.category.name if obj.product.category else ''
        return format_html(
            '<div style="line-height: 1.35;">'
            '<a href="{}" style="font-weight: 700; color: #1e293b; font-size: 13px; text-decoration: none;" title="Edit Product">{}</a>'
            '<div style="font-size: 11px; color: #64748b; margin-top: 2px;">🏷️ {} {}</div>'
            '</div>',
            product_url, obj.product.name, brand_name, f"• {cat_name}" if cat_name else ""
        )
    product_link.short_description = "Product"

    def color_badge(self, obj):
        color_url = reverse('admin:app1_productcolor_change', args=[obj.id])
        return format_html(
            '<a href="{}" style="display: inline-block; padding: 4px 10px; border-radius: 20px; background: #f8fafc; border: 1px solid #cbd5e1; font-weight: 700; font-size: 11.5px; color: #0f172a; text-decoration: none;" title="Edit Color Variant">'
            '🎨 {}'
            '</a>',
            color_url, obj.color_name
        )
    color_badge.short_description = "Color"

    def stock_inline_editor(self, obj):
        sizes = list(obj.sizes.all())
        if not sizes:
            return format_html(
                '<div class="no-sizes-wrap" id="sizes-box-{}">'
                '<span style="font-size: 11px; color: #94a3b8; margin-right: 8px;">No sizes</span>'
                '<button type="button" class="btn-init-sizes" onclick="initStandardSizes({})" style="background: #475569; color: #fff; border: none; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; cursor: pointer;">+ Add S, M, L, XL, 2XL</button>'
                '</div>',
                obj.id, obj.id
            )

        items_html = []
        for s in sizes:
            items_html.append(
                f'<div class="stock-pill" style="display: inline-flex; align-items: center; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; overflow: hidden; margin: 2px 4px 2px 0; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">'
                f'<span style="background: #f1f5f9; color: #334155; font-size: 11px; font-weight: 700; padding: 4px 7px; border-right: 1px solid #cbd5e1; text-transform: uppercase;">{s.size_name}</span>'
                f'<input type="number" class="stock-input" data-size-id="{s.id}" data-color-id="{obj.id}" data-original="{s.stock}" value="{s.stock}" min="0" '
                f'style="width: 48px; border: none; padding: 4px 6px; font-size: 12px; font-weight: 700; text-align: center; color: #0f172a; outline: none; background: transparent;" '
                f'oninput="handleStockInput(this, {obj.id})" onkeydown="if(event.key===\'Enter\'){{event.preventDefault();saveColorStock({obj.id});}}">'
                f'</div>'
            )

        add_btn = (
            f'<button type="button" onclick="addCustomSizePrompt({obj.id})" '
            f'style="background: #f8fafc; border: 1px dashed #94a3b8; color: #64748b; font-size: 10px; font-weight: 700; padding: 4px 7px; border-radius: 4px; cursor: pointer; margin-left: 4px;" title="Add another custom size">'
            f'+ Size'
            f'</button>'
        )

        return format_html(
            '<div class="stock-editor-box" id="sizes-box-{}" style="display: flex; flex-wrap: wrap; align-items: center; max-width: 480px;">'
            '{}{}'
            '</div>',
            obj.id, mark_safe(''.join(items_html)), mark_safe(add_btn)
        )
    stock_inline_editor.short_description = "Sizes & Stocks (Edit Directly Here)"

    def total_stock_display(self, obj):
        total = sum(s.stock for s in obj.sizes.all())
        if total <= 0:
            badge = f'<span id="total-badge-{obj.id}" style="display: inline-block; padding: 4px 9px; border-radius: 4px; background: #fee2e2; color: #dc2626; font-weight: 800; font-size: 11px; border: 1px solid #fca5a5; white-space: nowrap;">❌ SOLD OUT (0)</span>'
        else:
            badge = f'<span id="total-badge-{obj.id}" style="display: inline-block; padding: 4px 9px; border-radius: 4px; background: #dcfce7; color: #15803d; font-weight: 800; font-size: 11px; border: 1px solid #86efac; white-space: nowrap;">✅ {total} in stock</span>'
        return mark_safe(badge)
    total_stock_display.short_description = "Status"

    def row_actions(self, obj):
        return format_html(
            '<div style="display: flex; align-items: center; gap: 8px;">'
            '<button type="button" id="save-btn-{}" onclick="saveColorStock({})" '
            'style="background: #2563eb; color: #ffffff; border: none; padding: 5px 12px; border-radius: 5px; font-size: 12px; font-weight: 700; cursor: pointer; box-shadow: 0 1px 3px rgba(37,99,235,0.3); transition: all 0.15s ease;" '
            'onmouseover="this.style.background=\'#1d4ed8\'" onmouseout="this.style.background=\'#2563eb\'">'
            '💾 Save'
            '</button>'
            '<span id="status-{}" style="font-size: 11px; font-weight: 700; color: #16a34a; white-space: nowrap;"></span>'
            '</div>',
            obj.id, obj.id, obj.id
        )
    row_actions.short_description = "Save"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('quick-update-stock/', self.admin_site.admin_view(csrf_exempt(self.quick_update_stock_view)), name='productcolor_quick_update_stock'),
            path('quick-init-sizes/', self.admin_site.admin_view(csrf_exempt(self.quick_init_sizes_view)), name='productcolor_quick_init_sizes'),
            path('quick-add-custom-size/', self.admin_site.admin_view(csrf_exempt(self.quick_add_custom_size_view)), name='productcolor_quick_add_custom_size'),
        ]
        return custom_urls + urls

    def quick_update_stock_view(self, request):
        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
        try:
            data = json.loads(request.body.decode('utf-8'))
            updates = data.get('updates', [])
            color_id = data.get('color_id')
            
            for item in updates:
                size_id = item.get('size_id')
                stock = item.get('stock')
                if size_id is not None and stock is not None:
                    stock_int = max(0, int(stock))
                    ColorSizeStock.objects.filter(id=size_id).update(stock=stock_int)
            
            # Clear caches so website reflects live
            cache.delete('home_display_products_v3')
            cache.delete('home_display_products_v4')

            if color_id:
                total = sum(ColorSizeStock.objects.filter(product_color_id=color_id).values_list('stock', flat=True))
                return JsonResponse({'success': True, 'total_stock': total, 'updated_count': len(updates)})
            else:
                size_ids = [u['size_id'] for u in updates if 'size_id' in u]
                touched_colors = set(ColorSizeStock.objects.filter(id__in=size_ids).values_list('product_color_id', flat=True))
                variant_totals = {}
                for c_id in touched_colors:
                    variant_totals[c_id] = sum(ColorSizeStock.objects.filter(product_color_id=c_id).values_list('stock', flat=True))
                return JsonResponse({'success': True, 'variant_totals': variant_totals, 'updated_count': len(updates)})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    def quick_init_sizes_view(self, request):
        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
        try:
            data = json.loads(request.body.decode('utf-8'))
            color_id = data.get('color_id')
            product_color = ProductColor.objects.get(id=color_id)
            default_sizes = ['S', 'M', 'L', 'XL', '2XL']
            existing_names = set(product_color.sizes.values_list('size_name', flat=True))
            created_sizes = []
            for name in default_sizes:
                if name not in existing_names:
                    s = ColorSizeStock.objects.create(product_color=product_color, size_name=name, stock=0)
                    created_sizes.append({'id': s.id, 'size_name': s.size_name, 'stock': s.stock})
                else:
                    s = product_color.sizes.get(size_name=name)
                    created_sizes.append({'id': s.id, 'size_name': s.size_name, 'stock': s.stock})
            return JsonResponse({'success': True, 'sizes': created_sizes})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    def quick_add_custom_size_view(self, request):
        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
        try:
            data = json.loads(request.body.decode('utf-8'))
            color_id = data.get('color_id')
            size_name = (data.get('size_name') or '').strip().upper()
            stock = max(0, int(data.get('stock', 0)))
            if not size_name:
                return JsonResponse({'success': False, 'error': 'Size name cannot be empty'}, status=400)
            product_color = ProductColor.objects.get(id=color_id)
            s, created = ColorSizeStock.objects.get_or_create(
                product_color=product_color, 
                size_name=size_name,
                defaults={'stock': stock}
            )
            if not created:
                s.stock = stock
                s.save()
            return JsonResponse({'success': True, 'size': {'id': s.id, 'size_name': s.size_name, 'stock': s.stock}})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@admin.register(ColorSizeStock)
class ColorSizeStockAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'color_name', 'size_name', 'stock')
    list_editable = ('stock',)
    list_filter = ('size_name', 'product_color__product__brand')
    search_fields = ('product_color__product__name', 'product_color__color_name', 'size_name')
    list_per_page = 100

    def product_name(self, obj):
        return obj.product_color.product.name
    product_name.short_description = "Product"

    def color_name(self, obj):
        return obj.product_color.color_name
    color_name.short_description = "Color"


# --- Main Product Core Admin (RAM Optimized Layout) ---
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # 1. List View Tweaks
    list_display = [
    'name',
    'brand',
    'price',
    'original_price',
    'offer_enabled',
    'offer_started_at',
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
    readonly_fields = ('offer_started_at',)
    
    inlines = [ProductImageInline, SimpleProductSizeStockInline, ProductColorInline]

    def save_model(self, request, obj, form, change):

        if change:
            old_obj = Product.objects.get(pk=obj.pk)

            if not old_obj.offer_enabled and obj.       offer_enabled:
                obj.offer_started_at = timezone.now()

            elif old_obj.offer_enabled and not obj.offer_enabled:
                obj.offer_started_at = None

        elif obj.offer_enabled:
            obj.offer_started_at = timezone.now()

        super().save_model(request, obj, form, change)

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
                'price', 'original_price', 'offer_enabled', 'offer_started_at', 'image', 'size_chart',
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
admin.site.register(Profile)

# ===== ADDRESS ADMIN (Improved) =====
# Pehle plain registration hatao
admin.site.unregister(Address) if Address in [m.model for m in admin.site._registry.values()] else None

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display  = ('user_name', 'user_email', 'full_name', 'mobile', 'city', 'state', 'pincode', 'submitted_at')
    list_filter   = ('state', 'city')
    search_fields = ('user__username', 'user__email', 'first_name', 'last_name', 'mobile', 'city')
    ordering      = ('-id',)

    def user_name(self, obj):
        return obj.user.username
    user_name.short_description = 'Username'

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
    full_name.short_description = 'Full Name'

    def submitted_at(self, obj):
        if obj.created_at:
            return obj.created_at.strftime('%d %b %Y %H:%M')
        return '—'
    submitted_at.short_description = 'Submitted At'


# ===== USER ADMIN (Google Login + Normal dono dikhaye) =====
# Pehle Django ka default User admin unregister karo
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    list_display  = ('username', 'email', 'full_name', 'login_type', 
                     'has_address', 'has_order', 'date_joined', 'last_login')
    list_filter   = ('is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering      = ('-date_joined',)

    def full_name(self, obj):
        name = f"{obj.first_name} {obj.last_name}".strip()
        return name if name else '—'
    full_name.short_description = 'Name'

    def login_type(self, obj):
        # Google se login kiya toh socialaccount hoga
        try:
            from allauth.socialaccount.models import SocialAccount
            if SocialAccount.objects.filter(user=obj, provider='google').exists():
                return '🟢 Google'
        except ImportError:
            pass
        return '🔵 Email'
    login_type.short_description = 'Login Type'

    def has_address(self, obj):
        return '✅' if Address.objects.filter(user=obj).exists() else '❌'
    has_address.short_description = 'Address?'

    def has_order(self, obj):
        return '✅' if Order.objects.filter(user=obj).exists() else '❌'
    has_order.short_description = 'Order?'

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display  = ('name', 'email', 'phone', 'source', 'created_at')
    list_filter   = ('source', 'created_at')
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('created_at',)
    ordering      = ('-created_at',)

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'badge', 'button_text', 'order', 'is_active', 'created_at')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'subtitle', 'badge')

@admin.register(CustomerReview)
class CustomerReviewAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'product_name', 'rating', 'is_verified', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_verified', 'is_approved', 'created_at')
    search_fields = ('name', 'city', 'product_name', 'comment')
    list_editable = ('is_approved', 'is_verified')

    