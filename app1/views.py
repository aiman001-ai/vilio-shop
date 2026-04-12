import random
import razorpay  # Library को अलग से इम्पोर्ट किया
from django.core.mail import send_mail
from django.conf import settings # Razorpay Keys के लिए ज़रूरी
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import F, Sum, Q

# Models में से razorpay हटा दिया गया है क्योंकि वो मॉडल नहीं है
from .models import (
    Address, Profile, Product, Cart, CartItem, 
    Order, OrderItem, ProductColor, ColorSizeStock, Category, SubCategory, ProductType, Blog
)

# ================= HOME =================
def home(request):
    # Ab sirf active products dikhenge. 
    # Stock ka check humne hata diya hai kyunki aap manually control kar rahe ho.
    products = Product.objects.filter(is_active=True).order_by('?')
    return render(request, 'home.html', {'products': products})
# ================= SHOP NOW (BUY NOW) =================
def shop_now(request, product_id):
    if not request.user.is_authenticated:
        # लॉगिन से पहले डेटा सेशन में सुरक्षित रखें
        request.session['buy_now_product'] = product_id
        request.session['buy_now_color'] = request.GET.get('color', 'Default')
        request.session['buy_now_size'] = request.GET.get('size', 'S')
        request.session['after_login_redirect'] = 'cart'
        return redirect('/login/')
    
    # सीधे कार्ट में डालें (URL पैरामीटर्स के साथ)
    add_product_to_cart(request, product_id) 
    return redirect('cart')

# ================= LOGIN =================
def login_page(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            merge_cart(request)
            redirect_to = request.session.pop('after_login_redirect', None)
            return redirect('cart' if redirect_to == 'cart' else 'home')
        else:
            messages.error(request, "Invalid credentials")
    return render(request, 'login.html')

# ================= POST LOGIN REDIRECT =================
@login_required
def post_login_redirect(request):
    # 1. Buy Now वाला पेंडिंग चेक करें
    product_id = request.session.pop('buy_now_product', None)
    if product_id:
        color = request.session.pop('buy_now_color', 'Default')
        size = request.session.pop('buy_now_size', 'S')
        # यहाँ हमने कलर और साइज पास कर दिया ताकि स्टॉक सही मिले
        add_product_to_cart(request, product_id, color=color, size=size)
        return redirect('cart')

    # 2. Add to Bag वाला पेंडिंग चेक करें
    pending_product = request.session.pop('pending_cart_product', None)
    if pending_product:
        p_color = request.session.pop('pending_color', 'Default')
        p_size = request.session.pop('pending_size', 'S')
        add_product_to_cart(request, pending_product, color=p_color, size=p_size)
        return redirect('cart')

    redirect_to = request.session.pop('after_login_redirect', None)
    return redirect('cart' if redirect_to == 'cart' else 'home')
# ================= MERGE SESSION CART TO DB =================
def merge_cart(request):
    session_cart = request.session.get('cart', {})
    if session_cart and request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        for pid, qty in session_cart.items():
            product = Product.objects.get(id=pid)
            item, created = CartItem.objects.get_or_create(cart=cart, product=product)
            if not created:
                item.quantity += qty
            else:
                item.quantity = qty
            item.save()
        del request.session['cart']

# ================= LOGOUT =================
def logout_page(request):
    logout(request)
    return redirect('home')

# ================= ADD TO CART (AJAX & NORMAL) =================
def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({'login_required': True, 'login_url': '/login/'})

    product = get_object_or_404(Product, id=product_id)
    color = request.GET.get('color', 'Default') # अगर बिना कलर वाला है तो 'Default'
    size = request.GET.get('size')
    
    available_stock = 0

    # --- TYPE 1: WITHOUT COLOR ---
    if not product.has_variants:
        # यहाँ बदलाव है: हम उस साइज का स्टॉक निकाल रहे हैं जो यूजर ने चुना है
        # 'simple_size_stocks' वही related_name है जो आपने template में use किया है
        size_obj = product.simple_size_stocks.filter(size_name=size).first()
        
        if size_obj:
            available_stock = size_obj.stock
        else:
            # अगर साइज नहीं मिला, तो बैकअप के तौर पर simple_stock (अगर use करते हो)
            available_stock = product.simple_stock if product.simple_stock else 0
            
        final_color = "Default"
        
    # --- TYPE 2: WITH COLOR ---
    else:
        try:
            # पहले कलर वेरिएंट ढूंढो
            color_obj = ProductColor.objects.get(product=product, color_name=color)
            # फिर उस कलर का साइज और स्टॉक ढूंढो
            size_obj = ColorSizeStock.objects.get(product_color=color_obj, size_name=size)
            available_stock = size_obj.stock
            final_color = color
        except (ProductColor.DoesNotExist, ColorSizeStock.DoesNotExist):
            return JsonResponse({'success': False, 'message': 'This combination is not available'})

    # --- CART PROCESSING ---
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(
        cart=cart, product=product, color=final_color, size=size
    )

    if not created:
        if item.quantity < available_stock:
            item.quantity += 1
            item.save()
            msg = "Quantity updated!"
        else:
            return JsonResponse({'success': False, 'message': f'Only {available_stock} items left!'})
    else:
        if available_stock > 0:
            item.quantity = 1
            item.save()
            msg = "Added to bag!"
        else:
            item.delete()
            return JsonResponse({'success': False, 'message': 'Out of stock!'})

    total_count = sum(i.quantity for i in cart.items.all())
    return JsonResponse({'success': True, 'message': msg, 'global_cart_count': total_count})

# Helper function for internal use
def add_product_to_cart(request, product_id, color=None, size=None):
    product = get_object_or_404(Product, id=product_id)
    
    # अगर डायरेक्ट पैरामीटर (लॉगिन के बाद के लिए) नहीं मिला, तो URL से लो
    color_name = color if color else request.GET.get('color', 'Default')
    size_name = size if size else request.GET.get('size', 'S')
    
    available_stock = 0
    final_color = color_name

    # --- नया लॉजिक (Tick = Has Colors) ---
    # नोट: अगर आपने models.py में has_variants को "Does this product have colors?" कर दिया है 
    # तो logic सीधा रहेगा।
    if not product.has_variants:
        size_obj = product.simple_size_stocks.filter(size_name=size_name).first()
        available_stock = size_obj.stock if size_obj else 0
        final_color = "Default"
    else:
        # Variant Product (Has colors)
        color_variant = ProductColor.objects.filter(product=product, color_name=color_name).first()
        if color_variant:
            size_variant = ColorSizeStock.objects.filter(product_color=color_variant, size_name=size_name).first()
            if size_variant:
                available_stock = size_variant.stock
                final_color = color_name
        else:
            available_stock = 0

    # कार्ट में जोड़ना
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(
        cart=cart, 
        product=product, 
        color=final_color, 
        size=size_name
    )

    if not created:
        if item.quantity < available_stock:
            item.quantity += 1
            item.save()
    else:
        if available_stock > 0:
            item.quantity = 1
            item.save()
        else:
            # अगर स्टॉक नहीं मिला, तो आइटम हटा दो (ताकि खाली कार्ट न दिखे)
            item.delete()

def cart(request):
    cart_items = []
    total = 0
    if request.user.is_authenticated:
        cart_obj, _ = Cart.objects.get_or_create(user=request.user)
        
        for item in cart_obj.items.select_related('product').all():
            subtotal = item.product.price * item.quantity
            total += subtotal
            
            # --- Image Logic for Simple vs Variant ---
            display_img = "/static/images/no-image.png"
            
            if item.color == "Default" or not item.color:
                # Without color वाले के लिए Main Image उठाओ
                if item.product.image:
                    display_img = item.product.image.url
            else:
                # Color variant वाले के लिए Variant Image उठाओ
                variant = ProductColor.objects.filter(product=item.product, color_name=item.color).first()
                if variant and variant.color_image:
                    display_img = variant.color_image.url
                elif item.product.image:
                    display_img = item.product.image.url
            
            cart_items.append({
                'item_id': item.id,
                'product': item.product,
                'quantity': item.quantity,
                'subtotal': subtotal,
                'color': item.color,
                'size': item.size,
                'display_image': display_img,
            })
            
    return render(request, 'cart.html', {'cart_items': cart_items, 'total': total})

# ================= QUANTITY CONTROLS (AJAX) =================
@login_required
@require_POST
def increase_quantity(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product = cart_item.product
    
    available_stock = 0

    # 1. Stock Check Logic (Simple vs Variant)
    if not product.has_variants:
        # Simple product ke liye specific size ka stock nikalein
        size_obj = product.simple_size_stocks.filter(size_name=cart_item.size).first()
        available_stock = size_obj.stock if size_obj else 0
    else:
        # Variant product (Colors) ke liye stock nikalein
        try:
            color_obj = ProductColor.objects.get(product=product, color_name=cart_item.color)
            size_obj = ColorSizeStock.objects.get(product_color=color_obj, size_name=cart_item.size)
            available_stock = size_obj.stock
        except:
            available_stock = 0

    # 2. Validation: Kya stock bacha hai?
    if cart_item.quantity >= available_stock:
        return JsonResponse({
            'success': False, 
            'message': f'Sorry, only {available_stock} items in stock!',
            'quantity': cart_item.quantity,
            'total': float(calculate_total(request.user))
        })

    # 3. Agar stock hai, toh badhao
    cart_item.quantity += 1
    cart_item.save()
    
    data = cart_item_data(request.user, cart_item)
    data['success'] = True
    return JsonResponse(data)


@login_required
@require_POST
def decrease_quantity(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
        data = cart_item_data(request.user, cart_item)
        data['success'] = True
        return JsonResponse(data)
    else:
        # Agar 1 se kam ho raha hai toh delete kar do
        cart_item.delete()
        return JsonResponse({
            'success': True, 
            'quantity': 0, 
            'subtotal': 0, 
            'total': float(calculate_total(request.user))
        })

def cart_item_data(user, cart_item):
    total_val = calculate_total(user)
    return {
        'success': True,
        'quantity': cart_item.quantity,
        'subtotal': float(cart_item.product.price * cart_item.quantity),
        'total': float(total_val)
    }

def calculate_total(user):
    cart = Cart.objects.filter(user=user).first()
    if not cart: return 0
    result = cart.items.aggregate(total_price=Sum(F('product__price') * F('quantity')))
    return result['total_price'] or 0

# ================= ADDRESS & OTP =================
@login_required
def add_address(request):
    if request.method == 'POST':
        # request.POST.get use karne se website crash nahi hogi agar data missing ho
        name = request.POST.get('name')
        mobile = request.POST.get('mobile')
        address_text = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        pincode = request.POST.get('pincode')

        # Database mein save
        Address.objects.create(
            user=request.user,
            name=name,
            mobile=mobile,
            address=address_text,
            city=city,
            state=state,
            pincode=pincode
        )

        # Agar user checkout se aaya tha toh wapas wahi bhejo, warna profile par
        next_page = request.GET.get('next', 'checkout') 
        return redirect(next_page)

    return render(request, 'add_address.html')

@login_required
def my_addresses(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'my_addresses.html', {'addresses': addresses})

def verify_otp(request):
    if request.method == "POST":
        otp = request.POST['otp']
        user_id = request.session.get('uid')
        profile = Profile.objects.get(user_id=user_id)
        if profile.otp == otp:
            profile.is_verified = True
            profile.save()
            user = profile.user
            user.is_active = True
            user.save()
            return redirect('login')
        return render(request, 'verify_otp.html', {'error': 'Invalid OTP'})
    return render(request, 'verify_otp.html')

# ================= PRODUCT DETAIL =================
def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    
    # 1. Color Variants (पुराना काम - छेड़छाड़ नहीं)
    colors_qs = product.color_variants.all().prefetch_related('sizes')
    variants_data = []
    for c in colors_qs:
        size_list = [f"{s.size_name}:{s.stock}" for s in c.sizes.all()] # साइज के साथ स्टॉक जोड़ा
        size_string = ",".join(size_list)
        total_stock = sum([s.stock for s in c.sizes.all()])
        
        variants_data.append({
            'color_name': c.color_name,
            'color_image': c.color_image,
            'size_name': size_string,  # JS के लिए "S,M,L"
            'stock': total_stock
        })

    # 2. Simple Product Sizes (नया काम)
    simple_sizes_list = product.simple_size_stocks.all()

    colors_qs = product.color_variants.all().prefetch_related('sizes')
    variants_data = []
    for c in colors_qs:
        size_list = [f"{s.size_name}:{s.stock}" for s in c.sizes.all()]
        variants_data.append({
            'color_name': c.color_name,
            'color_image': c.color_image,
            'size_name': ",".join(size_list),
            'stock': sum([s.stock for s in c.sizes.all()])
        })

    simple_sizes_list = product.simple_size_stocks.all()

    # --- NEW: SMART SUGGESTIONS LOGIC ---
    # 1. तय करें कि किस कैटेगरी के लिए क्या दिखाना है
    target_category = None
    current_cat_name = product.category.name.lower()
    current_sub_name = product.sub_category.name.lower() if product.sub_category else ""

    if 'shirt' in current_sub_name or 'top' in current_sub_name:
        target_category = 'Jeans'  # शर्ट वालों को जींस दिखाओ
    elif 'jeans' in current_sub_name or 'pant' in current_sub_name:
        target_category = 'Shirt'  # पैंट वालों को शर्ट दिखाओ
    
    # 2. Related Products निकालें
    related_products = []
    if target_category:
        related_products = list(Product.objects.filter(
            Q(sub_category__name__icontains=target_category) | 
            Q(product_type__name__icontains=target_category),
            is_active=True
        ).exclude(id=product.id)[:10]) # पहले 10 रिलेटेड आइटम

    # 3. बाकी बचे हुए रैंडम प्रोडक्ट्स (ताकि स्लाइडर खाली न रहे)
    other_products = list(Product.objects.filter(is_active=True).exclude(
        id__in=[p.id for p in related_products] + [product.id]
    ).order_by('?')[:15])

    # दोनों को मिला दें (Related वाले पहले आएंगे)
    all_suggestions = related_products + other_products

    return render(request, 'product_detail.html', {
        'product': product, 
        'variants': variants_data, 
        'simple_sizes_list': simple_sizes_list,
        'suggestions': all_suggestions # इसे टेम्पलेट में भेजें
    })

# ================= CHECKOUT & ORDERS =================
@login_required
def checkout(request):
    cart_obj = Cart.objects.filter(user=request.user).first()
    
    # Check agar cart khali hai
    if not cart_obj or not cart_obj.items.exists():
        messages.error(request, "Your cart is empty")
        return redirect('cart')

    # Check agar address nahi hai
    addresses = Address.objects.filter(user=request.user)
    if not addresses.exists():
        messages.info(request, "Please add a delivery address first.")
        return redirect('add_address')

    processed_cart_items = []
    total = 0
    
    # Cart items par loop chala kar details nikalna
    for item in cart_obj.items.select_related('product'):
        subtotal = item.product.price * item.quantity
        total += subtotal
        
        # --- UPDATE: Naya Variant Image Logic ---
        # ProductVariant ki jagah ProductColor model se filter kar rahe hain
        color_var = ProductColor.objects.filter(
            product=item.product, 
            color_name__iexact=item.color
        ).first()

        if color_var and color_var.color_image:
            variant_image = color_var.color_image.url
        elif item.product.image: # Apne main product image field ka naam yahan check karein
            variant_image = item.product.image.url
        else:
            variant_image = "/static/images/no-image.png"

        processed_cart_items.append({
            'product': item.product,
            'quantity': item.quantity,
            'subtotal': subtotal,
            'color': item.color,
            'size': item.size,
            'display_image': variant_image,
        })

    context = {
        'cart_items': processed_cart_items,
        'addresses': addresses,
        'total': total
    }

    return render(request, 'place_order.html', context)

@login_required
@require_POST
def place_order(request):
    address_id = request.POST.get("address_id")
    payment_method = request.POST.get("payment_method")
    
    # ज़रूरी डेटा गेट करें
    address = get_object_or_404(Address, id=address_id, user=request.user)
    cart_obj = get_object_or_404(Cart, user=request.user)
    cart_items = cart_obj.items.all()

    # खाली कार्ट चेक करें
    if not cart_items.exists():
        messages.error(request, "Your cart is empty")
        return redirect('cart')

    # टोटल अमाउंट कैलकुलेट करें
    total = sum(item.product.price * item.quantity for item in cart_items)
    full_address_string = f"{address.name}, {address.mobile}, {address.address}, {address.city}, {address.state} - {address.pincode}"

    # --- CASE 1: CASH ON DELIVERY (COD) ---
    if payment_method == "COD":
        # 1. ऑर्डर क्रिएट करें
        order = Order.objects.create(
            user=request.user,
            address=full_address_string,
            total_amount=total,
            status="Confirmed",
            payment_method="COD",
            payment_status="Pending"
        )
        
        # 2. एडमिन को ईमेल भेजें
        send_admin_order_notification(order)

        # 3. स्टॉक घटाएँ और Order Items बनाएँ
        for item in cart_items:
            try:
                # स्टॉक अपडेट (Variant logic)
                color_obj = ProductColor.objects.get(product=item.product, color_name=item.color)
                size_stock_obj = ColorSizeStock.objects.get(product_color=color_obj, size_name=item.size)
                size_stock_obj.stock = max(0, size_stock_obj.stock - item.quantity)
                size_stock_obj.save()
            except Exception as e:
                print(f"Stock Update Error: {e}")

            # ऑर्डर आइटम सेव करें
            OrderItem.objects.create(
                order=order,
                product=item.product,
                color=item.color,
                size=item.size,
                quantity=item.quantity,
                price=item.product.price
            )
        
        # 4. कार्ट साफ़ करें
        cart_items.delete()
        messages.success(request, "🎉 Order placed successfully (COD)!")
        return redirect('my_orders')

    # --- CASE 2: ONLINE PAYMENT ---
    elif payment_method == "ONLINE":
        # नोट: यहाँ Razorpay का क्लाइंट-साइड से डेटा आने के बाद का लॉजिक है
        # अगर आप Razorpay use कर रहे हैं, तो आमतौर पर payment_id और order_id 
        # success callback से मिलते हैं।
        
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')

        order = Order.objects.create(
            user=request.user,
            address=full_address_string,
            total_amount=total,
            status="Confirmed",
            payment_method="ONLINE",
            payment_status="Paid",
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id
        )

        # एडमिन को ईमेल भेजें
        send_admin_order_notification(order)

        for item in cart_items:
            try:
                color_obj = ProductColor.objects.get(product=item.product, color_name=item.color)
                size_stock_obj = ColorSizeStock.objects.get(product_color=color_obj, size_name=item.size)
                size_stock_obj.stock = max(0, size_stock_obj.stock - item.quantity)
                size_stock_obj.save()
            except:
                pass

            OrderItem.objects.create(
                order=order,
                product=item.product,
                color=item.color,
                size=item.size,
                quantity=item.quantity,
                price=item.product.price
            )

        cart_items.delete()
        messages.success(request, "🎉 Online Payment Successful & Order Placed!")
        return redirect('my_orders')

    # अगर कुछ मैच न हो
    return redirect('checkout')


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'my_orders.html', {'orders': orders})

# ================= SEARCH & CATEGORIES =================
def search(request):
    query = request.GET.get('q')
    products = Product.objects.filter(name__icontains=query, is_active=True) if query else []
    return render(request, 'search_results.html', {'products': products, 'query': query})

def get_menu_data(request):
    # यह डेटा हर पेज पर भेजने के लिए context processor में भी डाल सकते हैं
    categories = Category.objects.prefetch_related('subcategories').all()
    return {'all_categories': categories}

def category_products(request, category_slug, sub_slug=None, type_slug=None):
    # 1. Main Category (Men/Women)
    category = get_object_or_404(Category, name__iexact=category_slug)
    products = Product.objects.filter(category=category, is_active=True)

    # 2. Filtering Logic
    if type_slug:
        # अगर तीनो लेवल मौजूद हैं (/men/top-wear/shirt/)
        products = products.filter(product_type__name__iexact=type_slug)
    elif sub_slug:
        # अगर सिर्फ दो लेवल हैं (/men/shirt/) 
        # तो हम चेक करेंगे कि ये 'shirt' SubCategory है या ProductType
        products = products.filter(
            Q(sub_category__name__iexact=sub_slug) | 
            Q(product_type__name__iexact=sub_slug)
        )

    context = {
        'products': products,
        'category_name': category_slug,
        'sub_category_name': sub_slug,
        'type_name': type_slug
    }
    return render(request, 'category_products.html', context)

def category_default(request, category_slug):
    # 1. 'category_slug' नाम यहाँ होना जरूरी है (ताकि TypeError न आए)
    
    # 2. डेटाबेस से उस पूरी कैटेगरी के सारे प्रोडक्ट्स उठाएं
    products = Product.objects.filter(category__name__iexact=category_slug)
    
    # 3. आपकी 'category_products.html' फाइल को रेंडर करें
    # इससे नया पेज खुलेगा और 'men' वाले सारे कपड़े दिखेंगे
    context = {
        'products': products,
        'category': category_slug,
        'sub_category': 'All Products', 
    }
    
    return render(request, 'category_products.html', context)


# ================= CANCEL ORDER (NEW) =================
@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Status check: Sirf Confirmed ya Placed order hi cancel honge
   # Yahan 'Pending' add kiya hai kyunki aapka default status wahi hai
    if order.status in ['Confirmed', 'Placed', 'Pending']:
        if order.can_cancel:
            order_items = OrderItem.objects.filter(order=order)
            
            for item in order_items:
                c_name = item.color.strip() if item.color else ""
                s_name = item.size.strip() if item.size else ""
                
                try:
                    color_obj = ProductColor.objects.get(product=item.product, color_name__iexact=c_name)
                    size_stock_obj = ColorSizeStock.objects.get(product_color=color_obj, size_name__iexact=s_name)
                    
                    # Stock restoration
                    size_stock_obj.stock = F('stock') + item.quantity
                    size_stock_obj.save()
                except:
                    pass

            order.status = 'Cancelled'
            order.save()
            messages.success(request, "Order successfully cancelled.")
        else:
            messages.error(request, "Cancellation time expired (5-minute window).")
    
    return redirect('my_orders')

@login_required
def payment_success(request):
    payment_id = request.GET.get('payment_id')
    order_id = request.GET.get('order_id')
    address_id = request.GET.get('address_id') 

    # 1. डेटा निकालें
    cart_obj = get_object_or_404(Cart, user=request.user)
    cart_items = cart_obj.items.all()
    
    # Address check karein
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    total = sum(item.product.price * item.quantity for item in cart_items)

    # 2. असली Order डेटाबेस में बनाएँ
    # Note: Humne address fields ko fix kiya hai (house/street hata kar)
    order = Order.objects.create(
    user=request.user,
    # MOBILE BHI DAAL DIYA AB STRING MEIN
    address=f"{address.name}, {address.mobile}, {address.address}, {address.city}, {address.state} - {address.pincode}",
    total_amount=total,
    status="Confirmed",
    payment_method="ONLINE",
    payment_status="Paid",
    razorpay_order_id=order_id,
    razorpay_payment_id=payment_id
)

    # 3. स्टॉक घटाएँ (Stock Minus Logic)
    for item in cart_items:
        try:
            # Color aur Size ke basis par stock dhoondein
            color_obj = ProductColor.objects.get(product=item.product, color_name=item.color)
            size_stock_obj = ColorSizeStock.objects.get(product_color=color_obj, size_name=item.size)
            
            # Stock kam karein
            size_stock_obj.stock = max(0, size_stock_obj.stock - item.quantity)
            size_stock_obj.save()

            # Order Item record karein
            OrderItem.objects.create(
                order=order,
                product=item.product,
                color=item.color,
                size=item.size,
                quantity=item.quantity,
                price=item.product.price
            )
        except Exception as e:
            # Agar koi item stock mein nahi milta toh terminal mein error dikhega
            print(f"Error updating stock for {item.product.name}: {e}")

    # 4. कार्ट खाली करें
    cart_items.delete()

    messages.success(request, f"🎉 Payment Successful! Order ID: {order.id}")
    return redirect('my_orders')


def privacy_policy(request):
        return render(request, 'privacy_policy.html')

def shipping_policy(request):
    return render(request, 'shipping_policy.html')        

def about_us(request):
    return render(request, 'about_us.html')    

def return_policy(request):
    return render(request, 'return_policy.html')    

# app1/views.py

def cheapify_insider(request):
    # हम discount_percentage फ़ील्ड को कैलकुलेट करेंगे: ((original_price - price) / original_price) * 100
    # लेकिन आसान रास्ता ये है कि बस वो प्रोडक्ट्स दिखाएं जिनका original_price, actual price से ज्यादा है।
    
    exclusive_deals = Product.objects.filter(
        original_price__gt=F('price'), 
        is_active=True
    ).order_by('?')[:8] # '?' का मतलब है हर बार रैंडम प्रोडक्ट्स दिखेंगे
    
    return render(request, 'insider.html', {'deals': exclusive_deals})  

# app1/views.py
def careers_page(request):
    # हम कुछ डमी जॉब वैकेंसीज बना देते हैं जिन्हें आप बाद में बदल सकते हैं
    jobs = [
        {'title': 'Fashion Designer', 'location': 'Remote / Delhi', 'type': 'Full-time'},
        {'title': 'Social Media Manager', 'location': 'Mumbai', 'type': 'Internship'},
        {'title': 'Operations Lead', 'location': 'Bangalore', 'type': 'Full-time'},
    ]
    return render(request, 'careers.html', {'jobs': jobs})    


def blog_list(request):
    blogs = Blog.objects.all().order_by('-created_at')
    return render(request, 'blog.html', {'blogs': blogs})

def blog_detail(request, slug):
    blog = Blog.objects.get(slug=slug)
    return render(request, 'blog_detail.html', {'blog': blog})    


def sitemap_page(request):
    categories = Category.objects.all()
    return render(request, 'sitemap.html', {'categories': categories})   


def corporate_info(request):
    return render(request, 'corporate_info.html')     

# app1/views.py
from django.contrib import messages

def contact_us(request):
    if request.method == "POST":
        # यहाँ आप डेटाबेस में सेव करने या ईमेल भेजने का कोड लिख सकते हैं
        name = request.POST.get('name')
        messages.success(request, f"Thank you {name}, your message has been sent!")
        return redirect('contact_us')
    return render(request, 'contact.html')    

    # app1/views.py
def faq_page(request):
    faqs = [
        {
            'category': 'Orders & Shipping',
            'questions': [
                {'q': 'How do I track my order?', 'a': 'You can track your order in the "My Orders" section of your profile or using the tracking link sent to your email.'},
                {'q': 'What are the delivery charges?', 'a': 'For Cheapify Insiders, delivery is FREE. For others, a nominal fee of ₹49 is charged on orders below ₹799.'},
            ]
        },
        {
            'category': 'Returns & Refunds',
            'questions': [
                {'q': 'What is the return policy?', 'a': 'We offer a 15-day hassle-free return policy for most products. Items must be unused and have original tags.'},
                {'q': 'When will I get my refund?', 'a': 'Refunds are typically processed within 5-7 business days after we receive the returned product.'},
            ]
        }
    ]
    return render(request, 'faq.html', {'faqs': faqs})


# app1/views.py
def terms_conditions(request):
    return render(request, 'terms.html')

def terms_of_use(request):
    return render(request, 'terms_of_use.html')

@login_required
def track_orders(request):
    # यूजर के सारे ऑर्डर्स उठाएं, नए ऑर्डर्स सबसे ऊपर
    user_orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'track_orders.html', {'orders': user_orders})    

# app1/views.py
def shipping_policy(request):
    return render(request, 'shipping.html')    

# app1/views.py
def return_policy(request):
    return render(request, 'returns.html')    

# app1/views.py
def privacy_policy(request):
    return render(request, 'privacy.html')    

def edit_address(request, addr_id):
    address = get_object_or_404(Address, id=addr_id, user=request.user)
    
    if request.method == "POST":
        address.name = request.POST.get('name')
        address.mobile = request.POST.get('mobile')
        address.address = request.POST.get('address')
        address.city = request.POST.get('city')
        address.state = request.POST.get('state')
        address.pincode = request.POST.get('pincode')
        address.save()
        return redirect('my_addresses') # Apne address list wale URL ka naam likho
        
    return render(request, 'edit_address.html', {'a': address})    


def send_admin_order_notification(order):
    try:
        # Email ka Subject
        subject = f"🚨 NAYA ORDER AAYA HAI - #{order.id}"
        
        # Order items ki list banana (Taki pata chale kya bika hai)
        items = order.items.all()
        item_details = ""
        for item in items:
            item_details += f"- {item.product.name} (Qty: {item.quantity}) - ₹{item.price}\n"

        # Email ki Body
        message = f"""
Bhai, website par naya order receive hua hai!

--- ORDER SUMMARY ---
Order ID: #{order.id}
Customer: {order.user.get_full_name() or order.user.username}
Total Amount: ₹{order.total_amount}
Payment Mode: {order.payment_method}

--- ITEMS ---
{item_details}

--- SHIPPING ADDRESS ---
{order.address}

Jaldi se Admin Panel check karo aur Shiprocket CSV nikaalo!
        """

        # Kisko bhejna hai? (Settings mein jo email hai usi par)
        admin_email = settings.EMAIL_HOST_USER
        
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [admin_email],
            fail_silently=False,
        )
        print("Notification sent to Admin!")
    except Exception as e:
        print(f"Mail bhejte waqt error aaya: {e}")    