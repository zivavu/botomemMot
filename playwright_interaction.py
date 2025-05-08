import asyncio
from playwright.async_api import async_playwright
import os
import re
import aiohttp
import cv2
import numpy as np
from PIL import Image
import io

async def capture_margonem_page(url: str, output_filename: str = "margonem_live_screenshot.png"):
    """Launches a browser, navigates to the Margonem URL, and takes a screenshot."""
    async with async_playwright() as p:
        # Launch the browser (headless=False to see the browser, True for background)
        # You can also specify browser_type: p.chromium, p.firefox, or p.webkit
        browser = await p.chromium.launch(headless=False) 
        page = await browser.new_page()
        
        print(f"Navigating to {url}...")
        try:
            # Go to the specified URL
            # waitUntil can be 'load', 'domcontentloaded', 'networkidle'
            await page.goto(url, wait_until="networkidle", timeout=60000) # Wait up to 60s for network to be idle
            print("Page loaded successfully.")
            
            # Take a screenshot
            print(f"Taking screenshot and saving as {output_filename}...")
            await page.screenshot(path=output_filename)
            print(f"Screenshot saved to {output_filename}")
            
        except Exception as e:
            print(f"An error occurred during navigation or screenshot: {e}")
        finally:
            # Close the browser
            await browser.close()
            print("Browser closed.")

async def scrape_enemy_sprites_from_html(html_table_body_content: str, output_base_dir: str = "templates"):
    """
    Parses HTML to find enemy sprites, extracts details, downloads, and saves them.
    """
    enemies_dir = os.path.join(output_base_dir, "enemies")
    os.makedirs(enemies_dir, exist_ok=True)
    print(f"Saving enemy sprites to: {os.path.abspath(enemies_dir)}")

    # Wrap the tbody content in a basic HTML structure for Playwright
    full_html = f"<html><body><table>{html_table_body_content}</table></body></html>"

    async with async_playwright() as p_manager:
        browser = await p_manager.chromium.launch()
        page = await browser.new_page()
        await page.set_content(full_html)

        image_elements = await page.query_selector_all('img.npc')
        print(f"Found {len(image_elements)} enemy images to process.")

        async with aiohttp.ClientSession() as session:
            for i, element in enumerate(image_elements):
                src_url = await element.get_attribute('src')
                data_tip = await element.get_attribute('data-tip')

                if not src_url or not data_tip:
                    print(f"Skipping element {i+1} due to missing src or data-tip.")
                    continue

                # Parse name and level from data_tip
                name_match = re.search(r"<b>(.*?)</b>", data_tip)
                name = name_match.group(1) if name_match else f"unknown_enemy_{i+1}"
                
                level_match = re.search(r"</b>(\d+lvl)", data_tip)
                level = level_match.group(1) if level_match else "lvlUnk"

                # Sanitize name for filename
                sanitized_name = re.sub(r'[\\/*?:"<>|]', "", name)
                sanitized_name = sanitized_name.replace(" ", "_")
                
                # Get image extension
                try:
                    extension = src_url.split('.')[-1].split('?')[0]
                    if not extension or len(extension) > 4 : # Basic check for valid extension
                        filename_from_src = src_url.split('/')[-1].split('?')[0]
                        extension = filename_from_src.split('.')[-1] if '.' in filename_from_src else 'png' # Default to png
                except IndexError:
                    extension = 'png' # Default if parsing fails

                filename = f"{sanitized_name}_{level}.{extension}"
                full_output_path = os.path.join(enemies_dir, filename)

                try:
                    print(f"Downloading {src_url} as {filename}...")
                    async with session.get(src_url) as resp:
                        if resp.status == 200:
                            image_data = await resp.read()
                            with open(full_output_path, 'wb') as f:
                                f.write(image_data)
                            print(f"Successfully saved {filename}")
                        else:
                            print(f"Failed to download {src_url}. Status: {resp.status}")
                except Exception as e:
                    print(f"Error downloading or saving {src_url}: {e}")
            
        await browser.close()
    print("Finished scraping enemy sprites.")

async def capture_canvas_screenshot(url: str, output_filename: str = "canvas.png"):
    """
    Launches a browser, navigates to the Margonem URL, and takes a screenshot of the canvas element.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        print(f"Navigating to {url}...")
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            print("Page loaded successfully.")
            # Wait for the canvas to appear
            await page.wait_for_selector('canvas', timeout=30000)
            canvas = await page.query_selector('canvas')
            if canvas:
                print("Canvas found. Taking screenshot...")
                await canvas.screenshot(path=output_filename)
                print(f"Canvas screenshot saved to {output_filename}")
            else:
                print("Canvas element not found!")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            await browser.close()
            print("Browser closed.")

async def find_enemies_on_canvas(canvas_screenshot_path, template_dir, threshold=0.7):
    """
    Find enemy sprites on the canvas screenshot using template matching.
    Returns a list of tuples (enemy_name, match_position, match_confidence).
    """
    print(f"Looking for enemies in {canvas_screenshot_path}...")
    
    # Read the canvas screenshot
    canvas_img = cv2.imread(canvas_screenshot_path)
    if canvas_img is None:
        print(f"Error: Could not read canvas screenshot at {canvas_screenshot_path}")
        return []
    
    # Convert to grayscale for better matching
    canvas_gray = cv2.cvtColor(canvas_img, cv2.COLOR_BGR2GRAY)
    
    results = []
    
    # Loop through all enemy templates
    for filename in os.listdir(template_dir):
        if not (filename.endswith('.png') or filename.endswith('.gif') or filename.endswith('.jpg')):
            continue
            
        template_path = os.path.join(template_dir, filename)
        
        # For GIF files, we need to extract the first frame
        if filename.endswith('.gif'):
            try:
                with Image.open(template_path) as img:
                    # Convert PIL Image to cv2 format
                    img_array = np.array(img.convert('RGB'))
                    template_img = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            except Exception as e:
                print(f"Error processing GIF {filename}: {e}")
                continue
        else:
            # For PNG/JPG, read directly
            template_img = cv2.imread(template_path)
            
        if template_img is None:
            print(f"Could not read template {filename}")
            continue
            
        # Convert template to grayscale
        template_gray = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)
        
        # Apply template matching
        res = cv2.matchTemplate(canvas_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        
        # Get positions where match exceeds threshold
        loc = np.where(res >= threshold)
        
        for pt in zip(*loc[::-1]):  # Switch columns and rows
            # Get the match confidence at this point
            confidence = res[pt[1], pt[0]]
            
            # Get enemy name from filename (remove level and extension)
            enemy_name = os.path.splitext(filename)[0]
            enemy_name = enemy_name.split('_lvl')[0]
            
            results.append({
                'name': enemy_name,
                'position': pt,  # (x, y) coordinates
                'confidence': float(confidence),
                'width': template_gray.shape[1],
                'height': template_gray.shape[0]
            })
    
    # Sort by confidence (highest first)
    results.sort(key=lambda x: x['confidence'], reverse=True)
    print(f"Found {len(results)} potential enemy matches")
    
    return results

async def find_and_fight_enemies(url: str):
    """
    Main bot function that captures the canvas, finds enemies, and clicks on them.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        print("Page loaded. Waiting for login...")
        
        # Wait for user to manually log in (we can automate this later)
        input("Please log in manually and press Enter when ready...")
        
        while True:
            try:
                # Ensure we have the canvas
                canvas = await page.query_selector('canvas')
                if not canvas:
                    print("Canvas not found! Waiting...")
                    await asyncio.sleep(2)
                    continue
                
                # Take a screenshot of the canvas
                await canvas.screenshot(path="current_canvas.png")
                
                # Find enemies on the canvas
                enemies_dir = os.path.join("templates", "enemies")
                enemies = await find_enemies_on_canvas("current_canvas.png", enemies_dir)
                
                if not enemies:
                    print("No enemies found. Waiting...")
                    await asyncio.sleep(2)
                    continue
                
                # Get canvas dimensions for center calculation
                canvas_size = await page.evaluate("""() => {
                    const canvas = document.querySelector('canvas');
                    return { width: canvas.width, height: canvas.height };
                }""")
                
                center_x = canvas_size['width'] / 2
                center_y = canvas_size['height'] / 2
                
                # Find the closest enemy to the center of the screen
                closest_enemy = None
                closest_distance = float('inf')
                
                for enemy in enemies:
                    # Calculate center point of the enemy
                    enemy_center_x = enemy['position'][0] + enemy['width'] / 2
                    enemy_center_y = enemy['position'][1] + enemy['height'] / 2
                    
                    # Calculate distance from center
                    distance = ((enemy_center_x - center_x) ** 2 + (enemy_center_y - center_y) ** 2) ** 0.5
                    
                    if distance < closest_distance:
                        closest_distance = distance
                        closest_enemy = enemy
                
                if closest_enemy:
                    print(f"Found closest enemy: {closest_enemy['name']} at position {closest_enemy['position']}")
                    
                    # Calculate click position (center of the enemy)
                    click_x = closest_enemy['position'][0] + closest_enemy['width'] / 2
                    click_y = closest_enemy['position'][1] + closest_enemy['height'] / 2
                    
                    # Click on the enemy
                    await page.mouse.click(click_x, click_y)
                    print(f"Clicked at position ({click_x}, {click_y})")
                    
                    # Look for and click the "Fight" button
                    # This part depends on the game's UI, we may need to adjust selectors
                    try:
                        fight_button = await page.wait_for_selector('button:has-text("Fight")', timeout=3000)
                        if fight_button:
                            await fight_button.click()
                            print("Clicked Fight button")
                            
                            # Wait for fight to complete
                            await asyncio.sleep(5)  # Adjust based on typical fight duration
                    except Exception as e:
                        print(f"Could not find or click Fight button: {e}")
                
                # Wait a bit before next iteration
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"An error occurred: {e}")
                await asyncio.sleep(5)
            
            # Optional: Add a way to exit the loop
            if input("Press Enter to continue, 'q' to quit: ").lower() == 'q':
                break
                
        await browser.close()
        print("Browser closed.")

if __name__ == "__main__":
    margonem_url = "https://gordion.margonem.pl/"
    # Choose which function to run
    print("Choose an operation:")
    print("1. Capture canvas screenshot")
    print("2. Run bot (detect and fight enemies)")
    
    choice = input("Enter choice (1 or 2): ")
    
    if choice == "1":
        asyncio.run(capture_canvas_screenshot(margonem_url, output_filename="canvas.png"))
    elif choice == "2":
        asyncio.run(find_and_fight_enemies(margonem_url))
    else:
        print("Invalid choice!")