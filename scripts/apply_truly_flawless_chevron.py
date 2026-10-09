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
SOURCE_DIR = os.path.join(r"d:\New folder (3)\clothing\myproject", "flawless_chevron_v2")

TASKS = [
    {
        'id': 42,
        'color': 'Green',
        'dir_name': 'Elite_Chevron_Casual_Shirt_Green_HD',
        'shade': 'Olive Sage Green',
    },
    {
        'id': 43,
        'color': 'Gray',
        'dir_name': 'Elite_Chevron_Casual_Shirt_Gray_HD',
        'shade': 'Slate Charcoal Gray',
    },
    {
        'id': 44,
        'color': 'Yellow',
        'dir_name': 'Elite_Chevron_Casual_Shirt_Yellow_HD',
        'shade': 'Mustard Ochre Yellow',
    },
    {
        'id': 39,
        'color': 'Brown',
        'dir_name': 'Elite_Chevron_Casual_Shirt_Brown_HD',
        'shade': 'Warm Mocha Tan Brown',
    },
    {
        'id': 40,
        'color': 'Black',
        'dir_name': 'Elite_Chevron_Casual_Shirt_Black_HD',
        'shade': 'Midnight Jet Black',
    },
]

def apply_all():
    print("=" * 80)
    print("APPLYING TRULY FLAWLESS CHEVRON PHOTOSHOOTS ACROSS ALL 5 COLOR VARIANTS")
    print("=" * 80)

    for task in TASKS:
        pid = task['id']
        color = task['color']
        shade = task['shade']
        hd_dir = os.path.join(BASE_DIR, task['dir_name'])
        os.makedirs(hd_dir, exist_ok=True)

        print(f"\n>>> Processing Product ID {pid}: {color} ({shade})...")

        file_keys = [
            ('main', f"{color}_1_Front_Main.jpg", f"1_Front_Main_{color}.jpg"),
            ('side', f"{color}_2_Side_View.jpg", f"2_Side_View_{color}.jpg"),
            ('full_body', f"{color}_3_Full_Body.jpg", f"3_Full_Body_{color}.jpg"),
            ('detail', f"{color}_4_Detail_Texture.jpg", f"4_Detail_Texture_{color}.jpg"),
        ]

        # 1. Copy files from flawless_chevron_v2 to HD directory
        for key, src_name, dst_name in file_keys:
            src_path = os.path.join(SOURCE_DIR, src_name)
            dst_path = os.path.join(hd_dir, dst_name)
            shutil.copy2(src_path, dst_path)
            print(f"  [OK] Saved HD file: {dst_name}")

        # 2. Upload each file to Cloudinary
        uploaded = {}
        for key, _, dst_name in file_keys:
            fpath = os.path.join(hd_dir, dst_name)
            target_folder = 'villi-shop/products' if key == 'main' else 'villi-shop/product_gallery'
            print(f"  Uploading {dst_name} -> Cloudinary [{target_folder}]...")
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
            print(f"    Uploaded: {pub_id}")
            time.sleep(0.3)

        # 3. Update Product database record
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
        print(f"  [OK] Product {pid} fields updated.")

        # 4. Update ProductColor variant
        variant = ProductColor.objects.filter(product=product, color_name__iexact=color).first()
        if variant:
            variant.color_image = uploaded['main']['public_id']
            variant.save(update_fields=['color_image'])
            print(f"  [OK] ProductColor({color}) color_image updated.")

        # 5. Update ProductImage gallery
        product.images.all().delete()
        for key in ['main', 'side', 'full_body', 'detail']:
            ProductImage.objects.create(
                product=product,
                image=uploaded[key]['public_id']
            )
        print("  [OK] Gallery updated with all 4 HD angles.")

    print("\n" + "=" * 80)
    print("Flushing Django Cache...")
    cache.clear()
    print("Django Cache Flushed Successfully!")
    print("=" * 80)

if __name__ == '__main__':
    apply_all()
