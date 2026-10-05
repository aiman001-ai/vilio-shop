import os
import shutil
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

import cloudinary.uploader
from django.core.cache import cache
from app1.models import Product, ProductColor, ProductImage

# 1. APPLY PINK (ID: 67)
pink_dir = r"d:\New folder (3)\clothing\Waffle_Grid_Textured_Shirt_Pink_HD"
os.makedirs(pink_dir, exist_ok=True)

pink_sources = {
    '1_Front_Main_Pink.jpg': r"C:\Users\INDIAN COMPUTER\.gemini\antigravity-ide\brain\ad4da40d-ba5f-44f2-be13-a14b6c2740e4\waffle_pink_front_upper_1791125016461.jpg",
    '2_Side_View_Pink.jpg': r"C:\Users\INDIAN COMPUTER\.gemini\antigravity-ide\brain\ad4da40d-ba5f-44f2-be13-a14b6c2740e4\waffle_pink_side_view_1791125037711.jpg",
    '3_Back_View_Pink.jpg': r"C:\Users\INDIAN COMPUTER\.gemini\antigravity-ide\brain\ad4da40d-ba5f-44f2-be13-a14b6c2740e4\waffle_pink_back_view_1791125061972.jpg",
    '4_Detail_Texture_Pink.jpg': r"C:\Users\INDIAN COMPUTER\.gemini\antigravity-ide\brain\ad4da40d-ba5f-44f2-be13-a14b6c2740e4\waffle_pink_detail_view_1791125115124.jpg",
}

print("Saving Pink HD images...")
for dest_name, src_path in pink_sources.items():
    dest_path = os.path.join(pink_dir, dest_name)
    shutil.copy2(src_path, dest_path)
    print(f"  -> {dest_name}")

# 2. APPLY GREEN (ID: 68)
green_dir = r"d:\New folder (3)\clothing\Waffle_Grid_Textured_Shirt_Green_HD"
os.makedirs(green_dir, exist_ok=True)

green_sources = {
    '1_Front_Main_Green.jpg': r"C:\Users\INDIAN COMPUTER\.gemini\antigravity-ide\brain\ad4da40d-ba5f-44f2-be13-a14b6c2740e4\waffle_green_front_upper_1791125144909.jpg",
    '2_Side_View_Green.jpg': r"C:\Users\INDIAN COMPUTER\.gemini\antigravity-ide\brain\ad4da40d-ba5f-44f2-be13-a14b6c2740e4\waffle_green_side_view_1791125173230.jpg",
    '3_Back_View_Green.jpg': r"C:\Users\INDIAN COMPUTER\.gemini\antigravity-ide\brain\ad4da40d-ba5f-44f2-be13-a14b6c2740e4\waffle_green_back_view_1791125200786.jpg",
    '4_Detail_Texture_Green.jpg': r"C:\Users\INDIAN COMPUTER\.gemini\antigravity-ide\brain\ad4da40d-ba5f-44f2-be13-a14b6c2740e4\waffle_green_detail_view.jpg",
}

print("Saving Green HD images...")
for dest_name, src_path in green_sources.items():
    dest_path = os.path.join(green_dir, dest_name)
    shutil.copy2(src_path, dest_path)
    print(f"  -> {dest_name}")

def upload_and_update(product_id, color_name, image_dir, image_files):
    p = Product.objects.get(id=product_id)
    print(f"\n==========================================")
    print(f"Uploading Photoshoot for: ID {p.id} - {p.name} ({color_name})")
    
    uploaded_keys = []
    # Upload main image
    main_path = os.path.join(image_dir, image_files[0])
    print(f"Uploading Main: {image_files[0]}...")
    res = cloudinary.uploader.upload(main_path, folder='villi-shop/products', resource_type='image')
    main_pid = res['public_id']
    print(f"  -> Main uploaded: {main_pid}")

    # Upload gallery images
    gallery_pids = []
    for f in image_files[1:]:
        fpath = os.path.join(image_dir, f)
        print(f"Uploading Gallery: {f}...")
        res = cloudinary.uploader.upload(fpath, folder='villi-shop/product_gallery', resource_type='image')
        gallery_pids.append(res['public_id'])
        print(f"  -> Gallery uploaded: {res['public_id']}")

    # 1. Update Product.image
    p.image = main_pid
    p.save(update_fields=['image'])
    print(f"Updated Product.image -> {main_pid}")

    # 2. Update ProductColor.color_image
    var = ProductColor.objects.filter(product=p).first()
    if var:
        var.color_image = main_pid
        var.save(update_fields=['color_image'])
        print(f"Updated ProductColor({var.color_name}).color_image -> {main_pid}")

    # 3. Update ProductImage gallery
    p.images.all().delete()
    for g_pid in gallery_pids:
        ProductImage.objects.create(product=p, image=g_pid)
        print(f"Added gallery image: {g_pid}")

    print(f"SUCCESS: Product ID {product_id} ({color_name}) updated completely!")

# Execute Pink
upload_and_update(
    product_id=67,
    color_name="Pink",
    image_dir=pink_dir,
    image_files=['1_Front_Main_Pink.jpg', '2_Side_View_Pink.jpg', '3_Back_View_Pink.jpg', '4_Detail_Texture_Pink.jpg']
)

# Execute Green
upload_and_update(
    product_id=68,
    color_name="Green",
    image_dir=green_dir,
    image_files=['1_Front_Main_Green.jpg', '2_Side_View_Green.jpg', '3_Back_View_Green.jpg', '4_Detail_Texture_Green.jpg']
)

cache.clear()
print("\nDjango cache cleared. Pink and Green are LIVE!")
