import os
import sys
import shutil
import time
import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

import cloudinary.uploader
from django.core.cache import cache
from app1.models import Product, ProductColor, ProductImage

BASE_DIR = r"d:\New folder (3)\clothing"
PROD_DIR = os.path.join(r"d:\New folder (3)\clothing\myproject", "production_ready_chevron")

TASKS = [
    {
        'id': 42,
        'color': 'Green',
        'dir_name': 'Elite_Chevron_Casual_Shirt_Green_HD',
        'shade': 'Olive Sage Khaki Green',
        'files': {
            'main': os.path.join(PROD_DIR, 'Green_1_Front_Main.jpg'),
            'side': os.path.join(PROD_DIR, 'Green_2_Side_View.jpg'),
            'full_body': os.path.join(PROD_DIR, 'Green_3_Full_Body.jpg'),
            'detail': os.path.join(PROD_DIR, 'Green_4_Detail_Texture.jpg'),
        }
    },
    {
        'id': 43,
        'color': 'Gray',
        'dir_name': 'Elite_Chevron_Casual_Shirt_Gray_HD',
        'shade': 'Slate Charcoal Heather Gray',
        'files': {
            'main': os.path.join(PROD_DIR, 'Gray_1_Front_Main.jpg'),
            'side': os.path.join(PROD_DIR, 'Gray_2_Side_View.jpg'),
            'full_body': os.path.join(PROD_DIR, 'Gray_3_Full_Body.jpg'),
            'detail': os.path.join(PROD_DIR, 'Gray_4_Detail_Texture.jpg'),
        }
    },
    {
        'id': 44,
        'color': 'Yellow',
        'dir_name': 'Elite_Chevron_Casual_Shirt_Yellow_HD',
        'shade': 'Mustard Ochre Honey Yellow',
        'files': {
            'main': os.path.join(PROD_DIR, 'Yellow_1_Front_Main.jpg'),
            'side': os.path.join(PROD_DIR, 'Yellow_2_Side_View.jpg'),
            'full_body': os.path.join(PROD_DIR, 'Yellow_3_Full_Body.jpg'),
            'detail': os.path.join(PROD_DIR, 'Yellow_4_Detail_Texture.jpg'),
        }
    },
    {
        'id': 39,
        'color': 'Brown',
        'dir_name': 'Elite_Chevron_Casual_Shirt_Brown_HD',
        'shade': 'Warm Mocha Tan Brown',
        'files': {
            'main': os.path.join(BASE_DIR, 'Elite_Chevron_Casual_Shirt_Brown_HD', '1_Front_Main_Brown.jpg'),
            'side': os.path.join(BASE_DIR, 'Elite_Chevron_Casual_Shirt_Brown_HD', '2_Side_View_Brown.jpg'),
            'full_body': os.path.join(BASE_DIR, 'Elite_Chevron_Casual_Shirt_Brown_HD', '3_Full_Body_Brown.jpg'),
            'detail': os.path.join(PROD_DIR, 'Brown_4_Detail_Texture.jpg'),
        }
    },
    {
        'id': 40,
        'color': 'Black',
        'dir_name': 'Elite_Chevron_Casual_Shirt_Black_HD',
        'shade': 'Midnight Jet Obsidian Black',
        'files': {
            'main': os.path.join(BASE_DIR, 'Elite_Chevron_Casual_Shirt_Black_HD', '1_Front_Main_Black.jpg'),
            'side': os.path.join(BASE_DIR, 'Elite_Chevron_Casual_Shirt_Black_HD', '2_Side_View_Black.jpg'),
            'full_body': os.path.join(BASE_DIR, 'Elite_Chevron_Casual_Shirt_Black_HD', '3_Full_Body_Black.jpg'),
            'detail': os.path.join(PROD_DIR, 'Black_4_Detail_Texture.jpg'),
        }
    },
]

def update_all():
    print("=" * 75)
    print("APPLYING FLAWLESS PRODUCTION CHEVRON PHOTOSHOOTS (100% UNIFORM COLOR COVERAGE)")
    print("=" * 75)

    for task in TASKS:
        pid = task['id']
        color = task['color']
        shade = task['shade']
        hd_dir = os.path.join(BASE_DIR, task['dir_name'])
        os.makedirs(hd_dir, exist_ok=True)

        print(f"\n>>> Updating Product {pid}: {color} ({shade})...")

        # 1. Copy files to HD directory
        file_map = {
            'main': f"1_Front_Main_{color}.jpg",
            'side': f"2_Side_View_{color}.jpg",
            'full_body': f"3_Full_Body_{color}.jpg",
            'detail': f"4_Detail_Texture_{color}.jpg",
        }

        for k, fname in file_map.items():
            src = task['files'][k]
            dst = os.path.join(hd_dir, fname)
            if src != dst:
                shutil.copy2(src, dst)
            print(f"  [OK] Saved local HD: {fname}")

        # 2. Upload to Cloudinary
        uploaded = {}
        for key, fname in file_map.items():
            fpath = os.path.join(hd_dir, fname)
            target_folder = 'villi-shop/products' if key == 'main' else 'villi-shop/product_gallery'
            print(f"  Uploading {fname} -> Cloudinary [{target_folder}]...")
            res = cloudinary.uploader.upload(
                fpath,
                folder=target_folder,
                resource_type='image'
            )
            pub_id = res['public_id']
            url = res['secure_url']
            uploaded[key] = {
                'public_id': pub_id,
                'url': url
            }
            print(f"    OK -> {pub_id}")
            time.sleep(0.3)

        # 3. Update Database
        product = Product.objects.get(id=pid)
        product.image = uploaded['main']['public_id']
        product.fabric = "100% Premium Combed Cotton (Textured Micro-Chevron Jacquard)"
        product.fit = "Modern Tailored Fit (Relaxed Breathable Silhouette)"
        product.care_instructions = (
            "Wash Care: Machine wash cold on gentle cycle, inside out with like fabrics to preserve the rich chevron texture.\n\n"
            "Bleach: Do not bleach.\n\n"
            "Dry: Line dry in shade; avoid harsh direct midday sunlight.\n\n"
            "Iron: Warm steam iron on reverse side; effortless wrinkle-resistant drape."
        )
        product.additional_info = (
            f"Signature micro-chevron jacquard weave engineered for superior tactile depth and all-day breathability in {shade}. "
            "Features a relaxed spread Cuban collar with metallic rivet details, contrast obsidian black snap buttons with silver chrome outer rims, "
            "and a tailored curved hemline designed for versatile tucked or untucked styling."
        )
        product.description = (
            f"Elevate your signature style with the Elite Chevron Casual Shirt in {shade}. "
            "Crafted from high-density, ultra-soft combed cotton woven into an intricate micro-chevron jacquard herringbone pattern, "
            "this shirt delivers exceptional tactile depth and natural all-season breathability. "
            "Designed with a flattering tailored silhouette that sits comfortably on the shoulders and chest while allowing effortless movement. "
            "Finished with distinctive black and polished chrome rim buttons, versatile spread Cuban collar, and rolled cuffs. "
            "Whether paired with sleek black trousers for smart evenings or casual denim for daytime outings, "
            "its wrinkle-resilient architecture ensures an impeccably composed look."
        )
        product.save(update_fields=['image', 'fabric', 'fit', 'care_instructions', 'additional_info', 'description'])
        print(f"  [OK] Updated Product {pid} main fields.")

        # 4. Update ProductColor variant
        variant = ProductColor.objects.filter(product=product, color_name__iexact=color).first()
        if variant:
            variant.color_image = uploaded['main']['public_id']
            variant.save(update_fields=['color_image'])
            print(f"  [OK] Updated ProductColor({color}) color_image.")

        # 5. Update ProductImage gallery
        product.images.all().delete()
        for gkey in ['main', 'side', 'full_body', 'detail']:
            ProductImage.objects.create(
                product=product,
                image=uploaded[gkey]['public_id']
            )
        print("  [OK] Replaced gallery with 4 verified HD angles.")

    print("\n" + "=" * 75)
    print("Clearing Django Cache...")
    cache.clear()
    print("Cache successfully cleared!")
    print("=" * 75)

if __name__ == '__main__':
    update_all()
