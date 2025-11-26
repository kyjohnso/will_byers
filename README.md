# Stranger Things Wall

<img src="./assets/images/full_color_wall.jpg" alt="Full Color Wall" style="max-width: 800px; width: 100%;">

*The completed installation with all LEDs positioned and tested*

A raspberry pi, WS2811 LED string, speach to text, and AI chat Stranger Things Wall - Talk to Will Byers in the upside down from the iconic Stranger Things Season 1 scene. 

**Project History:** I originally built this in May 2022 for the Stranger Things Season 4 premier, with plans to integrate voice activation using Amazon's Alexa Gadgets API (similar to my [Alexa-enabled Lego Mindstorms maze solver](https://www.hackster.io/kyle22/dwr-an-alexa-voice-enabled-maze-solving-lego-robot-405dbf)). Unfortunately, Amazon discontinued the Alexa Gadgets API before I could complete the integration so I was left with the (still pretty impressive, if I say so myself!) static message generator shown in the GIF above. I could use this to print out static messages to celebrate halloween, the Season 4 premier, and I could also put in secret messages to my kids. 

With Season 5 on the horizon and the massive improvements in LLMs and speech-to-text technology, I decided to revisit the project, this time using:
* [Vosk](https://alphacephei.com/vosk/) for custom wake-word detection, 
* [Whisper](https://github.com/openai/whisper) for speech to text, and
* [Anthropic SDK](https://github.com/anthropics/anthropic-sdk-python) for generating Will's response

The result realizes my original plan of talking to will in the Upside Down with Will replying through the Christmas Light Alphabet!

## Build Gallery

### Electronics
This version of the build leveraged all of the electronics from the original 2022 build - the image below is my original engineering notebook entry with a rough circuit diagram.

<img src="./assets/images/engineering_notebook_entry.png" alt="Engineering Notebook" style="max-width: 800px; width: 100%;">

*Initial planning and LED mapping in the engineering notebook*

I had a friend that was experimenting with the WS281x light strips which allow you to address individual lights and give a custom RGB value. I was pretty pleased to find [this version](https://www.amazon.co.uk/ruimeimei-50PCS-Addressable-Advertising-DC12V/dp/B0CW9Z7FW5/ref=sr_1_20_sspa?th=1) which were already arranged like Christmas Lights. I chose the 12v version which would allow longer light strings and potentially a bit brighter light configurations. 

For the controller I chose the Raspberry Pi Model 4B and made extensive use of AdaFruit's [NeoPixel](https://docs.circuitpython.org/projects/neopixel/en/latest/) python library. Using the GPIO pins on the Pi (GPIO Pin 18 PWM) required that I convert the 3.3 V logic to 5 V logic for the lights - this was accomplished with a I2C logic converter (also shown in the diagram). A separate 12v supply for the lights and we are off and running. Because this is meant as a temporary installation, I just used a breadboard though for more permanent installations this would be a very simple PCB build or maybe as a PI hat - 

<img src="./assets/images/breadboard.jpg" alt="Engineering Notebook" style="max-width: 800px; width: 100%;">

*Prototype breadboard (🤫-this is still running the main display)*

I used a pi GPIO breakout board to give a bit more of a sturdy connection between the breadboard and the Pi but you can just wire the appropriate pins to the board - this will work just fine.

### Lettering
Originally, we painted letters on cardboard and then cut them out allowing for us to reposition them on the wall (without having to paint over them if I forget my alphabet and make a mistake)

<img src="./assets/images/painting_the_alphabet.jpg" alt="Painting the Alphabet" style="max-width: 800px; width: 100%;">

*Hand-painting letters on the wall for LED positioning*

<img src="./assets/images/VID-20240407-WA0006_small.gif" alt="Full Color Wall" style="max-width: 800px; width: 100%;">

Between 2022 and 2025 we had our flat painted and so not even wanting celotape marks on the wall (let alone painted letters again), I decided to make a section of the wall out of thin MDF. 6ft x 2ft sections meant I had to figure out how to attach them. Some 1/2" x 2" pine strips and a staple gun did the trick.

<img src="./assets/images/back_of_wall.jpg" alt="Full Color Wall" style="max-width: 800px; width: 100%;">

*Joining of the MDF Sections*

But, by using a separate MDF board, I was afforded the chance to make a major upgrade - 70's era floral wall paper as a background for the lettering - 

<img src="./assets/images/wall_paper_closeup.jpg" alt="Full Color Wall" style="max-width: 800px; width: 100%;">

*Self-adhesive wallpaper provides a key detail for this project*

<img src="./assets/images/vecna_and_11.jpg" alt="Full Color Wall" style="max-width: 800px; width: 100%;">

*Vecna and El*

And if you use the keyboard triggered voice chat described below - you can sync with Season 1 Episode 3!

[![Watch the demo](https://img.youtube.com/vi/hM04iaqw8V4/maxresdefault.jpg)](https://youtube.com/shorts/hM04iaqw8V4?feature=share)

*Click to watch the Stranger Things Wall in action*

## Software

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

3. Create your LED character mapping:
```bash
# Activate your virtual environment first
source venv/bin/activate

# Run the mapping tool with sudo (requires GPIO access)
sudo $(which will-byers-create-mapping)
```

The mapping tool will:
- Light up each LED position (0-149) one at a time
- Prompt you to enter the letter at that position (or press ENTER to skip)
- Save the mapping to `led_mapping.json` in the project root
- Allow you to continue from where you left off if interrupted

**Note:** If you don't create a custom mapping, the system will use the default hardcoded mapping from the original project.

## Creating Your Letter to Light Mapping

The mapping tool helps you create a custom mapping between letters (A-Z) and their corresponding LED positions on your strip. The tool lights up each LED one at a time and prompts you to identify which letter is at that position. The mapping is saved to [`led_mapping.json`](led_mapping.json:1) and can be resumed if interrupted.

Before mapping, make sure you've painted or positioned your letters on the wall and installed your LED strip.

The tool is interactive and self-explanatory - just follow the on-screen prompts to map each letter to its LED position.

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

### Voice Chat

Talk to Will Byers using your voice! The voice chat uses Whisper for speech-to-text transcription.

#### Wake Word Voice Chat (Hands-Free)

The wake word voice chat allows you to activate Will by saying "will" (or a custom wake word). This uses Vosk for local wake word detection on the Raspberry Pi.

**First, install Vosk:**
```bash
# Activate your virtual environment first
source venv/bin/activate

# Install vosk
pip install vosk
```

The Vosk speech recognition model (~40MB) will be automatically downloaded on first run.

**Run the wake word chat:**
```bash
# Run with sudo using the venv Python
sudo $(which python) -m will_byers.wake_word_voice_chat
# Or if you installed as a script:
sudo $(which will-byers-wake-word-chat)
```

**Features:**
- Say "will" to activate (lights will flash to acknowledge)
- Automatically records for 5 seconds after wake word
- Supports both local and remote Whisper transcription
- Customizable wake word and sensitivity

**Advanced options:**
```bash
# Use remote Whisper server for faster transcription
sudo $(which will-byers-wake-word-chat) --remote-whisper http://192.168.1.100:5000

# Custom wake word
sudo $(which will-byers-wake-word-chat) --wake-word "hey will"

# Adjust sensitivity (lower = more sensitive)
sudo $(which will-byers-wake-word-chat) --sensitivity 1e-25

# Change recording duration after wake word
sudo $(which will-byers-wake-word-chat) --record-duration 10
```

#### Manual Voice Chat (Press Enter to Record)

```bash
# Activate your virtual environment first
source venv/bin/activate

# Run with sudo using the venv Python
sudo $(which python) -m will_byers.voice_chat
# Or if you installed as a script:
sudo $(which will-byers-voice-chat)
```

#### Remote Transcription (recommended for better performance)

For better performance, you can run Whisper on a separate machine with a GPU and use it as a remote transcription server:

**On your GPU machine (e.g., desktop with NVIDIA GPU):**

1. Install system dependencies:
```bash
# On Ubuntu/Debian
sudo apt-get update
sudo apt-get install ffmpeg

# On macOS
brew install ffmpeg

# On Windows
# Download from https://ffmpeg.org/download.html
```

2. Install the package:
```bash
pip install -e .
```

3. Start the Whisper server:
```bash
# Use the default base model
will-byers-whisper-server

# Or specify a different model and port
will-byers-whisper-server --model medium --port 5000 --host 0.0.0.0
```

Available models: `tiny`, `base`, `small`, `medium`, `large` (larger = more accurate but slower)

**On your Raspberry Pi:**

```bash
# Run voice chat with remote transcription
sudo $(which will-byers-voice-chat) --remote-whisper http://192.168.1.100:5000

# Replace 192.168.1.100 with your GPU machine's IP address

# Or use with wake word chat
sudo $(which will-byers-wake-word-chat) --remote-whisper http://192.168.1.100:5000
```

The remote server will:
- Use GPU acceleration for faster transcription
- Reduce CPU load on the Raspberry Pi
- Provide better transcription accuracy with larger models

**Note:** The wake word detection always runs locally on the Pi (using Vosk), only the speech-to-text transcription can be offloaded to the remote server.

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


## Troubleshooting

### Whisper Server Error: "No such file or directory: 'ffmpeg'"

If you encounter this error when running the Whisper server:
```
❌ Error: Server returned error: 500 - {"error":"[Errno 2] No such file or directory: 'ffmpeg'"}
```

**Solution:** Install ffmpeg on your system:

```bash
# On Ubuntu/Debian
sudo apt-get update
sudo apt-get install ffmpeg

# On macOS
brew install ffmpeg

# On Windows
# Download from https://ffmpeg.org/download.html and add to PATH
```

After installing ffmpeg, restart the Whisper server and try again.

### Verifying ffmpeg Installation

To verify ffmpeg is installed correctly:
```bash
ffmpeg -version
```

You should see version information. If you get "command not found", ffmpeg is not installed or not in your PATH.
Just like the show! 🎄
