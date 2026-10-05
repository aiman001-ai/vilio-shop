import os
import django

# Dhyaan dein: 'myproject' ko apne folder name se replace karein (jahan settings.py hai)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings') 
django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

def final_fix():
    # 1. Site Object (Live URL ke liye)
    site, _ = Site.objects.get_or_create(id=1)
    site.domain = 'vilio-shop.onrender.com'
    site.name = 'Vilio'
    site.save()

    # 2. Google App (Zabardasti delete karke naya banayein)
    SocialApp.objects.filter(provider='google').delete()
    
    app = SocialApp.objects.create(
        provider='google',
        name='Google Login',
        client_id='1099158331729-o56udcsu7gvsb83vcjas4e23nruv2enq.apps.googleusercontent.com',
        secret='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'
    )
    app.sites.add(site)
    print("✅ Database updated with Live Credentials!")

if __name__ == "__main__":
    final_fix()