import os
import sys
import shutil
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

import cloudinary.uploader
from django.core.cache import cache
from app1.models import Product, ProductColor, ColorSizeStock, ProductImage

BASE_DIR = r"d:\New folder (3)\clothing"
ORANGE_DIR = os.path.join(BASE_DIR, "Elite_Chevron_Casual_Shirt_Orange_HD")
BACKUP_DIR = os.path.join(BASE_DIR, "Elite_Chevron_Casual_Shirt_Orange_HD_backup")

BRAIN_DIR = r"C:\Users\INDIAN COMPUTER\.gemini\antigravity-ide\brain\b00cf47a-d1cd-4e18-87fa-ba87ee46c2bf"

SOURCE_FILES = {
    '1_Front_Main_Orange.jpg': os.path.join(BRAIN_DIR, 'chevron_orange_front_1791476478495.jpg'),
    '2_Side_View_Orange.jpg': os.path.join(BRAIN_DIR, 'chevron_orange_side_1791476521719.jpg'),
    '3_Full_Body_Orange.jpg': os.path.join(BRAIN_DIR, 'chevron_orange_back_1791476546920.jpg'),
    '4_Detail_Texture_Orange.jpg': os.path.join(BRAIN_DIR, 'chevron_orange_detail_1791476567597.jpg'),
}

def update_orange_chevron():
    print("=" * 70)
    print("UPDATING ELITE CHEVRON CASUAL SHIRT (ORANGE - PRODUCT ID 41)")
    print("=" * 70)
    
    # 1. Backup old files
    os.makedirs(BACKUP_DIR, exist_ok=True)
    for fname in os.listdir(ORANGE_DIR):
        old_f = os.path.join(ORANGE_DIR, fname)
        if os.path.isfile(old_f):
            shutil.copy2(old_f, os.path.join(BACKUP_DIR, fname))
    print(f"Backed up previous files to: {BACKUP_DIR}")
    
    # 2. Copy new generated AI photoshoot images into HD folder
    for target_name, src_path in SOURCE_FILES.items():
        if not os.path.exists(src_path):
            raise FileNotFoundError(f"Source file not found: {src_path}")
        dest_path = os.path.join(ORANGE_DIR, target_name)
        shutil.copy2(src_path, dest_path)
        print(f"Copied {os.path.basename(src_path)} -> {dest_path}")
        
    # 3. Upload all 4 angles to Cloudinary
    uploaded = {}
    angle_config = [
        ('main', '1_Front_Main_Orange.jpg', 'villi-shop/products'),
        ('side', '2_Side_View_Orange.jpg', 'villi-shop/product_gallery'),
        ('full_body', '3_Full_Body_Orange.jpg', 'villi-shop/product_gallery'),
        ('detail', '4_Detail_Texture_Orange.jpg', 'villi-shop/product_gallery'),
    ]
    
    for key, fname, target_folder in angle_config:
        fpath = os.path.join(ORANGE_DIR, fname)
        print(f"\nUploading {fname} to Cloudinary folder [{target_folder}]...")
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
        print(f"  -> Uploaded successfully: {pub_id}")
        print(f"  -> URL: {url}")
        time.sleep(0.3)
        
    # 4. Update Database: Product ID 41
    product = Product.objects.get(id=41)
    product.image = uploaded['main']['public_id']
    
    # Ensure descriptions and fabric specs are rich and accurate
    product.fabric = "100% Premium Combed Cotton (Textured Micro-Chevron Jacquard)"
    product.fit = "Modern Tailored Fit (Relaxed Breathable Silhouette)"
    product.care_instructions = (
        "Wash Care: Machine wash cold on gentle cycle, inside out with like fabrics to preserve the rich chevron texture.\n\n"
        "Bleach: Do not bleach.\n\n"
        "Dry: Line dry in shade; avoid harsh direct midday sunlight.\n\n"
        "Iron: Warm steam iron on reverse side; effortless wrinkle-resistant drape."
    )
    product.additional_info = (
        "Signature micro-chevron jacquard weave engineered for superior tactile depth and all-day breathability. "
        "Features a relaxed spread Cuban collar with metallic rivet details, contrast obsidian black snap buttons with silver chrome outer rims, "
        "and a tailored curved hemline designed for versatile tucked or untucked styling."
    )
    product.description = (
        "Elevate your signature style with the Elite Chevron Casual Shirt in Terracotta Rust Orange. "
        "Crafted from high-density, ultra-soft combed cotton woven into an intricate micro-chevron jacquard herringbone pattern, "
        "this shirt delivers exceptional tactile depth and natural all-season breathability. "
        "Designed with a flattering tailored silhouette that sits comfortably on the shoulders and chest while allowing effortless movement. "
        "Finished with distinctive black and polished chrome rim buttons, versatile spread Cuban collar, and rolled cuffs. "
        "Whether paired with sleek black trousers for smart evenings or casual denim for daytime outings, "
        "its wrinkle-resilient architecture ensures an impeccably composed look."
    )
    product.save(update_fields=[
        'image', 'fabric', 'fit', 'care_instructions', 'additional_info', 'description'
    ])
    print(f"\n[OK] Updated Product {product.id} main image and details.")
    
    # 5. Update ProductColor variant for Orange
    variant = ProductColor.objects.filter(product=product, color_name__iexact='Orange').first()
    if variant:
        variant.color_image = uploaded['main']['public_id']
        variant.save(update_fields=['color_image'])
        print(f"[OK] Updated ProductColor(Orange) color_image -> {variant.color_image}")
        
    # 6. Replace gallery images with all 4 angles
    old_count = product.images.count()
    product.images.all().delete()
    print(f"[OK] Deleted {old_count} old gallery images.")
    
    for key, fname, _ in angle_config:
        ProductImage.objects.create(
            product=product,
            image=uploaded[key]['public_id']
        )
    print(f"[OK] Added 4 fresh HD photoshoot angles to product gallery.")
    
    # 7. Flush Django Cache
    cache.clear()
    print("[OK] Django cache flushed successfully.")
    
    print("\n" + "=" * 70)
    print("ORANGE CHEVRON CASUAL SHIRT UPDATE COMPLETE!")
    print("=" * 70)
    for key, data in uploaded.items():
        print(f"  • {key.upper()}: {data['url']}")

if __name__ == '__main__':
    update_orange_chevron()
