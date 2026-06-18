from django.contrib.sitemaps import Sitemap
from django.urls import reverse
# Agar aapke paas Product, Category, ya Blog ke Models hain toh unhe yahan import karein
# Example:
# from .models import Product, Category, BlogModel 

# 1. Static Pages ke liye Sitemap
class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'

    def get_domain(self, site=None):
        return 'vilio.shop'

    def items(self):
        # Aapke urls.py ke name attributes ki list
        return [
            'home', 'about_us', 'contact_us', 'faq', 'careers', 'insider_page',
            'privacy_policy', 'shipping_policy', 'return_policy', 'terms', 'terms_use',
            'track_orders', 'corporate_info', 'blog_list', 'cart', 'login'
        ]

    def location(self, item):
        return reverse(item)

# 2. Dynamic Blog Pages ke liye (Agar Models use kar rahe hain)
# class BlogSitemap(Sitemap):
#     changefreq = "weekly"
#     priority = 0.7
#
#     def items(self):
#         return BlogModel.objects.filter(status='published') # Apne hisab se filter lagayein
#
#     def location(self, obj):
#         return reverse('blog_detail', kwargs={'slug': obj.slug})

# 3. Dynamic Products ke liye (Agar models use kar rahe hain)
# class ProductSitemap(Sitemap):
#     changefreq = "daily"
#     priority = 1.0
#
#     def items(self):
#         return Product.objects.filter(is_active=True) # Jo live products hain
#
#     def location(self, obj):
#         return reverse('product_detail', kwargs={'id': obj.id})