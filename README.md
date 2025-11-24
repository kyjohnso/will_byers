# Will Byers LED Chat

![Will Byers LED Demo](./assets/images/VID-20240407-WA0006_small.gif)

Talk to Will Byers from Stranger Things through LED Christmas lights! This recreates the iconic scene where Will communicates from the Upside Down using individually addressable LEDs.

**Project History:** I originally built this in May 2022 for Stranger Things Season 4, with plans to integrate voice activation using Amazon's Alexa Gadgets API (similar to my [Alexa-enabled Lego Mindstorms maze solver](https://www.hackster.io/kyle22/dwr-an-alexa-voice-enabled-maze-solving-lego-robot-405dbf)). Unfortunately, Amazon discontinued the Alexa Gadgets API before I could complete the integration. With Season 5 on the horizon and the massive improvements in LLMs and speech-to-text technology, I decided to revisit the project—this time with Claude AI bringing Will Byers to life through natural conversation.

## Build Gallery

The complete build process, from planning to final installation:

![Engineering Notebook](./assets/images/engineering_notebook_entry.png)
*Initial planning and LED mapping in the engineering notebook*

![Painting the Alphabet](./assets/images/painting_the_alphabet.jpg)
*Hand-painting letters on the wall for LED positioning*

![Full Color Wall](./assets/images/full_color_wall.jpg)
*The completed installation with all LEDs positioned and tested*

## Installation

### Using a Virtual Environment (Recommended for Raspberry Pi)

1. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install the project and dependencies:
```bash
pip install -e .
```

3. Install system-level GPIO dependencies (if not already installed):
```bash
sudo apt-get update
sudo apt-get install python3-dev
```

4. Install audio dependencies (required for voice chat):
```bash
sudo apt-get install portaudio19-dev
```

### Running with sudo and Virtual Environment

Since GPIO access requires root privileges, you need to use the virtual environment's Python interpreter with sudo:

```bash
# Get the path to your venv Python
which python  # Should show something like /path/to/will_byers/venv/bin/python

# Use that path with sudo
sudo /path/to/will_byers/venv/bin/python -m will_byers.demos.static_messages
```

Or create an alias for convenience:
```bash
alias sudo-venv='sudo $(which python)'
# Then use: sudo-venv -m will_byers.demos.static_messages
```

## Setup

1. Create a `.env` file in your project directory:
```
ANTHROPIC_API_KEY=your-api-key-here
```

2. Wire up your LED strip to GPIO 18 on your Raspberry Pi

## Usage

### Interactive Chat

```bash
# Activate your virtual environment first
source venv/bin/activate

# Run with sudo using the venv Python
sudo $(which python) -m will_byers.chat
# Or if you installed as a script:
sudo $(which will-byers-chat)
```

### Static Message Demo

```bash
# Activate your virtual environment first
source venv/bin/activate

# Run with sudo using the venv Python
sudo $(which python) -m will_byers.demos.static_messages
```

### Testing Without Hardware

The chat script includes graceful fallback for systems without LED hardware:
```bash
# No sudo needed when running without LEDs
python -m will_byers.chat
```

## Hardware Requirements

- Raspberry Pi (any model with GPIO)
- WS281x LED strip (100 LEDs recommended)
- 5V power supply for LEDs
- Letters A-Z positioned at specific LED indices (see `char_to_pixel_map` in code)

## How It Works

1. Type a message in the terminal
2. It gets sent to Claude AI (playing Will Byers)
3. Will's response appears in the terminal
4. Each letter flashes on its corresponding LED
5. Spaces create dramatic pauses

Just like the show! 🎄
