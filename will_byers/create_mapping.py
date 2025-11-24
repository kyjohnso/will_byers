#!/usr/bin/env python

import json
import sys
import time
from pathlib import Path

# Try to import LED libraries
try:
    import board
    import neopixel
    LED_AVAILABLE = True

    pixel_pin = board.D18
    num_pixels = 150
    ORDER = neopixel.GRB

    pixels = neopixel.NeoPixel(
        pixel_pin, num_pixels, brightness=0.9, pixel_order=ORDER
    )
except (ImportError, NotImplementedError, RuntimeError) as e:
    LED_AVAILABLE = False
    pixels = None
    print(f"ERROR: LED hardware not available: {e}")
    print("This tool requires LED hardware to be connected.")
    exit(1)

# Try to import getch for better keyboard input handling
try:
    import tty
    import termios
    GETCH_AVAILABLE = True
    
    def getch():
        """Get a single character from stdin without echo."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
    
    def get_input():
        """Get input with support for backspace and enter."""
        chars = []
        while True:
            ch = getch()
            
            # Handle Enter (newline)
            if ch == '\r' or ch == '\n':
                print()  # New line
                return ''.join(chars).upper()
            
            # Handle Backspace (127 or 8)
            elif ord(ch) == 127 or ord(ch) == 8:
                return 'BACKSPACE'
            
            # Handle Ctrl+C
            elif ord(ch) == 3:
                raise KeyboardInterrupt
            
            # Handle regular characters
            elif ch.isprintable():
                chars.append(ch)
                sys.stdout.write(ch)
                sys.stdout.flush()
            
            # Handle escape sequences (arrow keys, etc.)
            elif ord(ch) == 27:
                # Read the rest of the escape sequence
                next1 = getch()
                next2 = getch()
                # Ignore for now
                continue
                
except ImportError:
    GETCH_AVAILABLE = False
    print("Warning: Advanced keyboard input not available. Using basic input.")
    
    def get_input():
        """Fallback to basic input."""
        return input().strip().upper()

def create_led_mapping():
    """Interactive tool to create LED to character mapping."""
    print("=" * 60)
    print("LED Mapping Configuration Tool")
    print("=" * 60)
    print("\nThis tool will help you map each letter to its LED position.")
    print("For each LED position (0-149):")
    print("  - The LED will light up")
    print("  - Type a letter (A-Z) and press ENTER to map it")
    print("  - Press ENTER alone to skip this position")
    print("  - Press BACKSPACE to go back to the previous LED")
    print("\nYou can type 'quit' at any time to save and exit.")
    print("=" * 60)
    
    # Determine config file path (in project root)
    config_path = Path(__file__).parent.parent / "led_mapping.json"
    
    # Load existing mapping if it exists
    mapping = {}
    if config_path.exists():
        print(f"\nFound existing mapping at: {config_path}")
        response = input("Do you want to start fresh or continue from existing? (fresh/continue): ").strip().lower()
        if response == 'continue':
            with open(config_path, 'r') as f:
                mapping = json.load(f)
            print(f"Loaded {len(mapping)} existing mappings.")
    
    # Clear all LEDs
    pixels.fill((0, 0, 0))
    
    # Color to use for highlighting
    highlight_color = (255, 255, 0)  # Yellow
    
    try:
        led_num = 0
        while led_num < 150:
            # Light up current LED
            pixels[led_num] = highlight_color
            
            print(f"\n--- LED #{led_num} ---")
            
            # Show existing mapping if any
            existing = None
            for letter, pos in mapping.items():
                if pos == led_num:
                    existing = letter
                    break
            
            if existing:
                print(f"Current mapping: {existing}")
            
            # Get user input
            if GETCH_AVAILABLE:
                print(f"Letter for LED #{led_num} (ENTER=skip, BACKSPACE=go back, 'quit'=exit): ", end='', flush=True)
                user_input = get_input()
            else:
                user_input = input(f"Letter for LED #{led_num} (ENTER=skip, 'back'=go back, 'quit'=exit): ").strip().upper()
            
            # Handle backspace
            if user_input == 'BACKSPACE' or user_input == 'BACK':
                if led_num > 0:
                    # Turn off current LED
                    pixels[led_num] = (0, 0, 0)
                    # Go back one
                    led_num -= 1
                    print("← Going back to previous LED")
                    continue
                else:
                    print("Already at first LED, cannot go back.")
                    continue
            
            if user_input == 'QUIT':
                print("\nSaving and exiting...")
                break
            
            if user_input and len(user_input) == 1 and user_input.isalpha():
                # Remove any existing mapping for this letter
                if user_input in mapping:
                    old_pos = mapping[user_input]
                    print(f"Note: {user_input} was previously mapped to LED #{old_pos}")
                
                # Remove any existing mapping for this LED position
                for letter, pos in list(mapping.items()):
                    if pos == led_num:
                        del mapping[letter]
                        print(f"Removed previous mapping: {letter}")
                
                mapping[user_input] = led_num
                print(f"✓ Mapped '{user_input}' to LED #{led_num}")
            elif user_input and user_input not in ['', 'BACKSPACE', 'BACK']:
                print("Invalid input. Please enter a single letter A-Z, or press ENTER to skip.")
                # Don't advance, let them try again
                continue
            
            # Turn off current LED
            pixels[led_num] = (0, 0, 0)
            time.sleep(0.1)
            
            # Move to next LED
            led_num += 1
        
        # Save mapping to JSON file
        with open(config_path, 'w') as f:
            json.dump(mapping, f, indent=2, sort_keys=True)
        
        print("\n" + "=" * 60)
        print(f"✓ Mapping saved to: {config_path}")
        print(f"Total letters mapped: {len(mapping)}")
        print("\nMapping summary:")
        for letter in sorted(mapping.keys()):
            print(f"  {letter}: LED #{mapping[letter]}")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        # Save what we have so far
        if mapping:
            with open(config_path, 'w') as f:
                json.dump(mapping, f, indent=2, sort_keys=True)
            print(f"Partial mapping saved to: {config_path}")
    finally:
        # Clear all LEDs
        pixels.fill((0, 0, 0))

def main():
    """Main entry point."""
    if not LED_AVAILABLE:
        print("ERROR: This tool requires LED hardware to be connected.")
        return 1
    
    create_led_mapping()
    return 0

if __name__ == "__main__":
    exit(main())