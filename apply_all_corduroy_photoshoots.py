import os
import sys

sys.path.insert(0, os.getcwd())
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

import cloudinary.uploader
from django.core.cache import cache
from app1.models import Product, ProductColor, ProductImage

PRODUCTS_CONFIG = [
    {
        'id': 60,
        'color_name': 'White',
        'dir': r'd:\New folder (3)\clothing\Dual_Pocket_Corduroy_Overshirt_White_HD',
        'files': {
            'main': '1_Front_Main_Dual_Pocket_Corduroy_Overshirt_White_HD.jpg',
            'side': '2_Side_View_Dual_Pocket_Corduroy_Overshirt_White_HD.jpg',
            'back': '3_Back_View_Dual_Pocket_Corduroy_Overshirt_White_HD.jpg',
            'full_body': '4_Full_Body_Dual_Pocket_Corduroy_Overshirt_White_HD.jpg',
        }
    },
    {
        'id': 59,
        'color_name': 'Yellow',
        'dir': r'd:\New folder (3)\clothing\Dual_Pocket_Corduroy_Overshirt_Yellow_HD',
        'files': {
            'main': '1_Front_Main_Dual_Pocket_Corduroy_Overshirt_Yellow_HD.jpg',
            'side': '2_Side_View_Dual_Pocket_Corduroy_Overshirt_Yellow_HD.jpg',
            'back': '3_Back_View_Dual_Pocket_Corduroy_Overshirt_Yellow_HD.jpg',
            'full_body': '4_Full_Body_Dual_Pocket_Corduroy_Overshirt_Yellow_HD.jpg',
        }
    },
    {
        'id': 61,
        'color_name': 'Orange',
        'dir': r'd:\New folder (3)\clothing\Dual_Pocket_Corduroy_Overshirt_Orange_HD',
        'files': {
            'main': '1_Front_Main_Dual_Pocket_Corduroy_Overshirt_Orange_HD.jpg',
            'side': '2_Side_View_Dual_Pocket_Corduroy_Overshirt_Orange_HD.jpg',
            'back': '3_Back_View_Dual_Pocket_Corduroy_Overshirt_Orange_HD.jpg',
            'full_body': '4_Full_Body_Dual_Pocket_Corduroy_Overshirt_Orange_HD.jpg',
        }
    },
]

def sync_all():
    for cfg in PRODUCTS_CONFIG:
        product_id = cfg['id']
        color_name = cfg['color_name']
        folder_dir = cfg['dir']
        files = cfg['files']
        
        product = Product.objects.get(id=product_id)
        print(f"\n==========================================")
        print(f"Processing Product ID {product.id}: {product.name} ({color_name})")
        print(f"==========================================")
        
        uploaded = {}
        # Upload main to villi-shop/products
        main_path = os.path.join(folder_dir, files['main'])
        print(f"Uploading main image ({files['main']})...")
        res_main = cloudinary.uploader.upload(main_path, folder='villi-shop/products', resource_type='image')
        uploaded['main'] = res_main['public_id']
        print(f"  -> Uploaded main: {uploaded['main']}")
        
        # Upload gallery angles to villi-shop/product_gallery
        for key in ['side', 'back', 'full_body']:
            img_path = os.path.join(folder_dir, files[key])
            print(f"Uploading {key} ({files[key]})...")
            res = cloudinary.uploader.upload(img_path, folder='villi-shop/product_gallery', resource_type='image')
            uploaded[key] = res['public_id']
            print(f"  -> Uploaded {key}: {uploaded[key]}")
            
        # 1. Update Product.image
        product.image = uploaded['main']
        product.save(update_fields=['image'])
        print(f"  [OK] Product.image updated -> {product.image}")
        
        # 2. Update ProductColor
        variant = ProductColor.objects.filter(product=product, color_name__iexact=color_name).first()
        if variant:
            variant.color_image = uploaded['main']
            variant.save(update_fields=['color_image'])
            print(f"  [OK] ProductColor({color_name}).color_image updated -> {variant.color_image}")
        else:
            print(f"  [NOTE] No variant found with color_name='{color_name}'")
            
        # 3. Update Gallery Images
        product.images.all().delete()
        for key in ['main', 'side', 'back', 'full_body']:
            g_item = ProductImage.objects.create(product=product, image=uploaded[key])
            print(f"  [OK] Added gallery image ID {g_item.id}: {uploaded[key]}")
            
    cache.clear()
    print("\n==========================================")
    print("ALL REMAINING COLORS (White, Yellow, Orange) SUCCESSFULLY SYNCED TO CLOUDINARY & DATABASE!")
    print("==========================================")

if __name__ == '__main__':
    sync_all()
