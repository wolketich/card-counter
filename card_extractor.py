import cv2
import os

def slice_card_row(image_path, output_dir='cards_output', card_width=180, card_height=250, gap=15):
    image = cv2.imread(image_path)
    if image is None:
        print("❌ Could not load image.")
        return

    os.makedirs(output_dir, exist_ok=True)

    img_height, img_width, _ = image.shape
    y = 0  # Since it’s a single row
    x = 0
    card_index = 0

    while x + card_width <= img_width:
        card = image[y:y+card_height, x:x+card_width]

        filename = f'card_{card_index:02d}.png'
        cv2.imwrite(os.path.join(output_dir, filename), card)

        card_index += 1
        x += card_width + gap

    print(f"✅ Extracted {card_index} card(s) to folder: {output_dir}")

# Example usage
slice_card_row('cards_input.png')