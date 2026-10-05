import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

import cloudinary.uploader
from app1.models import Product, ProductColor, ProductImage

HD_DIR = r'd:\New folder (3)\clothing\Linen_Blend_Striped_Casual_Shirt_Gray_HD'

images_to_upload = [
    ('main', os.path.join(HD_DIR, '1_Front_Main_Linen_Shirt_Gray_HD.jpg'), 'villi-shop/products'),
    ('full_body', os.path.join(HD_DIR, '2_Full_Body_Model_Linen_Shirt_Gray_HD.jpg'), 'villi-shop/product_gallery'),
    ('side', os.path.join(HD_DIR, '3_Side_Profile_Linen_Shirt_Gray_HD.jpg'), 'villi-shop/product_gallery'),
    ('detail', os.path.join(HD_DIR, '4_Closeup_Texture_Linen_Shirt_Gray_HD.jpg'), 'villi-shop/product_gallery'),
]

def apply_photoshoot():
    product = Product.objects.get(id=62)
    print(f"Target Product: ID {product.id} - {product.name} (Gray)")

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

    # 2. Update Color Variant (Gray)
    variant = ProductColor.objects.filter(product=product, color_name__iexact='Gray').first()
    if variant:
        variant.color_image = uploaded['main']['public_id']
        variant.save(update_fields=['color_image'])
        print(f"Updated ProductColor(Gray).color_image -> {variant.color_image}")

    # 3. Update Gallery
    product.images.all().delete()
    for key in ['main', 'full_body', 'side', 'detail']:
        gallery_item = ProductImage.objects.create(
            product=product,
            image=uploaded[key]['public_id']
        )
        print(f"Added gallery image ID {gallery_item.id}: {uploaded[key]['public_id']}")

    print("\nSUCCESS: Photoshoot successfully applied to Product ID 62 (Gray) in Cloudinary & Django DB!")

if __name__ == '__main__':
    apply_photoshoot()
