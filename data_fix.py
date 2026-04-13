import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings') # Apne project ka naam check kar lena
django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

# 1. Site object theek karein
site, created = Site.objects.get_or_create(id=1, defaults={'domain': 'vilio-shop.onrender.com', 'name': 'Vilio'})
if not created:
    site.domain = 'vilio-shop.onrender.com'
    site.name = 'Vilio'
    site.save()

# 2. Google Social App create karein
# Apni Client ID aur Secret yahan dalo
app, created = SocialApp.objects.get_or_create(
    provider='google',
    name='Google Login',
    defaults={
        'client_id': 'YOUR_GOOGLE_CLIENT_ID', 
        'secret': 'YOUR_GOOGLE_SECRET_KEY',
    }
)
app.sites.add(site)

print("Database fixed: Site and SocialApp created!")