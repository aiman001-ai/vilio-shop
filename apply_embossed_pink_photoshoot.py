import os
import shutil
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

import cloudinary.uploader
from django.core.cache import cache
from app1.models import Product, ProductColor, ProductImage

# 1. Setup Pink HD directory
pink_dir = r"d:\New folder (3)\clothing\Embossed_Triangle_Luxury_Tee_Pink_HD"
os.makedirs(pink_dir, exist_ok=True)

pink_sources = {
    '1_Front_Main_Pink.jpg': r"d:\New folder (3)\clothing\myproject\embossed_triangle_refs\final_pink_angle_1.jpg",
    '2_Side_View_Pink.jpg': r"d:\New folder (3)\clothing\myproject\embossed_triangle_refs\final_pink_angle_2.jpg",
    '3_Back_View_Pink.jpg': r"d:\New folder (3)\clothing\myproject\embossed_triangle_refs\final_pink_angle_3_perfect.jpg",
    '4_Detail_Texture_Pink.jpg': r"d:\New folder (3)\clothing\myproject\embossed_triangle_refs\final_pink_angle_4_master.jpg",
}

print("Saving Pink HD images...")
for dest_name, src_path in pink_sources.items():
    dest_path = os.path.join(pink_dir, dest_name)
    shutil.copy2(src_path, dest_path)
    print(f"  -> Saved {dest_name}")

# 2. Setup Cream HD directory for clean archive
cream_dir = r"d:\New folder (3)\clothing\Embossed_Triangle_Luxury_Tee_Cream_HD"
os.makedirs(cream_dir, exist_ok=True)

cream_sources = {
    '1_Front_Main_Cream.jpg': r"d:\New folder (3)\clothing\myproject\embossed_triangle_refs\prod_85_Cream_main.jpg",
    '2_Side_View_Cream.jpg': r"d:\New folder (3)\clothing\myproject\embossed_triangle_refs\prod_85_Cream_gallery_1.jpg",
    '3_Back_View_Cream.jpg': r"d:\New folder (3)\clothing\myproject\embossed_triangle_refs\prod_85_Cream_gallery_2.jpg",
    '4_Detail_Texture_Cream.jpg': r"d:\New folder (3)\clothing\myproject\embossed_triangle_refs\prod_85_Cream_gallery_3.jpg",
}

print("\nSaving Cream HD images...")
for dest_name, src_path in cream_sources.items():
    dest_path = os.path.join(cream_dir, dest_name)
    shutil.copy2(src_path, dest_path)
    print(f"  -> Saved {dest_name}")

# 3. Upload to Cloudinary & update database
product_id = 84
p = Product.objects.get(id=product_id)
print(f"\n==========================================")
print(f"Uploading Photoshoot for: ID {p.id} - {p.name} (Pink)")

# Upload main image
main_path = os.path.join(pink_dir, '1_Front_Main_Pink.jpg')
print("Uploading Main: 1_Front_Main_Pink.jpg...")
res_main = cloudinary.uploader.upload(main_path, folder='villi-shop/products', resource_type='image')
main_pid = res_main['public_id']
print(f"  -> Main uploaded: {main_pid}")

# Upload gallery images
gallery_files = ['2_Side_View_Pink.jpg', '3_Back_View_Pink.jpg', '4_Detail_Texture_Pink.jpg']
gallery_pids = []
for f in gallery_files:
    fpath = os.path.join(pink_dir, f)
    print(f"Uploading Gallery: {f}...")
    res = cloudinary.uploader.upload(fpath, folder='villi-shop/product_gallery', resource_type='image')
    gallery_pids.append(res['public_id'])
    print(f"  -> Gallery uploaded: {res['public_id']}")

# Update Product.image
p.image = main_pid
p.save(update_fields=['image'])
print(f"Updated Product.image -> {main_pid}")

# Update ProductColor.color_image
var = ProductColor.objects.filter(product=p).first()
if var:
    var.color_image = main_pid
    var.save(update_fields=['color_image'])
    print(f"Updated ProductColor({var.color_name}).color_image -> {main_pid}")

# Update ProductImage gallery
p.images.all().delete()
for g_pid in gallery_pids:
    ProductImage.objects.create(product=p, image=g_pid)
    print(f"Added gallery image: {g_pid}")

# Clear cache
cache.clear()
print("\nSUCCESS: Product ID 84 (Pink Embossed Triangle Luxury Tee) is 100% LIVE!")
