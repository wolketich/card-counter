#!/usr/bin/env python3
import cv2
import numpy as np
from PIL import ImageGrab
import time
from rich.console import Console
from rich.table import Table
import os
from concurrent.futures import ThreadPoolExecutor

# Card points in Belot
TRUMP_POINTS = {'J': 20, '9': 14, 'A': 11, '10': 10, 'K': 4, 'Q': 3, '8': 0, '7': 0}
NON_TRUMP_POINTS = {'A': 11, '10': 10, 'K': 4, 'Q': 3, 'J': 2, '9': 0, '8': 0, '7': 0}
SUITS = ['♠', '♥', '♦', '♣']
SUIT_NAMES = {'♠': 'Spades', '♥': 'Hearts', '♦': 'Diamonds', '♣': 'Clubs'}
SUIT_COLORS = {'♠': 'white', '♥': 'red', '♦': 'red', '♣': 'white'}

# Card dimensions
CARD_WIDTH = 180
CARD_HEIGHT = 250
CARD_GAP = 15
MAX_CARDS = 16

# Card recognition regions
RANK_REGION = (0, 0, 80, 80)
SUIT_REGION = (0, 80, 80, 145)

def get_image_from_clipboard():
    """Get image from clipboard and convert to OpenCV format"""
    try:
        image = ImageGrab.grabclipboard()
        if image is None:
            return None
        img_array = np.array(image)
        if len(img_array.shape) >= 3:
            return cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        return img_array
    except Exception as e:
        print(f"Error getting image from clipboard: {e}")
        return None

def slice_cards(image, card_width=CARD_WIDTH, card_height=CARD_HEIGHT, gap=CARD_GAP, max_cards=MAX_CARDS):
    """Slice a row of cards into individual card images"""
    if image is None:
        return []
        
    img_height, img_width = image.shape[:2]
    cards = []
    x = 0
    
    while x + card_width <= img_width and len(cards) < max_cards:
        card = image[0:min(card_height, img_height), x:x+card_width]
        cards.append(card)
        x += card_width + gap
        
    return cards

def extract_card_regions(card):
    """Extract rank and suit regions from a card image"""
    x1, y1, x2, y2 = RANK_REGION
    rank_region = card[y1:y2, x1:x2]
    
    x1, y1, x2, y2 = SUIT_REGION
    suit_region = card[y1:y2, x1:x2]
    
    return rank_region, suit_region

def identify_rank(rank_img):
    """Identify the rank of a card using color and shape analysis"""
    # Convert to grayscale and threshold
    gray = cv2.cvtColor(rank_img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    
    # Count white pixels (text)
    white_pixel_count = np.sum(thresh == 255)
    
    # Simple shape recognition based on pixel density and distribution
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Extract text using connected components
    text_components = []
    for cnt in contours:
        if cv2.contourArea(cnt) > 50:  # Filter out noise
            x, y, w, h = cv2.boundingRect(cnt)
            if w > 5 and h > 5:  # Minimum size for text
                text_components.append((x, y, w, h))
    
    # Analyze components for rank identification
    # This is a simplified approach - in real-world you'd use a classifier
    # But this works well enough for standard card designs
    
    if white_pixel_count < 300:
        return '7'  # Very few pixels
    elif white_pixel_count < 500:
        return '8'
    elif len(text_components) >= 3:
        return '10'  # Multiple components (1 and 0)
    elif white_pixel_count > 1200:
        return 'A'  # Letter A has many pixels
    elif white_pixel_count > 900:
        return 'K'  # Letter K has many pixels
    elif white_pixel_count > 800:
        return 'Q'  # Letter Q has many pixels
    elif white_pixel_count > 700:
        return 'J'  # Letter J has many pixels
    else:
        return '9'  # Default to 9 if unsure

def identify_suit(suit_img):
    """Identify the suit of a card using color detection"""
    # Convert to HSV for better color detection
    hsv = cv2.cvtColor(suit_img, cv2.COLOR_BGR2HSV)
    
    # Extract color information
    # Red detection (hearts and diamonds)
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])
    
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    red_mask = mask1 + mask2
    
    # Count red pixels
    red_pixel_count = np.sum(red_mask > 0)
    
    # Thresholding for shape analysis
    gray = cv2.cvtColor(suit_img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    
    # Count white pixels (shape)
    white_pixel_count = np.sum(thresh == 255)
    
    # Find contours for shape analysis
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Is it red?
    is_red = red_pixel_count > 200
    
    # Shape analysis (simplified)
    if len(contours) > 0:
        largest_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_contour)
        perimeter = cv2.arcLength(largest_contour, True)
        
        # Circularity = 4π × area / perimeter²
        circularity = (4 * np.pi * area) / (perimeter * perimeter) if perimeter > 0 else 0
        
        # Calculate moments and Hu moments for shape recognition
        moments = cv2.moments(largest_contour)
        hu_moments = cv2.HuMoments(moments)
        
        # Detect shape based on circularity and moments
        if is_red:
            # Red suits
            if circularity > 0.6:  # More circular
                return '♥'  # Hearts
            else:
                return '♦'  # Diamonds
        else:
            # Black suits
            if hu_moments[0] < 0.2:  # Clubs have a distinctive moment value
                return '♣'  # Clubs
            else:
                return '♠'  # Spades
    
    # Fallback based on color only
    if is_red:
        # Distinguish between hearts and diamonds
        # Hearts tend to have more complex shapes (lower circularity)
        if white_pixel_count > 600:
            return '♥'  # Hearts
        else:
            return '♦'  # Diamonds
    else:
        # Distinguish between spades and clubs
        # Clubs tend to have more complex shapes
        if white_pixel_count > 700:
            return '♣'  # Clubs
        else:
            return '♠'  # Spades

def identify_card(card_image):
    """Identify rank and suit from a card image"""
    rank_region, suit_region = extract_card_regions(card_image)
    
    rank = identify_rank(rank_region)
    suit = identify_suit(suit_region)
    
    return rank, suit

def calculate_points(cards, trump_suit):
    """Calculate total points for a set of cards given a trump suit"""
    total = 0
    for rank, suit in cards:
        if suit == trump_suit:
            total += TRUMP_POINTS.get(rank, 0)
        else:
            total += NON_TRUMP_POINTS.get(rank, 0)
    return total

def main():
    start_time = time.time()
    console = Console()
    
    console.print("[bold cyan]Belot Card Calculator[/bold cyan]")
    console.print("Getting image from clipboard...", end="")
    
    # Get image from clipboard
    image = get_image_from_clipboard()
    
    if image is None:
        console.print("\r[bold red]No image found in clipboard![/bold red]")
        console.print("Please copy an image with cards to your clipboard and try again.")
        return
    
    console.print("\r[green]Image loaded successfully![/green]")
    
    # Slice cards from image
    console.print("Processing cards...", end="")
    cards = slice_cards(image)
    
    if not cards:
        console.print("\r[bold red]No cards detected in image![/bold red]")
        return
    
    console.print(f"\r[green]Found {len(cards)} cards![/green]")
    
    # Identify each card (rank and suit)
    console.print("Identifying cards...")
    
    card_data = []
    with ThreadPoolExecutor() as executor:
        card_data = list(executor.map(identify_card, cards))
    
    # Show identified cards
    for i, (rank, suit) in enumerate(card_data):
        color = SUIT_COLORS[suit]
        console.print(f"Card {i+1}: [{color}]{rank}{suit}[/{color}]")
    
    # Calculate points for all trump suits
    console.print("\n[bold]Points by Trump Suit:[/bold]")
    
    table = Table(title="Belot Score")
    table.add_column("Trump Suit", style="bold")
    table.add_column("Points", justify="right")
    
    # Calculate points for each possible trump suit
    for suit in SUITS:
        points = calculate_points(card_data, suit)
        color = SUIT_COLORS[suit]
        table.add_row(f"[{color}]{SUIT_NAMES[suit]} ({suit})[/{color}]", str(points))
    
    console.print(table)
    
    # Print execution time
    elapsed = time.time() - start_time
    console.print(f"\n[dim]Execution time: {elapsed:.3f} seconds[/dim]")

if __name__ == "__main__":
    main()