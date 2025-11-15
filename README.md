# Will Byers LED Chat

![Will Byers LED Demo](./assets/images/VID-20240407-WA0006_small.gif)

Talk to Will Byers from Stranger Things through LED Christmas lights! This recreates the iconic scene where Will communicates from the Upside Down using individually addressable LEDs.

## Installation

```bash
pip install -e .
```

## Setup

1. Create a `.env` file in your project directory:
```
ANTHROPIC_API_KEY=your-api-key-here
```

2. Wire up your LED strip to GPIO 18 on your Raspberry Pi

## Usage

Run the interactive chat:
```bash
sudo will-byers-chat
```

Or run the static message demo:
```bash
sudo python -m will_byers.demos.static_messages
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
