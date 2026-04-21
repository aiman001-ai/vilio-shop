from django.urls import path
from .views import (
    home, shop_now, cart, add_to_cart, login_page, verify_otp, 
    logout_page, add_address, my_addresses, delete_address, product_detail, 
    post_login_redirect, increase_quantity, decrease_quantity,
    checkout, place_order, my_orders, search, 
    category_default, category_products, # Category views
    cancel_order, payment_success, privacy_policy, shipping_policy, about_us, return_policy, cheapify_insider, careers_page, blog_list, blog_detail, sitemap_page, corporate_info, contact_us, faq_page, terms_conditions, terms_of_use, track_orders, shipping_policy, return_policy, privacy_policy, edit_address, verify_payment, create_razorpay_order
)

urlpatterns = [
    path('', home, name='home'),
    path('login/', login_page, name='login'),
    path('logout/', logout_page, name='logout'),
    path('verify-otp/', verify_otp, name='verify_otp'),
    path('post-login/', post_login_redirect, name='post_login'),
    path('product/<int:id>/', product_detail, name='product_detail'),
    path('shop-now/<int:product_id>/', shop_now, name='shop_now'),
    path('cart/', cart, name='cart'),
    path('add-to-cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('add-address/', add_address, name='add_address'),
    path('my-addresses/', my_addresses, name='my_addresses'),
    path('delete-address/<int:id>/', delete_address, name='delete_address'),
    path('address/edit/<int:id>/', edit_address, name='edit_address'),

    # Quantity Update AJAX Routes
    path('cart/increase/<int:item_id>/', increase_quantity, name='increase_quantity'),
    path('cart/decrease/<int:item_id>/', decrease_quantity, name='decrease_quantity'),

    # Checkout
    path('checkout/', checkout, name='checkout'),
    path('place-order/', place_order, name='place_order'),
    path('my-orders/', my_orders, name='my_orders'),
    path('search/', search, name='search'),

    # --- ✅ DYNAMIC CATEGORY URLS ---
    
    # 1. Main Category (e.g., /category/men/)
    path('category/<str:category_slug>/', category_default, name='category_default'),
    
    # 2. Sub Category (e.g., /category/men/top-wear/)
    path('category/<str:category_slug>/<str:sub_slug>/', category_products, name='category_products'),

    # 3. Product Type / Deep Level (e.g., /category/men/top-wear/shirt/)
    # Agar aapka menu 3-level deep jata hai to ye use hoga
    path('category/<str:category_slug>/<str:sub_slug>/<str:type_slug>/', category_products, name='category_type_products'),

    # --- ORDER MANAGEMENT ---
    path('cancel-order/<int:order_id>/', cancel_order, name='cancel_order'),

    path('create-razorpay-order/', create_razorpay_order, name='create_razorpay_order'),

    path('payment-success/', payment_success, name='payment_success'),

    path('privacy-policy/', privacy_policy, name='privacy_policy'),

    path('shipping-policy/', shipping_policy, name='shipping_policy'),

    path('about-us/', about_us, name='about_us'),

    path('return-policy/', return_policy, name='return_policy'),

    # myproject/urls.py या app1/urls.py

path('cheapify-insider/', cheapify_insider, name='insider_page'),

# urls.py
path('careers/', careers_page, name='careers'),

# urls.py
path('blog/', blog_list, name='blog_list'),
path('blog/<slug:slug>/', blog_detail, name='blog_detail'),

# urls.py
path('site-map/', sitemap_page, name='sitemap'),

# urls.py
path('corporate-information/', corporate_info, name='corporate_info'),
# urls.py
path('contact-us/', contact_us, name='contact_us'),
# urls.py
path('faq/', faq_page, name='faq'),
# urls.py
path('terms-and-conditions/', terms_conditions, name='terms'),
path('terms-of-use/', terms_of_use, name='terms_use'),
# urls.py
path('track-orders/', track_orders, name='track_orders'),
# urls.py
path('shipping-policy/', shipping_policy, name='shipping_policy'),
# urls.py
path('cancellation-returns/', return_policy, name='return_policy'),
# urls.py
path('privacy-policy/', privacy_policy, name='privacy_policy'),

path('verify-payment/', verify_payment, name='verify_payment'),
]

