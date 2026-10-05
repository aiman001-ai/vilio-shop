import os
import sys
import shutil

sys.path.insert(0, os.getcwd())
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

import cloudinary.uploader
from django.core.cache import cache
from app1.models import Product, ProductColor, ProductImage

HD_DIR = r'd:\New folder (3)\clothing\LA_Edition_Tee_Bottle_Green_HD'

images_to_upload = [
    ('main', os.path.join(HD_DIR, '1_Front_Main_LA_Tee_Bottle_Green_HD.jpg'), 'villi-shop/products'),
    ('full_body', os.path.join(HD_DIR, '2_Full_Body_Model_LA_Tee_Bottle_Green_HD.jpg'), 'villi-shop/product_gallery'),
    ('back', os.path.join(HD_DIR, '3_Back_Profile_LA_Tee_Bottle_Green_HD.jpg'), 'villi-shop/product_gallery'),
    ('detail', os.path.join(HD_DIR, '4_Closeup_Texture_LA_Tee_Bottle_Green_HD.jpg'), 'villi-shop/product_gallery'),
]

def apply_photoshoot_and_specs():
    product = Product.objects.get(id=82)
    print(f"\nTarget Product: ID {product.id} - {product.name}")
    print(f"Current Fabric: {product.fabric}")
    print(f"Current Colors: {[c.color_name for c in product.color_variants.all()]}")

    uploaded = {}
    for key, path, folder in images_to_upload:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing image file: {path}")
        print(f"Uploading {key} ({os.path.basename(path)}) to Cloudinary [{folder}]...")
        res = cloudinary.uploader.upload(
            path,
            folder=folder,
            resource_type='image'
        )
        public_id = res['public_id']
        uploaded[key] = {
            'public_id': public_id,
            'url': res['secure_url']
        }
        print(f"  -> Uploaded: {public_id}")

    # 1. Update Product main image & Specs
    product.image = uploaded['main']['public_id']
    product.fabric = "240 GSM Heavyweight Combed Cotton Blend (Soft-touch, breathable & structured drop-shoulder drape)"[:100]
    product.fit = "Relaxed / Oversized Drop Shoulder (Roomy boxy cut with clean drape)"[:100]
    product.additional_info = (
        "• Color Profile: Deep Bottle Green (Pine Green) with rich, cool-toned undertones\n"
        "• Fabric Spec: 240+ GSM Super Combed Compact Cotton Blend\n"
        "• Knit Finish: Single jersey knit with bio-polish & silicon softening\n"
        "• Graphic Print: Crisp white high-density screen print on chest & back\n"
        "• Construction: Reinforced ribbed crew neck & drop-shoulder styling"
    )
    product.save()
    print(f"\n[OK] Updated Product {product.id} image, fabric, fit, and additional_info.")

    # 2. Update Color Variant from 'Green' to 'Bottle Green'
    variant = product.color_variants.filter(color_name__iexact='Green').first()
    if not variant:
        variant = product.color_variants.first()
    
    if variant:
        old_color_name = variant.color_name
        variant.color_name = 'Bottle Green'
        variant.color_image = uploaded['main']['public_id']
        variant.save(update_fields=['color_name', 'color_image'])
        print(f"[OK] Updated ProductColor {variant.id}: '{old_color_name}' -> '{variant.color_name}'")
        print(f"[OK] Updated ProductColor.color_image -> {variant.color_image}")

    # 3. Update Gallery Images
    product.images.all().delete()
    for key in ['main', 'full_body', 'back', 'detail']:
        gallery_item = ProductImage.objects.create(
            product=product,
            image=uploaded[key]['public_id']
        )
        print(f"[OK] Added gallery image ID {gallery_item.id}: {uploaded[key]['public_id']}")

    # 4. Clear Django cache to ensure frontend renders immediately
    cache.clear()
    print("[OK] Cleared Django cache.")
    print(f"\nSUCCESS: Successfully updated Product ID 82 to 'Bottle Green' with new fabric specs and Cloudinary HD assets!")

if __name__ == '__main__':
    apply_photoshoot_and_specs()
