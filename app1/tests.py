from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from app1.models import Category, SubCategory, Product, ProductColor, ColorSizeStock, Cart, CartItem

class ProductModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Men")
        self.subcategory = SubCategory.objects.create(name="Top Wear", category=self.category)
        self.product = Product.objects.create(
            name="Classic Oxford Cotton Shirt",
            brand="Vilio",
            description="100% breathable Oxford cotton shirt.",
            price=1299,
            original_price=1999,
            category=self.category,
            sub_category=self.subcategory,
            has_variants=True,
            is_active=True
        )

    def test_product_str(self):
        self.assertEqual(str(self.product), "Vilio - Classic Oxford Cotton Shirt")

    def test_product_pricing_properties(self):
        self.assertTrue(self.product.original_price > self.product.price)
        self.assertEqual(self.product.google_price, 1999)

    def test_product_variant_stock(self):
        color = ProductColor.objects.create(
            product=self.product,
            color_name="Navy Blue"
        )
        ColorSizeStock.objects.create(
            product_color=color,
            size_name="M",
            stock=15
        )
        ColorSizeStock.objects.create(
            product_color=color,
            size_name="L",
            stock=10
        )
        self.assertEqual(self.product.total_stock, 25)

class CartAndOrderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testcustomer", password="password123")
        self.category = Category.objects.create(name="Men")
        self.subcategory = SubCategory.objects.create(name="Bottom Wear", category=self.category)
        self.product = Product.objects.create(
            name="Performance Joggers",
            brand="Vilio",
            price=999,
            original_price=1499,
            category=self.category,
            sub_category=self.subcategory,
            is_active=True
        )
        self.cart = Cart.objects.create(user=self.user)

    def test_cart_item_subtotal(self):
        item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2,
            size="M",
            color="Black"
        )
        self.assertEqual(item.subtotal(), 1998)

class CoreViewsTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_homepage_status(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_informational_pages(self):
        urls = ['about_us', 'contact_us', 'faq', 'shipping_policy', 'return_policy', 'terms', 'privacy_policy']
        for url_name in urls:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200)

    def test_product_feed(self):
        response = self.client.get(reverse('product_feed'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "text/tab-separated-values; charset=utf-8")
