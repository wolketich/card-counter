#!/usr/bin/env python3
import cv2
import numpy as np
from PIL import ImageGrab
import time
import os
import json
from rich.console import Console
from rich.table import Table
from concurrent.futures import ThreadPoolExecutor

# Current user and time information
USER = "wolketich"
CURRENT_TIME = "2025-04-23 08:33:58"

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

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
MAPPING_FILE = os.path.join(BASE_DIR, 'card_mapping.json')

# Template caches
rank_templates = {}
suit_templates = {}
back_template = None

def load_templates():
    """Load templates for ranks and suits"""
    global rank_templates, suit_templates, back_template
    
    # Check if templates directory exists
    if not os.path.exists(TEMPLATES_DIR):
        return False
    
    # Load rank templates
    rank_dir = os.path.join(TEMPLATES_DIR, 'ranks')
    if os.path.exists(rank_dir):
        for file in os.listdir(rank_dir):
            if file.endswith('.png'):
                rank = os.path.splitext(file)[0]
                template_path = os.path.join(rank_dir, file)
                template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
                if template is not None:
                    rank_templates[rank] = template
    
    # Load suit templates
    suit_dir = os.path.join(TEMPLATES_DIR, 'suits')
    if os.path.exists(suit_dir):
        for file in os.listdir(suit_dir):
            if file.endswith('.png'):
                suit = os.path.splitext(file)[0]
                template_path = os.path.join(suit_dir, file)
                template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
                if template is not None:
                    suit_templates[suit] = template
    
    # Load card back template
    back_path = os.path.join(TEMPLATES_DIR, 'back.png')
    if os.path.exists(back_path):
        back_template = cv2.imread(back_path, cv2.IMREAD_GRAYSCALE)
    
    return len(rank_templates) > 0 and len(suit_templates) > 0

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

def is_card_back(card):
    """Check if this card is a card back"""
    if back_template is None:
        return False
        
    # Just check top-left corner
    corner = card[0:80, 0:80]
    gray = cv2.cvtColor(corner, cv2.COLOR_BGR2GRAY)
    
    # Template matching with back template
    result = cv2.matchTemplate(gray, back_template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)
    
    return max_val > 0.7  # High threshold for certainty

def identify_rank(rank_img):
    """Identify the rank of a card using template matching"""
    gray = cv2.cvtColor(rank_img, cv2.COLOR_BGR2GRAY)
    
    best_match = None
    best_score = -1
    
    for rank, template in rank_templates.items():
        # Template matching
        result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        
        if max_val > best_score:
            best_score = max_val
            best_match = rank
    
    return best_match if best_score > 0.6 else '?'

def identify_suit(suit_img):
    """Identify the suit of a card using template matching"""
    gray = cv2.cvtColor(suit_img, cv2.COLOR_BGR2GRAY)
    
    best_match = None
    best_score = -1
    
    for suit, template in suit_templates.items():
        # Template matching
        result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        
        if max_val > best_score:
            best_score = max_val
            best_match = suit
    
    return best_match if best_score > 0.6 else '?'

def identify_card(card_image):
    """Identify rank and suit from a card image"""
    # Check if this is a card back
    if is_card_back(card_image):
        return "back", "back"
    
    rank_region, suit_region = extract_card_regions(card_image)
    
    rank = identify_rank(rank_region)
    suit = identify_suit(suit_region)
    
    return rank, suit

def calculate_points(cards, trump_suit):
    """Calculate total points for a set of cards given a trump suit"""
    total = 0
    for rank, suit in cards:
        # Skip card backs and unidentified cards
        if rank == "back" or suit == "back" or rank == '?' or suit == '?':
            continue
            
        if suit == trump_suit:
            total += TRUMP_POINTS.get(rank, 0)
        else:
            total += NON_TRUMP_POINTS.get(rank, 0)
    return total

def main():
    start_time = time.time()
    console = Console()
    
    console.print(f"[bold cyan]Belot Card Calculator[/bold cyan]")
    console.print(f"[dim]User: {USER} | Time: {CURRENT_TIME}[/dim]\n")
    
    # Check if templates are available
    if not load_templates():
        console.print("[bold red]Card templates not found![/bold red]")
        console.print("Please run belot_calibrator.py first to set up card recognition.")
        return
    
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
    unknown_count = 0
    back_count = 0
    for i, (rank, suit) in enumerate(card_data):
        if rank == "back" and suit == "back":
            back_count += 1
            console.print(f"Card {i+1}: [blue]Card Back[/blue]")
        elif rank == '?' or suit == '?':
            unknown_count += 1
            console.print(f"Card {i+1}: [red]Unidentified[/red]")
        else:
            color = SUIT_COLORS[suit]
            console.print(f"Card {i+1}: [{color}]{rank}{suit}[/{color}]")
    
    if unknown_count > 0:
        console.print(f"\n[yellow]Warning: {unknown_count} cards could not be identified.[/yellow]")
        console.print("[yellow]Try running belot_calibrator.py again for better accuracy.[/yellow]")
    
    # Filter out card backs for point calculation
    valid_cards = [(r, s) for r, s in card_data if r != "back" and s != "back"]
    
    if len(valid_cards) == 0:
        console.print("\n[yellow]No valid cards found for point calculation.[/yellow]")
        return
    
    # Calculate points for all trump suits
    console.print("\n[bold]Points by Trump Suit:[/bold]")
    
    table = Table(title="Belot Score")
    table.add_column("Trump Suit", style="bold")
    table.add_column("Points", justify="right")
    
    # Calculate points for each possible trump suit
    for suit in SUITS:
        points = calculate_points(valid_cards, suit)
        color = SUIT_COLORS[suit]
        table.add_row(f"[{color}]{SUIT_NAMES[suit]} ({suit})[/{color}]", str(points))
    
    console.print(table)
    
    # Print execution time
    elapsed = time.time() - start_time
    console.print(f"\n[dim]Execution time: {elapsed:.3f} seconds[/dim]")
    console.print(f"[dim]Valid cards: {len(valid_cards)}, Card backs: {back_count}, Unidentified: {unknown_count}[/dim]")

if __name__ == "__main__":
    main()