import os
import sys

sys.path.insert(0, os.getcwd())
import django

sys.stdout.reconfigure(encoding='utf-8')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

import cloudinary.uploader
from django.core.cache import cache
from app1.models import Product, ProductImage

BASE_DIR = r"d:\New folder (3)\clothing\myproject\generated_missing_angles"

def upload_and_sync_all():
    subdirs = [d for d in os.listdir(BASE_DIR) if d.startswith("pid_")]
    subdirs.sort(key=lambda x: int(x.split("_")[1]))
    
    total_added = 0
    for sdir in subdirs:
        pid = int(sdir.split("_")[1])
        product = Product.objects.get(id=pid)
        p_path = os.path.join(BASE_DIR, sdir)
        files = sorted(os.listdir(p_path))
        
        print(f"\n==========================================")
        print(f"Product {pid}: {product.name} (Adding {len(files)} new angles)")
        print(f"==========================================")
        
        for fname in files:
            fpath = os.path.join(p_path, fname)
            angle_tag = fname.replace(".jpg", "")
            print(f"  Uploading {fname} to Cloudinary...")
            res = cloudinary.uploader.upload(
                fpath,
                folder='villi-shop/product_gallery',
                public_id=f"p{pid}_{angle_tag}",
                overwrite=True,
                resource_type='image'
            )
            pub_id = res['public_id']
            print(f"  -> Uploaded as: {pub_id}")
            
            # Check if this public_id already exists in gallery
            exists = ProductImage.objects.filter(product=product, image=pub_id).exists()
            if not exists:
                pi = ProductImage.objects.create(product=product, image=pub_id)
                print(f"  [OK] Created ProductImage ID {pi.id}")
                total_added += 1
            else:
                print(f"  [EXISTS] ProductImage already present")
                
    cache.clear()
    print(f"\n==========================================")
    print(f"SUCCESS: Added {total_added} new HD angles to Cloudinary & Django DB!")

if __name__ == '__main__':
    upload_and_sync_all()
