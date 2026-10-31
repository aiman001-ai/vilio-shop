from django.urls import path
from django.contrib.sitemaps.views import sitemap
from .sitemaps import StaticViewSitemap
from .views import (
    home, shop_now, cart, add_to_cart, login_page, verify_otp, 
    logout_page, add_address, my_addresses, delete_address, product_detail, 
    post_login_redirect, increase_quantity, decrease_quantity,
    checkout, place_order, my_orders, search, 
    category_default, category_products,
    cancel_order, about_us, cheapify_insider, careers_page, blog_list, blog_detail, 
    sitemap_page, corporate_info, contact_us, faq_page, terms_conditions, terms_of_use, 
    track_orders, shipping_policy, return_policy, privacy_policy, edit_address, 
    verify_payment, create_razorpay_order, razorpay_webhook, get_product_data, 
    cancel_razorpay_order, order_success, product_feed_json, submit_review,
    lookup_address_by_phone
)

sitemaps = {
    'static': StaticViewSitemap,
}

urlpatterns = [
    # SEO & Data Feeds
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('product-feed/', product_feed_json, name='product_feed'),

    # Core Navigation & Auth
    path('', home, name='home'),
    path('login/', login_page, name='login'),
    path('signup/', login_page, name='signup'),
    path('logout/', logout_page, name='logout'),
    path('verify-otp/', verify_otp, name='verify_otp'),
    path('post-login/', post_login_redirect, name='post_login'),

    # Product & Catalog
    path('product/<int:id>/', product_detail, name='product_detail'),
    path('shop-now/<int:product_id>/', shop_now, name='shop_now'),
    path('get-product-data/<int:product_id>/', get_product_data, name='get_product_data'),
    path('search/', search, name='search'),

    # Hierarchical Category Routing
    path('category/<str:category_slug>/', category_default, name='category_default'),
    path('category/<str:category_slug>/<str:sub_slug>/', category_products, name='category_products'),
    path('category/<str:category_slug>/<str:sub_slug>/<str:type_slug>/', category_products, name='category_type_products'),

    # Cart & Quantity Management
    path('cart/', cart, name='cart'),
    path('add-to-cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/increase/<str:item_id>/', increase_quantity, name='increase_quantity'),
    path('cart/decrease/<str:item_id>/', decrease_quantity, name='decrease_quantity'),

    # Checkout & Address
    path('checkout/', checkout, name='checkout'),
    path('place-order/', place_order, name='place_order'),
    path('add-address/', add_address, name='add_address'),
    path('my-addresses/', my_addresses, name='my_addresses'),
    path('address/edit/<int:id>/', edit_address, name='edit_address'),
    path('delete-address/<int:id>/', delete_address, name='delete_address'),
    path('api/lookup-address/', lookup_address_by_phone, name='lookup_address_by_phone'),

    # Order Management & Payment Processing
    path('my-orders/', my_orders, name='my_orders'),
    path('track-orders/', track_orders, name='track_orders'),
    path('order-success/<int:order_id>/', order_success, name='order_success'),
    path('cancel-order/<int:order_id>/', cancel_order, name='cancel_order'),
    path('create-razorpay-order/', create_razorpay_order, name='create_razorpay_order'),
    path('verify-payment/', verify_payment, name='verify_payment'),
    path('cancel-razorpay-order/', cancel_razorpay_order, name='cancel_razorpay_order'),
    path('razorpay/webhook/', razorpay_webhook, name='razorpay_webhook'),

    # Reviews API
    path('api/submit-review/', submit_review, name='submit_review'),

    # Content & Information Pages
    path('about-us/', about_us, name='about_us'),
    path('cheapify-insider/', cheapify_insider, name='insider_page'),
    path('careers/', careers_page, name='careers'),
    path('blog/', blog_list, name='blog_list'),
    path('blog/<slug:slug>/', blog_detail, name='blog_detail'),
    path('site-map/', sitemap_page, name='sitemap'),
    path('corporate-information/', corporate_info, name='corporate_info'),
    path('contact-us/', contact_us, name='contact_us'),
    path('contact/', contact_us),
    path('faq/', faq_page, name='faq'),
    path('terms-and-conditions/', terms_conditions, name='terms'),
    path('terms-of-use/', terms_of_use, name='terms_use'),
    path('shipping-policy/', shipping_policy, name='shipping_policy'),
    path('shipping/', shipping_policy),
    path('cancellation-returns/', return_policy, name='return_policy'),
    path('return-policy/', return_policy),
    path('returns/', return_policy),
    path('privacy-policy/', privacy_policy, name='privacy_policy'),
]
