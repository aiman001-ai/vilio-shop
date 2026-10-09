import cv2
import numpy as np

side_src = r'C:\Users\INDIAN COMPUTER\.gemini\antigravity-ide\brain\6ef495ca-e327-46dd-830d-3010eb6b6622\dot_matrix_white_side_1791565421444.jpg'
img = cv2.imread(side_src)
h, w = img.shape[:2]

# Let's inspect HSV of shirt vs skin vs background
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
h_c, s_c, v_c = cv2.split(hsv)

# White shirt characteristics in this photo:
# Very low saturation: S < 35
# High brightness: V > 175
# Gray background wall also has low S, but:
# The model torso bounding box: X between 0.2*w and 0.75*w, Y between 0.22*h and 0.85*h
# Skin has S > 30 and H between 5 and 25.

# Load u2net mask from before or refine directly
# Let's see mask where V > 180 and S < 30 and Y > 0.22*h and Y < 0.82*h and X > 0.22*w and X < 0.72*w
shirt_region = np.zeros((h, w), dtype=bool)
shirt_region[int(0.22*h):int(0.82*h), int(0.22*w):int(0.72*w)] = True

is_white_shirt = (v_c > 170) & (s_c < 35) & shirt_region

# Exclude skin
is_skin = (h_c >= 4) & (h_c <= 25) & (s_c >= 25) & (v_c >= 70)
cloth_mask = is_white_shirt & (~is_skin)

# Morphological clean up
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
cloth_mask = cv2.morphologyEx(cloth_mask.astype(np.uint8), cv2.MORPH_CLOSE, kernel)
cloth_mask = cv2.morphologyEx(cloth_mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))

# Find connected components to only keep the main shirt body
num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(cloth_mask)
largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
shirt_clean_mask = (labels == largest_label).astype(np.uint8) * 255

# Fill internal holes (e.g. folds or text)
cnts, _ = cv2.findContours(shirt_clean_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
filled_mask = np.zeros_like(shirt_clean_mask)
cv2.drawContours(filled_mask, cnts, -1, 255, -1)

# Ensure skin is not included even in filled contour
filled_mask[is_skin] = 0

mask_blur = cv2.GaussianBlur(filled_mask.astype(np.float32) / 255.0, (7, 7), 0)
mask_3d = np.expand_dims(mask_blur, 2)

# Color transfer
v_norm = np.clip((v_c.astype(np.float32) - 170.0) / 85.0, 0.0, 1.0)
v_target = 80.0 + v_norm * 85.0 # range 80 to 165

hsv_red = hsv.copy().astype(np.float32)
hsv_red[:, :, 0] = 176.0 # Red
hsv_red[:, :, 1] = 235.0 # Saturation
hsv_red[:, :, 2] = v_target

bgr_red = cv2.cvtColor(hsv_red.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)
final = (bgr_red * mask_3d + img.astype(np.float32) * (1.0 - mask_3d)).astype(np.uint8)

cv2.imwrite(r'd:\New folder (3)\clothing\myproject\test_side_red_refined.jpg', final)
print('Refined side red saved!')
