import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

import cloudinary.uploader
from django.core.cache import cache
from app1.models import Product, ProductColor, ColorSizeStock, ProductImage

BASE_DIR = r'd:\New folder (3)\clothing'

CHEVRON_PRODUCTS = [
    {
        'id': 39,
        'color_name': 'Brown',
        'shade_desc': 'Warm Mocha Tan',
        'dir_name': 'Elite_Chevron_Casual_Shirt_Brown_HD',
        'files': {
            'main': '1_Front_Main_Brown.jpg',
            'side': '2_Side_View_Brown.jpg',
            'full_body': '3_Full_Body_Brown.jpg',
            'detail': '4_Detail_Texture_Brown.jpg',
        }
    },
    {
        'id': 40,
        'color_name': 'Black',
        'shade_desc': 'Midnight Jet Black',
        'dir_name': 'Elite_Chevron_Casual_Shirt_Black_HD',
        'files': {
            'main': '1_Front_Main_Black.jpg',
            'side': '2_Side_View_Black.jpg',
            'full_body': '3_Full_Body_Black.jpg',
            'detail': '4_Detail_Texture_Black.jpg',
        }
    },
    {
        'id': 41,
        'color_name': 'Orange',
        'shade_desc': 'Terracotta Rust',
        'dir_name': 'Elite_Chevron_Casual_Shirt_Orange_HD',
        'files': {
            'main': '1_Front_Main_Orange.jpg',
            'side': '2_Side_View_Orange.jpg',
            'full_body': '3_Full_Body_Orange.jpg',
            'detail': '4_Detail_Texture_Orange.jpg',
        }
    },
    {
        'id': 42,
        'color_name': 'Green',
        'shade_desc': 'Olive Sage Green',
        'dir_name': 'Elite_Chevron_Casual_Shirt_Green_HD',
        'files': {
            'main': '1_Front_Main_Green.jpg',
            'side': '2_Side_View_Green.jpg',
            'full_body': '3_Full_Body_Green.jpg',
            'detail': '4_Detail_Texture_Green.jpg',
        }
    },
    {
        'id': 43,
        'color_name': 'Gray',
        'shade_desc': 'Slate Charcoal Gray',
        'dir_name': 'Elite_Chevron_Casual_Shirt_Gray_HD',
        'files': {
            'main': '1_Front_Main_Gray.jpg',
            'side': '2_Side_View_Gray.jpg',
            'full_body': '3_Full_Body_Gray.jpg',
            'detail': '4_Detail_Texture_Gray.jpg',
        }
    },
    {
        'id': 44,
        'color_name': 'Yellow',
        'shade_desc': 'Mustard Ochre Yellow',
        'dir_name': 'Elite_Chevron_Casual_Shirt_Yellow_HD',
        'files': {
            'main': '1_Front_Main_Yellow.jpg',
            'side': '2_Side_View_Yellow.jpg',
            'full_body': '3_Full_Body_Yellow.jpg',
            'detail': '4_Detail_Texture_Yellow.jpg',
        }
    },
]

FABRIC_TEXT = "100% Premium Combed Cotton (Textured Micro-Chevron Jacquard)"
FIT_TEXT = "Modern Tailored Fit (Relaxed Breathable Silhouette)"
CARE_TEXT = (
    "Wash Care: Machine wash cold on gentle cycle, inside out with like fabrics to preserve the rich chevron texture.\n\n"
    "Bleach: Do not bleach.\n\n"
    "Dry: Line dry in shade; avoid harsh direct midday sunlight.\n\n"
    "Iron: Warm steam iron on reverse side; effortless wrinkle-resistant drape."
)
ADDITIONAL_INFO_TEXT = (
    "Signature micro-chevron jacquard weave engineered for superior tactile depth and all-day breathability. "
    "Features a reinforced spread collar architecture that stays sharp, premium matte pearlized contrast buttons, "
    "and a tailored curved hemline designed for both tucked and untucked styling."
)
DESCRIPTION_TEXT = (
    "Elevate your signature style with the Elite Chevron Casual Shirt. "
    "Crafted from high-density, ultra-soft combed cotton woven into an intricate micro-chevron jacquard pattern, "
    "this shirt delivers exceptional tactile depth and natural all-season breathability. "
    "Designed with a flattering tailored silhouette that sits comfortably on the shoulders and chest while allowing effortless movement. "
    "Whether paired with crisp tailored trousers for business-casual settings or relaxed denim for weekend evenings, "
    "its wrinkle-resilient architecture ensures you look sharp and composed from morning to night."
)

SIZE_STOCKS = {
    'S': 4,
    'M': 6,
    'L': 6,
    'XL': 5,
    '2XL': 3
}

def apply_all_photoshoots():
    print("=" * 70)
    print("STARTING COMPLETE CLOUDINARY UPLOAD & DB UPDATE FOR ALL CHEVRON SHIRTS")
    print("=" * 70)
    
    overall_results = []
    
    for item in CHEVRON_PRODUCTS:
        pid = item['id']
        color = item['color_name']
        shade = item['shade_desc']
        cdir = os.path.join(BASE_DIR, item['dir_name'])
        
        print(f"\n>>> Processing Product ID {pid} - {color} ({shade})")
        print(f"    Source directory: {cdir}")
        
        product = Product.objects.get(id=pid)
        
        uploaded = {}
        for key, fname in item['files'].items():
            fpath = os.path.join(cdir, fname)
            if not os.path.exists(fpath):
                raise FileNotFoundError(f"Missing image file: {fpath}")
            
            target_folder = 'villi-shop/products' if key == 'main' else 'villi-shop/product_gallery'
            print(f"    Uploading {key} ({fname}) -> Cloudinary [{target_folder}]...")
            
            res = cloudinary.uploader.upload(
                fpath,
                folder=target_folder,
                resource_type='image'
            )
            public_id = res['public_id']
            uploaded[key] = {
                'public_id': public_id,
                'url': res['secure_url']
            }
            print(f"      OK -> {public_id}")
            time.sleep(0.3)
        
        # 1. Update Product main image & presentation fields
        product.image = uploaded['main']['public_id']
        product.fabric = FABRIC_TEXT
        product.fit = FIT_TEXT
        product.care_instructions = CARE_TEXT
        product.additional_info = ADDITIONAL_INFO_TEXT
        product.description = DESCRIPTION_TEXT
        product.save(update_fields=[
            'image', 'fabric', 'fit', 'care_instructions', 'additional_info', 'description'
        ])
        print(f"    Updated Product {pid}: image={product.image}, fabric, fit, care, description")
        
        # 2. Update ProductColor variant image
        variant = ProductColor.objects.filter(product=product, color_name__iexact=color).first()
        if variant:
            variant.color_image = uploaded['main']['public_id']
            variant.save(update_fields=['color_image'])
            print(f"    Updated ProductColor({color}).color_image -> {variant.color_image}")
            
            # 3. Update stock levels for sizes
            for s_name, s_qty in SIZE_STOCKS.items():
                size_obj, created = ColorSizeStock.objects.get_or_create(
                    product_color=variant,
                    size_name=s_name,
                    defaults={'stock': s_qty}
                )
                if not created:
                    size_obj.stock = s_qty
                    size_obj.save(update_fields=['stock'])
            print(f"    Updated stock levels: {SIZE_STOCKS}")
        
        # 4. Refresh ProductImage Gallery (all 4 angles)
        old_count = product.images.count()
        product.images.all().delete()
        
        gallery_keys = ['main', 'side', 'full_body', 'detail']
        for gkey in gallery_keys:
            ProductImage.objects.create(
                product=product,
                image=uploaded[gkey]['public_id']
            )
        print(f"    Replaced gallery images ({old_count} old -> 4 new HD angles)")
        
        overall_results.append({
            'id': pid,
            'color': color,
            'main_public_id': uploaded['main']['public_id'],
            'main_url': uploaded['main']['url'],
        })
    
    print("\n" + "=" * 70)
    print("Flushing Django Cache...")
    cache.clear()
    print("Cache successfully cleared!")
    print("=" * 70)
    print("\nSUMMARY OF UPDATES:")
    for res in overall_results:
        print(f"  • ID {res['id']} ({res['color']}): {res['main_url']}")
    print("\nALL 6 CHEVRON PRODUCTS ARE NOW COMPLETELY UPDATED WITH HIGH-END PHOTOSHOOTS & PRESENTATION!")

if __name__ == '__main__':
    apply_all_photoshoots()
