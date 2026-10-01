import os
import django
import shutil

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

import cloudinary.uploader
from app1.models import Product, ProductColor, ProductImage

BRAIN_DIR = r"C:\Users\INDIAN COMPUTER\.gemini\antigravity-ide\brain\3e789620-1dc3-4f23-8904-98af6e166973"
HD_DIR = r"d:\New folder (3)\clothing\LA_Edition_Tee_White_HD"
os.makedirs(HD_DIR, exist_ok=True)

source_images = [
    ('main', os.path.join(BRAIN_DIR, 'la_white_main_1790890602332.jpg'), '1_Front_Main_LA_Tee_White_HD.jpg', 'villi-shop/products'),
    ('full_body', os.path.join(BRAIN_DIR, 'la_white_full_1790890617384.jpg'), '2_Full_Body_Model_LA_Tee_White_HD.jpg', 'villi-shop/product_gallery'),
    ('side', os.path.join(BRAIN_DIR, 'la_white_side_1790890633772.jpg'), '3_Back_Profile_LA_Tee_White_HD.jpg', 'villi-shop/product_gallery'),
    ('detail', os.path.join(BRAIN_DIR, 'la_white_detail_1790890657319.jpg'), '4_Closeup_Texture_LA_Tee_White_HD.jpg', 'villi-shop/product_gallery'),
]

def apply_white_photoshoot():
    product = Product.objects.get(id=79)
    print(f"Target Product: ID {product.id} - {product.name} (White)")

    uploaded = {}
    for key, src_path, dest_filename, folder in source_images:
        dest_path = os.path.join(HD_DIR, dest_filename)
        shutil.copy2(src_path, dest_path)
        print(f"Copied {dest_filename} to {HD_DIR}")

        print(f"Uploading {key} ({dest_filename}) to Cloudinary [{folder}]...")
        res = cloudinary.uploader.upload(
            dest_path,
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
    print(f"Updated Product(79).image -> {product.image}")

    # 2. Update Color Variant (White)
    variant = ProductColor.objects.filter(product=product, color_name__iexact='White').first()
    if variant:
        variant.color_image = uploaded['main']['public_id']
        variant.save(update_fields=['color_image'])
        print(f"Updated ProductColor(White).color_image -> {variant.color_image}")

    # 3. Update Gallery
    product.images.all().delete()
    for key in ['main', 'full_body', 'side', 'detail']:
        gallery_item = ProductImage.objects.create(
            product=product,
            image=uploaded[key]['public_id']
        )
        print(f"Added gallery image ID {gallery_item.id}: {uploaded[key]['public_id']}")

    print("\nSUCCESS: Photoshoot successfully applied to Product ID 79 (White) in Cloudinary & Django DB!")

if __name__ == '__main__':
    apply_white_photoshoot()
