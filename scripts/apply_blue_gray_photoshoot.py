import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

import cloudinary.uploader
from django.core.cache import cache
from app1.models import Product, ProductColor, ProductImage

blue_dir = r"d:\New folder (3)\clothing\Waffle_Grid_Textured_Shirt_Blue_HD"
gray_dir = r"d:\New folder (3)\clothing\Waffle_Grid_Textured_Shirt_Gray_HD"
green_dir = r"d:\New folder (3)\clothing\Waffle_Grid_Textured_Shirt_Green_HD"

def upload_and_update(product_id, color_name, image_dir, image_files):
    p = Product.objects.get(id=product_id)
    print(f"\n==========================================")
    print(f"Uploading Photoshoot for: ID {p.id} - {p.name} ({color_name})")
    
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

# 1. Execute Blue (ID: 69)
upload_and_update(
    product_id=69,
    color_name="Blue",
    image_dir=blue_dir,
    image_files=['1_Front_Main_Blue.jpg', '2_Side_View_Blue.jpg', '3_Back_View_Blue.jpg', '4_Detail_Texture_Blue.jpg']
)

# 2. Execute Gray (ID: 70)
upload_and_update(
    product_id=70,
    color_name="Gray",
    image_dir=gray_dir,
    image_files=['1_Front_Main_Gray.jpg', '2_Side_View_Gray.jpg', '3_Back_View_Gray.jpg', '4_Detail_Texture_Gray.jpg']
)

# 3. Refine Green (ID: 68) detail image in gallery if needed
print("\nUpdating Green (ID 68) with refined detail image...")
green_p = Product.objects.get(id=68)
detail_green_res = cloudinary.uploader.upload(
    os.path.join(green_dir, '4_Detail_Texture_Green.jpg'),
    folder='villi-shop/product_gallery',
    resource_type='image'
)
# Update the last gallery image for green
green_imgs = list(green_p.images.all())
if len(green_imgs) >= 3:
    green_imgs[2].image = detail_green_res['public_id']
    green_imgs[2].save(update_fields=['image'])
    print(f"Updated Green 3rd gallery image -> {detail_green_res['public_id']}")

cache.clear()
print("\nDjango cache cleared completely! All waffle grid photoshoot colors are 100% LIVE!")
