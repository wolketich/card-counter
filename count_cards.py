import cv2
import pytesseract
import os

# Set Tesseract path if needed
# pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

# Belot point tables
TRUMP_POINTS = {'J': 20, '9': 14, 'A': 11, '10': 10, 'K': 4, 'Q': 3, '8': 0, '7': 0}
NON_TRUMP_POINTS = {'A': 11, '10': 10, 'K': 4, 'Q': 3, 'J': 2, '9': 0, '8': 0, '7': 0}

def read_card_value(image_path):
    img = cv2.imread(image_path)
    h, w = img.shape[:2]
    
    # Crop top-left corner where rank and suit are visible
    corner = img[0:int(h*0.4), 0:int(w*0.4)]
    gray = cv2.cvtColor(corner, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    config = '--psm 7 -c tessedit_char_whitelist=A23456789JQK10♠♣♥♦'
    text = pytesseract.image_to_string(thresh, config=config).strip()

    # Clean up and return first symbols
    cleaned = text.replace('\n', '').replace(' ', '').replace('0', '10')
    return cleaned[:3]  # e.g., "J♣" or "10♠"

def get_belot_points(card_code, trump_suit='♠'):
    if len(card_code) < 2:
        return 0  # unreadable

    # Extract rank and suit
    if card_code.startswith('10'):
        rank, suit = '10', card_code[2:]
    else:
        rank, suit = card_code[0], card_code[1:]

    if suit == trump_suit:
        return TRUMP_POINTS.get(rank, 0)
    else:
        return NON_TRUMP_POINTS.get(rank, 0)

def process_all_cards(folder='cards_output', trump_suit='♣'):
    total_points = 0
    for filename in sorted(os.listdir(folder)):
        if filename.endswith('.png'):
            path = os.path.join(folder, filename)
            code = read_card_value(path)
            points = get_belot_points(code, trump_suit=trump_suit)
            print(f'{filename}: {code} → {points} points')
            total_points += points

    print(f'\n🧮 Total Belot Score (Trump: {trump_suit}): {total_points}')

# Example usage
process_all_cards()