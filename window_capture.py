import pygetwindow as gw
import mss
import mss.tools

def list_and_select_window():
    """Lists all open windows and lets the user select one."""
    windows = gw.getAllTitles()
    print("Available windows:")
    for i, title in enumerate(windows):
        if title:  # Only display non-empty titles
            print(f"{i}: {title}")

    while True:
        try:
            choice = int(input("Enter the number of the window you want to capture: "))
            if 0 <= choice < len(windows) and windows[choice]:
                return windows[choice]
            else:
                print("Invalid choice. Please enter a valid number from the list.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except IndexError:
            print("Invalid choice. Please enter a valid number from the list.")


def capture_selected_window(window_title):
    """Captures a screenshot of the specified window."""
    try:
        # Get the specific window by title
        win = gw.getWindowsWithTitle(window_title)
        if not win:
            print(f"Error: Window with title '{window_title}' not found.")
            return False
        
        # Get the first window if multiple have the same title
        target_window = win[0]

        # Activate the window (optional, but can help ensure it's drawn correctly)
        # try:
        #     target_window.activate()
        # except Exception as e:
        #     print(f"Could not activate window: {e} (continuing anyway)")

        # Get window geometry
        # Ensure the window is not minimized for accurate geometry
        if target_window.isMinimized:
            target_window.restore()
            # Add a small delay to allow the window to restore
            import time
            time.sleep(0.5)
            
        x, y, width, height = target_window.left, target_window.top, target_window.width, target_window.height

        if width <= 0 or height <= 0:
            print(f"Error: Window '{window_title}' has invalid dimensions (width: {width}, height: {height}). It might be minimized or not rendered.")
            return False

        print(f"Capturing window: '{window_title}' at L:{x} T:{y} W:{width} H:{height}")

        # Capture the screen region of the window
        with mss.mss() as sct:
            monitor = {"top": y, "left": x, "width": width, "height": height}
            sct_img = sct.grab(monitor)
            
            # Save to a file
            output_filename = f"{window_title.replace(' ', '_').replace('.', '')}_screenshot.png"
            mss.tools.to_png(sct_img.rgb, sct_img.size, output=output_filename)
            print(f"Screenshot saved as {output_filename}")
            return True

    except Exception as e:
        print(f"An error occurred: {e}")
        return False

if __name__ == "__main__":
    selected_title = list_and_select_window()
    if selected_title:
        capture_selected_window(selected_title) 