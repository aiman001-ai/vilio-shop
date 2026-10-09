import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

import cloudinary.uploader
from django.core.cache import cache
from app1.models import Product, ProductColor, ProductImage

HD_DIR = r'd:\New folder (3)\clothing\The_Dot_Matrix_Casual_TShirt_Red_HD'
os.makedirs(HD_DIR, exist_ok=True)

source_images = {
    '1_Front_Main_Dot_Matrix_TShirt_Red_HD.jpg': r'C:\Users\INDIAN COMPUTER\.gemini\antigravity-ide\brain\6ef495ca-e327-46dd-830d-3010eb6b6622\dot_matrix_red_front_1791565812835.jpg',
    '2_Editorial_Portrait_Dot_Matrix_TShirt_Red_HD.jpg': r'd:\New folder (3)\clothing\myproject\test_model_upper_crop.jpg',
    '3_Back_View_Artwork_Dot_Matrix_TShirt_Red_HD.jpg': r'd:\New folder (3)\clothing\myproject\test_back_enhanced.jpg',
    '4_Closeup_Texture_Dot_Matrix_TShirt_Red_HD.jpg': r'd:\New folder (3)\clothing\myproject\scripts\archive_assets\generated_missing_angles\pid_75\angle_4_detail_macro.jpg',
}

print("1. Copying HD photoshoot images to folder:", HD_DIR)
for dest_name, src_path in source_images.items():
    dest_path = os.path.join(HD_DIR, dest_name)
    shutil.copy2(src_path, dest_path)
    print(f"  -> Saved {dest_name} ({os.path.getsize(dest_path)} bytes)")

images_to_upload = [
    ('main', os.path.join(HD_DIR, '1_Front_Main_Dot_Matrix_TShirt_Red_HD.jpg'), 'villi-shop/products'),
    ('portrait', os.path.join(HD_DIR, '2_Editorial_Portrait_Dot_Matrix_TShirt_Red_HD.jpg'), 'villi-shop/product_gallery'),
    ('back', os.path.join(HD_DIR, '3_Back_View_Artwork_Dot_Matrix_TShirt_Red_HD.jpg'), 'villi-shop/product_gallery'),
    ('detail', os.path.join(HD_DIR, '4_Closeup_Texture_Dot_Matrix_TShirt_Red_HD.jpg'), 'villi-shop/product_gallery'),
]

def apply_photoshoot():
    product = Product.objects.get(id=75)
    print(f"\nTarget Product: ID {product.id} - {product.name} (Red)")

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

    # 1. Update Product main image
    product.image = uploaded['main']['public_id']
    product.save(update_fields=['image'])
    print(f"Updated Product.image -> {product.image}")

    # 2. Update Color Variant (Red)
    variant = ProductColor.objects.filter(product=product, color_name__iexact='Red').first()
    if variant:
        variant.color_image = uploaded['main']['public_id']
        variant.save(update_fields=['color_image'])
        print(f"Updated ProductColor(Red).color_image -> {variant.color_image}")

    # 3. Update Gallery
    product.images.all().delete()
    for key in ['main', 'portrait', 'back', 'detail']:
        gallery_item = ProductImage.objects.create(
            product=product,
            image=uploaded[key]['public_id']
        )
        print(f"Added gallery image ID {gallery_item.id}: {uploaded[key]['public_id']}")

    cache.clear()
    print("\nSUCCESS: Photoshoot successfully applied to Product ID 75 (The Dot-Matrix Casual T-Shirt - Red) in Cloudinary & Django DB!")

if __name__ == '__main__':
    apply_photoshoot()
