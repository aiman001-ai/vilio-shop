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

HD_DIR = r'd:\New folder (3)\clothing\The_Dot_Matrix_Casual_TShirt_White_HD'
os.makedirs(HD_DIR, exist_ok=True)

source_images = {
    '1_Front_Main_Dot_Matrix_TShirt_White_HD.jpg': r'C:\Users\INDIAN COMPUTER\.gemini\antigravity-ide\brain\6ef495ca-e327-46dd-830d-3010eb6b6622\dot_matrix_white_front_1791565396427.jpg',
    '2_Side_View_Dot_Matrix_TShirt_White_HD.jpg': r'C:\Users\INDIAN COMPUTER\.gemini\antigravity-ide\brain\6ef495ca-e327-46dd-830d-3010eb6b6622\dot_matrix_white_side_1791565421444.jpg',
    '3_Back_View_Dot_Matrix_TShirt_White_HD.jpg': r'C:\Users\INDIAN COMPUTER\.gemini\antigravity-ide\brain\6ef495ca-e327-46dd-830d-3010eb6b6622\dot_matrix_white_back_1791565449431.jpg',
    '4_Closeup_Texture_Dot_Matrix_TShirt_White_HD.jpg': r'C:\Users\INDIAN COMPUTER\.gemini\antigravity-ide\brain\6ef495ca-e327-46dd-830d-3010eb6b6622\dot_matrix_white_detail_1791565484088.jpg',
    '5_Full_Body_Dot_Matrix_TShirt_White_HD.jpg': r'C:\Users\INDIAN COMPUTER\.gemini\antigravity-ide\brain\6ef495ca-e327-46dd-830d-3010eb6b6622\dot_matrix_white_fullbody_1791565508672.jpg',
}

print("1. Copying generated HD images to folder:", HD_DIR)
for dest_name, src_path in source_images.items():
    dest_path = os.path.join(HD_DIR, dest_name)
    shutil.copy2(src_path, dest_path)
    print(f"  -> Saved {dest_name} ({os.path.getsize(dest_path)} bytes)")

images_to_upload = [
    ('main', os.path.join(HD_DIR, '1_Front_Main_Dot_Matrix_TShirt_White_HD.jpg'), 'villi-shop/products'),
    ('side', os.path.join(HD_DIR, '2_Side_View_Dot_Matrix_TShirt_White_HD.jpg'), 'villi-shop/product_gallery'),
    ('back', os.path.join(HD_DIR, '3_Back_View_Dot_Matrix_TShirt_White_HD.jpg'), 'villi-shop/product_gallery'),
    ('detail', os.path.join(HD_DIR, '4_Closeup_Texture_Dot_Matrix_TShirt_White_HD.jpg'), 'villi-shop/product_gallery'),
    ('full_body', os.path.join(HD_DIR, '5_Full_Body_Dot_Matrix_TShirt_White_HD.jpg'), 'villi-shop/product_gallery'),
]

def apply_photoshoot():
    product = Product.objects.get(id=74)
    print(f"\nTarget Product: ID {product.id} - {product.name} (White)")

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

    # 2. Update Color Variant (White)
    variant = ProductColor.objects.filter(product=product, color_name__iexact='White').first()
    if variant:
        variant.color_image = uploaded['main']['public_id']
        variant.save(update_fields=['color_image'])
        print(f"Updated ProductColor(White).color_image -> {variant.color_image}")

    # 3. Update Gallery
    product.images.all().delete()
    for key in ['main', 'side', 'back', 'detail', 'full_body']:
        gallery_item = ProductImage.objects.create(
            product=product,
            image=uploaded[key]['public_id']
        )
        print(f"Added gallery image ID {gallery_item.id}: {uploaded[key]['public_id']}")

    cache.clear()
    print("\nSUCCESS: Photoshoot successfully applied to Product ID 74 (The Dot-Matrix Casual T-Shirt - White) in Cloudinary & Django DB!")

if __name__ == '__main__':
    apply_photoshoot()
