# Margonem Bot

A bot for automating gameplay in Margonem by detecting enemies and performing combat automatically.

## Features

- Automatically captures the game canvas
- Uses image recognition to find enemies on screen
- Clicks on the closest enemy to your character
- Attempts to initiate combat automatically

## Setup Instructions

1. Clone this repository to your local machine

2. Install the required dependencies:

```bash
pip install playwright opencv-python numpy pillow
```

3. Install Playwright browsers:

```bash
playwright install
```

4. Make sure you have the enemy templates in the `templates/enemies` folder

## Usage

Run the script:

```bash
python playwright_interaction.py
```

You'll be prompted to choose an operation:
1. Capture canvas screenshot - just takes a screenshot of the game canvas
2. Run bot - starts the automated enemy detection and fighting

When running the bot:
1. The script will open a browser window and navigate to Margonem
2. You'll need to log in manually
3. Press Enter when ready to start the bot
4. The bot will continually scan for enemies and click on the closest one
5. Press 'q' at any prompt to quit the bot

## Customization

You can adjust the template matching threshold in the code (default is 0.7). 
A higher threshold means more precise matching but might miss some enemies.

## Notes

- You may need to adjust the selectors for the "Fight" button based on the game's UI
- The bot assumes your character is at the center of the screen
- For best results, collect templates of all enemy types you want the bot to recognize 