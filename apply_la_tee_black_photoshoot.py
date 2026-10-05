import os
import sys
import shutil

sys.path.insert(0, os.getcwd())
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

import cloudinary.uploader
from app1.models import Product, ProductColor, ProductImage

HD_DIR = r'd:\New folder (3)\clothing\LA_Edition_Tee_Black_HD'
os.makedirs(HD_DIR, exist_ok=True)

source_images = {
    '1_Front_Main_LA_Tee_Black_HD.jpg': r'C:\Users\INDIAN COMPUTER\.gemini\antigravity-ide\brain\7ffc6032-b408-485d-9a74-d5c71f0ccf71\la_tee_black_front_1790937835864.jpg',
    '2_Full_Body_Model_LA_Tee_Black_HD.jpg': r'C:\Users\INDIAN COMPUTER\.gemini\antigravity-ide\brain\7ffc6032-b408-485d-9a74-d5c71f0ccf71\la_tee_black_fullbody_1790937858909.jpg',
    '3_Back_Profile_LA_Tee_Black_HD.jpg': r'C:\Users\INDIAN COMPUTER\.gemini\antigravity-ide\brain\7ffc6032-b408-485d-9a74-d5c71f0ccf71\la_tee_black_back_1790937904586.jpg',
    '4_Closeup_Texture_LA_Tee_Black_HD.jpg': r'C:\Users\INDIAN COMPUTER\.gemini\antigravity-ide\brain\7ffc6032-b408-485d-9a74-d5c71f0ccf71\la_tee_black_detail_1790937928450.jpg',
}

print("1. Copying generated HD images to folder:", HD_DIR)
for dest_name, src_path in source_images.items():
    dest_path = os.path.join(HD_DIR, dest_name)
    shutil.copy2(src_path, dest_path)
    print(f"  -> Saved {dest_name} ({os.path.getsize(dest_path)} bytes)")

images_to_upload = [
    ('main', os.path.join(HD_DIR, '1_Front_Main_LA_Tee_Black_HD.jpg'), 'villi-shop/products'),
    ('full_body', os.path.join(HD_DIR, '2_Full_Body_Model_LA_Tee_Black_HD.jpg'), 'villi-shop/product_gallery'),
    ('back', os.path.join(HD_DIR, '3_Back_Profile_LA_Tee_Black_HD.jpg'), 'villi-shop/product_gallery'),
    ('detail', os.path.join(HD_DIR, '4_Closeup_Texture_LA_Tee_Black_HD.jpg'), 'villi-shop/product_gallery'),
]

def apply_photoshoot():
    product = Product.objects.get(id=80)
    print(f"\nTarget Product: ID {product.id} - {product.name} (Black)")

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

    # 2. Update Color Variant (Black)
    variant = ProductColor.objects.filter(product=product, color_name__iexact='Black').first()
    if variant:
        variant.color_image = uploaded['main']['public_id']
        variant.save(update_fields=['color_image'])
        print(f"Updated ProductColor(Black).color_image -> {variant.color_image}")

    # 3. Update Gallery
    product.images.all().delete()
    for key in ['main', 'full_body', 'back', 'detail']:
        gallery_item = ProductImage.objects.create(
            product=product,
            image=uploaded[key]['public_id']
        )
        print(f"Added gallery image ID {gallery_item.id}: {uploaded[key]['public_id']}")

    print("\nSUCCESS: Photoshoot successfully applied to Product ID 80 (Black) in Cloudinary & Django DB!")

if __name__ == '__main__':
    apply_photoshoot()
