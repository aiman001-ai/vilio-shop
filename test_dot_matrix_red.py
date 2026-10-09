import cv2
import numpy as np
import os
from rembg import new_session

session = new_session("u2net_cloth_seg")

def get_cloth_mask(img):
    h_orig, w_orig = img.shape[:2]
    resized = cv2.resize(img, (768, 768))
    blob = resized.astype(np.float32) / 255.0
    blob = (blob - np.array([0.485, 0.456, 0.406])) / np.array([0.229, 0.224, 0.225])
    blob = np.transpose(blob, (2, 0, 1))
    blob = np.expand_dims(blob, 0).astype(np.float32)

    outputs = session.inner_session.run(None, {'input': blob})
    preds = outputs[0][0]
    seg = np.argmax(preds, axis=0)
    
    # channel 1 is upper_clothes
    mask = (seg == 1).astype(np.uint8) * 255
    mask_full = cv2.resize(mask, (w_orig, h_orig), interpolation=cv2.INTER_LINEAR)
    return mask_full

def recolor_to_crimson_red(img, mask, protect_white_graphics=False, protect_artwork=False):
    h, w = img.shape[:2]
    
    # Refine mask: smooth edges
    mask_blur = cv2.GaussianBlur(mask, (7, 7), 0).astype(np.float32) / 255.0
    
    # If protecting white puff print/graphics (constellation text):
    # In the white shirt, the text is raised 3D emboss. In red shirt, the text is pure bright white puff print.
    # We can detect the text or if protect_white_graphics is True.
    # In the back shot: the mummy graphic has yellow/tan and black linework.
    # We must protect the graphic from being tinted red!
    if protect_artwork:
        # Detect mummy graphic on the back:
        # Mummy graphic has dark linework and tan/gold tones, surrounded by the shirt.
        # Inside the shirt mask, pixels that have significant darkness (linework) or gold/tan color
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        s = hsv[:, :, 1]
        v = hsv[:, :, 2]
        # In white shirt, shirt has s < 25, v > 190
        # Graphic has s > 35 or v < 160
        is_artwork = (mask > 128) & ((s > 35) | (v < 170))
        # Dilate slightly to avoid halo
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        is_artwork = cv2.dilate(is_artwork.astype(np.uint8), kernel, iterations=1)
        art_blur = cv2.GaussianBlur(is_artwork.astype(np.float32), (5, 5), 0)
        mask_blur = mask_blur * (1.0 - art_blur)

    # Let's do realistic color transfer from white to vibrant red
    # Red target has H around 176/0, high S (240), L proportional to shading
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    
    # Original brightness V (0-255) represents the wrinkles and folds
    v_orig = hsv[:, :, 2]
    # Normalize V: white shirt has high V (190 - 255)
    # Target red shirt has V around (100 - 180) with deep shadows around 70-90
    v_norm = (v_orig - 180.0) / 75.0
    v_norm = np.clip(v_norm, 0.0, 1.0)
    v_target = 85.0 + v_norm * 80.0 # Range 85 to 165
    
    hsv_red = hsv.copy()
    hsv_red[:, :, 0] = 176.0 # Vibrant Red hue
    hsv_red[:, :, 1] = 235.0 # Rich saturation
    hsv_red[:, :, 2] = v_target
    
    bgr_red = cv2.cvtColor(hsv_red.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)
    
    # If protecting white puff text on chest (for side/front):
    if protect_white_graphics:
        # On white shirt, find the embossed text highlights
        pass

    mask_3d = np.expand_dims(mask_blur, 2)
    final = (bgr_red * mask_3d + img.astype(np.float32) * (1.0 - mask_3d)).astype(np.uint8)
    return final

# Test on side shot
side_src = r'C:\Users\INDIAN COMPUTER\.gemini\antigravity-ide\brain\6ef495ca-e327-46dd-830d-3010eb6b6622\dot_matrix_white_side_1791565421444.jpg'
img_side = cv2.imread(side_src)
mask_side = get_cloth_mask(img_side)
red_side = recolor_to_crimson_red(img_side, mask_side)

out_test = r'd:\New folder (3)\clothing\myproject\test_side_red.jpg'
cv2.imwrite(out_test, red_side)
print('Test side red saved to:', out_test)
