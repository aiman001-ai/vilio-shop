from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Product

class StaticViewSitemap(Sitemap):
    """Sitemap for static marketing, informational, and policy pages."""
    priority = 0.8
    changefreq = 'weekly'

    def get_domain(self, site=None):
        return 'vilio.shop'

    def items(self):
        return [
            'home', 'about_us', 'contact_us', 'faq', 'careers', 'insider_page',
            'privacy_policy', 'shipping_policy', 'return_policy', 'terms', 'terms_use',
            'track_orders', 'corporate_info', 'blog_list', 'cart', 'login'
        ]

    def location(self, item):
        return reverse(item)

class ProductSitemap(Sitemap):
    """Sitemap for active product catalog items."""
    priority = 1.0
    changefreq = 'daily'

    def items(self):
        return Product.objects.filter(is_active=True)

    def location(self, obj):
        return reverse('product_detail', kwargs={'id': obj.id})