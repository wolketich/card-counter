#!/usr/bin/env python3
import os
import requests
import cv2
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import messagebox
import json
import shutil
from rich.console import Console
from rich.progress import Progress

# Current user and time information
USER = "wolketich"
CURRENT_TIME = "2025-04-23 08:33:58"

# Card info
SUITS = ['♠', '♥', '♦', '♣']
RANKS = ['7', '8', '9', '10', 'J', 'Q', 'K', 'A']

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CARDS_DIR = os.path.join(BASE_DIR, 'cards')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
MAPPING_FILE = os.path.join(BASE_DIR, 'card_mapping.json')

# Card dimensions
CARD_WIDTH = 180
CARD_HEIGHT = 250
CARD_GAP = 15

console = Console()

def download_cards():
    """Download all cards from the website"""
    os.makedirs(CARDS_DIR, exist_ok=True)
    
    console.print("[bold cyan]Downloading cards...[/bold cyan]")
    
    with Progress() as progress:
        task = progress.add_task("[green]Downloading...", total=33)
        
        for i in range(33):
            url = f"https://belot.md/static/images/cards/deck_5/{i}.png"
            file_path = os.path.join(CARDS_DIR, f"{i}.png")
            
            # Skip if file already exists
            if os.path.exists(file_path):
                progress.update(task, advance=1)
                continue
                
            try:
                response = requests.get(url, stream=True)
                if response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                else:
                    console.print(f"[red]Failed to download {url}. Status code: {response.status_code}[/red]")
            except Exception as e:
                console.print(f"[red]Error downloading {url}: {e}[/red]")
                
            progress.update(task, advance=1)
    
    console.print("[green]Cards downloaded successfully![/green]")

def identify_cards():
    """GUI to identify each card"""
    if not os.path.exists(CARDS_DIR):
        console.print("[red]Cards directory not found. Please download cards first.[/red]")
        return None
        
    card_files = sorted([f for f in os.listdir(CARDS_DIR) if f.endswith('.png')], 
                        key=lambda x: int(x.split('.')[0]))
    
    if not card_files:
        console.print("[red]No card images found in the cards directory.[/red]")
        return None
    
    # Create mapping dictionary
    card_mapping = {}
    
    # Special case for card 0.png (card back)
    if "0.png" in card_files:
        card_mapping["0.png"] = {"rank": "back", "suit": "back"}
        console.print("[cyan]Card 0.png automatically marked as card back[/cyan]")
    
    # Create GUI
    root = tk.Tk()
    root.title("Card Identification")
    root.geometry("400x550")
    
    # Variables
    current_index = [0]
    if "0.png" in card_files:
        current_index = [1]  # Skip card back in GUI
        
    current_card_var = tk.StringVar(value=card_files[current_index[0]])
    rank_var = tk.StringVar(value=RANKS[0])
    suit_var = tk.StringVar(value=SUITS[0])
    status_var = tk.StringVar(value="")
    progress_var = tk.StringVar(value=f"Card 1 of {len(card_files)-1}")
    
    # Frame for card display
    card_frame = tk.Frame(root)
    card_frame.pack(pady=10)
    
    # Label for card image
    card_label = tk.Label(card_frame)
    card_label.pack()
    
    # Function to update card image
    def update_card_image():
        try:
            img_path = os.path.join(CARDS_DIR, card_files[current_index[0]])
            img = Image.open(img_path)
            img = img.resize((180, 250), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            card_label.config(image=photo)
            card_label.image = photo  # Keep a reference
            current_card_var.set(f"Card: {card_files[current_index[0]]}")
            
            # Update progress
            progress_var.set(f"Card {current_index[0]} of {len(card_files)-1}")
            
            # If card was previously identified, set the dropdown values
            card_id = card_files[current_index[0]]
            if card_id in card_mapping:
                rank_var.set(card_mapping[card_id]['rank'])
                suit_var.set(card_mapping[card_id]['suit'])
                
        except Exception as e:
            status_var.set(f"Error: {e}")
    
    # Call initially
    update_card_image()
    
    # Frame for card info
    info_frame = tk.Frame(root)
    info_frame.pack(pady=10)
    
    # Label for current card
    current_card_label = tk.Label(info_frame, textvariable=current_card_var, font=("Arial", 12))
    current_card_label.grid(row=0, column=0, columnspan=2, pady=5)
    
    # Progress label
    progress_label = tk.Label(info_frame, textvariable=progress_var, font=("Arial", 10))
    progress_label.grid(row=1, column=0, columnspan=2, pady=5)
    
    # Rank selection
    tk.Label(info_frame, text="Rank:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
    rank_menu = tk.OptionMenu(info_frame, rank_var, *RANKS)
    rank_menu.grid(row=2, column=1, sticky="w", padx=5, pady=5)
    
    # Suit selection
    tk.Label(info_frame, text="Suit:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
    suit_menu = tk.OptionMenu(info_frame, suit_var, *SUITS)
    suit_menu.grid(row=3, column=1, sticky="w", padx=5, pady=5)
    
    # Navigation buttons
    nav_frame = tk.Frame(root)
    nav_frame.pack(pady=10)
    
    def next_card():
        # Save current selection
        card_id = card_files[current_index[0]]
        rank = rank_var.get()
        suit = suit_var.get()
        card_mapping[card_id] = {'rank': rank, 'suit': suit}
        
        # Move to next card
        if current_index[0] < len(card_files) - 1:
            current_index[0] += 1
            update_card_image()
            status_var.set(f"Saved {card_id} as {rank}{suit}")
        else:
            status_var.set("All cards identified!")
    
    def prev_card():
        if current_index[0] > 1:  # Don't go back to card 0 (back)
            current_index[0] -= 1
            update_card_image()
            
            # Update dropdown menus if card was previously identified
            card_id = card_files[current_index[0]]
            if card_id in card_mapping:
                rank_var.set(card_mapping[card_id]['rank'])
                suit_var.set(card_mapping[card_id]['suit'])
    
    def finish():
        # Save current selection
        card_id = card_files[current_index[0]]
        rank = rank_var.get()
        suit = suit_var.get()
        card_mapping[card_id] = {'rank': rank, 'suit': suit}
        
        # Check if all cards are identified
        if len(card_mapping) < len(card_files):
            unidentified = len(card_files) - len(card_mapping)
            if not messagebox.askyesno("Confirmation", 
                                       f"{unidentified} cards are not identified. Do you want to continue?"):
                return
        
        # Save mapping and close
        save_mapping(card_mapping)
        root.destroy()
    
    # Previous button
    prev_button = tk.Button(nav_frame, text="Previous", command=prev_card)
    prev_button.grid(row=0, column=0, padx=10)
    
    # Next button
    next_button = tk.Button(nav_frame, text="Next", command=next_card)
    next_button.grid(row=0, column=1, padx=10)
    
    # Finish button
    finish_button = tk.Button(nav_frame, text="Finish", command=finish, bg="#4CAF50", fg="white")
    finish_button.grid(row=0, column=2, padx=10)
    
    # Status bar
    status_bar = tk.Label(root, textvariable=status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
    status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    # Start main loop
    root.mainloop()
    
    return card_mapping

def save_mapping(card_mapping):
    """Save card mapping to JSON file"""
    if not card_mapping:
        return
        
    with open(MAPPING_FILE, 'w') as f:
        json.dump(card_mapping, f, indent=4)
    
    console.print(f"[green]Card mapping saved to {MAPPING_FILE}[/green]")
    
    # Create templates directory
    create_templates(card_mapping)

def create_templates(card_mapping):
    """Create template images for each rank and suit"""
    if os.path.exists(TEMPLATES_DIR):
        shutil.rmtree(TEMPLATES_DIR)
    
    os.makedirs(os.path.join(TEMPLATES_DIR, 'ranks'), exist_ok=True)
    os.makedirs(os.path.join(TEMPLATES_DIR, 'suits'), exist_ok=True)
    
    console.print("[bold cyan]Creating templates...[/bold cyan]")
    
    # Track which ranks and suits we've processed
    processed_ranks = set()
    processed_suits = set()
    
    for card_file, card_info in card_mapping.items():
        rank = card_info['rank']
        suit = card_info['suit']
        
        # Skip card back
        if rank == "back" and suit == "back":
            continue
        
        # Read the card image
        card_path = os.path.join(CARDS_DIR, card_file)
        card = cv2.imread(card_path)
        
        if card is None:
            console.print(f"[red]Could not read {card_path}[/red]")
            continue
        
        # Extract rank region (0-80px X, 0-80px Y)
        rank_region = card[0:80, 0:80]
        
        # Extract suit region (0-80px X, 80-145px Y)
        suit_region = card[80:145, 0:80]
        
        # Save rank template if we haven't processed this rank yet
        if rank not in processed_ranks:
            rank_path = os.path.join(TEMPLATES_DIR, 'ranks', f"{rank}.png")
            cv2.imwrite(rank_path, rank_region)
            processed_ranks.add(rank)
            console.print(f"Created template for rank: [cyan]{rank}[/cyan]")
        
        # Save suit template if we haven't processed this suit yet
        if suit not in processed_suits:
            suit_path = os.path.join(TEMPLATES_DIR, 'suits', f"{suit}.png")
            cv2.imwrite(suit_path, suit_region)
            processed_suits.add(suit)
            console.print(f"Created template for suit: [cyan]{suit}[/cyan]")
        
        # Once we have all ranks and suits, we can stop
        if len(processed_ranks) == len(RANKS) and len(processed_suits) == len(SUITS):
            break
    
    # Also create a template for card back
    back_path = os.path.join(CARDS_DIR, "0.png")
    if os.path.exists(back_path):
        back_img = cv2.imread(back_path)
        if back_img is not None:
            # Save small version of back for detection
            cv2.imwrite(os.path.join(TEMPLATES_DIR, 'back.png'), back_img[0:80, 0:80])
            console.print("Created template for card back")
    
    console.print("[green]Templates created successfully![/green]")

def main():
    console.print(f"[bold cyan]Belot Card Calibrator[/bold cyan]")
    console.print(f"[dim]User: {USER} | Time: {CURRENT_TIME}[/dim]\n")
    
    # Check if mapping already exists
    if os.path.exists(MAPPING_FILE):
        console.print("[yellow]Card mapping already exists.[/yellow]")
        choice = input("Do you want to recalibrate? (y/n): ").lower()
        if choice != 'y':
            console.print("[green]Using existing calibration.[/green]")
            return
    
    # Download cards if needed
    if not os.path.exists(CARDS_DIR) or not os.listdir(CARDS_DIR):
        download_cards()
    
    # Identify cards
    card_mapping = identify_cards()
    
    if card_mapping:
        console.print("\n[bold green]Calibration complete![/bold green]")
        console.print("You can now use belot_calculator.py to calculate card points.")
    else:
        console.print("\n[bold red]Calibration failed or was cancelled.[/bold red]")

if __name__ == "__main__":
    main()