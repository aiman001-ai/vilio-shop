import os
import sys

sys.path.insert(0, os.getcwd())
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

import cloudinary.uploader
from django.core.cache import cache
from app1.models import Product, ProductColor, ProductImage

JOGGER_CONFIGS = [
    {
        'id': 86,
        'color_name': 'Red',
        'dir': r'd:\New folder (3)\clothing\Ankle_Zip_Performance_Joggers_Red_HD',
        'main': '1_Front_Main_Red.jpg',
        'gallery': [
            '2_Full_Editorial_Red.jpg',
            '2_Side_Profile_Red.jpg',
            '3_Back_View_Red.jpg',
            '4_Detail_Macro_Red.jpg',
        ]
    },
    {
        'id': 87,
        'color_name': 'Green',
        'dir': r'd:\New folder (3)\clothing\Ankle_Zip_Performance_Joggers_Green_HD',
        'main': '1_Front_Main_Green.jpg',
        'gallery': [
            '2_Full_Editorial_Green.jpg',
            '2_Side_Profile_Green.jpg',
            '3_Back_View_Green.jpg',
            '4_Detail_Macro_Green.jpg',
        ]
    },
    {
        'id': 88,
        'color_name': 'White',
        'dir': r'd:\New folder (3)\clothing\Ankle_Zip_Performance_Joggers_White_HD',
        'main': '1_Front_Main_White.jpg',
        'gallery': [
            '2_Full_Editorial_White.jpg',
            '2_Side_Profile_White.jpg',
            '3_Back_View_White.jpg',
            '4_Detail_Macro_White.jpg',
        ]
    },
    {
        'id': 90,
        'color_name': 'Black',
        'dir': r'd:\New folder (3)\clothing\Ankle_Zip_Performance_Joggers_Black_HD',
        'main': '1_Front_Main_Black.jpg',
        'gallery': [
            '2_Full_Editorial_Black.jpg',
            '2_Side_Profile_Black.jpg',
            '3_Back_View_Black.jpg',
            '4_Detail_Macro_Black.jpg',
        ]
    },
]

def sync_all_joggers():
    for cfg in JOGGER_CONFIGS:
        product_id = cfg['id']
        color_name = cfg['color_name']
        folder_dir = cfg['dir']
        
        product = Product.objects.get(id=product_id)
        print(f"\n==========================================")
        print(f"Syncing Jogger ID {product.id}: {product.name} ({color_name})")
        print(f"==========================================")
        
        # 1. Upload Main image
        main_path = os.path.join(folder_dir, cfg['main'])
        print(f"Uploading main: {cfg['main']} ...")
        res_main = cloudinary.uploader.upload(main_path, folder='villi-shop/products', resource_type='image')
        main_pub_id = res_main['public_id']
        print(f"  -> Uploaded main: {main_pub_id}")
        
        # 2. Upload Gallery images
        gallery_pub_ids = []
        for g_file in cfg['gallery']:
            g_path = os.path.join(folder_dir, g_file)
            print(f"Uploading gallery angle: {g_file} ...")
            res_g = cloudinary.uploader.upload(g_path, folder='villi-shop/product_gallery', resource_type='image')
            gallery_pub_ids.append(res_g['public_id'])
            print(f"  -> Uploaded gallery: {res_g['public_id']}")
            
        # 3. Update Product model
        product.image = main_pub_id
        product.save(update_fields=['image'])
        print(f"  [OK] Product.image updated -> {product.image}")
        
        # 4. Update ProductColor model
        variant = ProductColor.objects.filter(product=product, color_name__iexact=color_name).first()
        if variant:
            variant.color_image = main_pub_id
            variant.save(update_fields=['color_image'])
            print(f"  [OK] ProductColor({color_name}).color_image updated -> {variant.color_image}")
        else:
            print(f"  [NOTE] No variant found with color_name='{color_name}'")
            
        # 5. Clear and create Gallery Images
        product.images.all().delete()
        for g_pid in gallery_pub_ids:
            g_item = ProductImage.objects.create(product=product, image=g_pid)
            print(f"  [OK] Created ProductImage ID {g_item.id}: {g_pid}")
            
    cache.clear()
    print("\n==========================================")
    print("ALL ANKLE-ZIP PERFORMANCE JOGGERS SUCCESSFULLY SYNCED TO CLOUDINARY & DATABASE!")

if __name__ == '__main__':
    sync_all_joggers()
