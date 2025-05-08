import cv2
import numpy as np
import os
from PIL import Image
import argparse

def debug_template_matching(canvas_path, template_dir, output_path="debug_result.png", threshold=0.7):
    """
    Visualize template matching results by drawing rectangles around detected enemies.
    
    Args:
        canvas_path: Path to the canvas screenshot
        template_dir: Directory containing enemy templates
        output_path: Path to save the visualization result
        threshold: Matching threshold (0.0 to 1.0)
    """
    # Read the canvas screenshot
    canvas_img = cv2.imread(canvas_path)
    if canvas_img is None:
        print(f"Error: Could not read canvas screenshot at {canvas_path}")
        return
    
    # Make a copy for visualization
    visualization = canvas_img.copy()
    canvas_gray = cv2.cvtColor(canvas_img, cv2.COLOR_BGR2GRAY)
    
    print(f"Looking for templates in {template_dir}...")
    found_count = 0
    
    # Loop through all enemy templates
    for filename in os.listdir(template_dir):
        if not (filename.endswith('.png') or filename.endswith('.gif') or filename.endswith('.jpg')):
            continue
            
        template_path = os.path.join(template_dir, filename)
        
        # For GIF files, we need to extract the first frame
        if filename.endswith('.gif'):
            try:
                with Image.open(template_path) as img:
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
        template_w, template_h = template_gray.shape[::-1]
        
        # Apply template matching
        res = cv2.matchTemplate(canvas_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        
        # Get positions where match exceeds threshold
        loc = np.where(res >= threshold)
        match_count = 0
        
        # Draw rectangles and labels for this template
        for pt in zip(*loc[::-1]):  # Switch columns and rows
            match_count += 1
            found_count += 1
            
            # Get the match confidence at this point
            confidence = res[pt[1], pt[0]]
            
            # Generate random color for this template type (consistent for same template)
            color_hash = hash(filename) % 255
            color = (color_hash, (color_hash + 85) % 255, (color_hash + 170) % 255)
            
            # Draw rectangle
            cv2.rectangle(visualization, pt, (pt[0] + template_w, pt[1] + template_h), color, 2)
            
            # Add text label with enemy name and confidence
            enemy_name = os.path.splitext(filename)[0]
            label = f"{enemy_name} ({confidence:.2f})"
            cv2.putText(visualization, label, (pt[0], pt[1] - 5), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
            
        if match_count > 0:
            print(f"Found {match_count} matches for {filename}")
    
    print(f"Total matches found: {found_count}")
    
    # Add threshold information to the image
    threshold_text = f"Threshold: {threshold}"
    cv2.putText(visualization, threshold_text, (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
    
    # Save the visualization
    cv2.imwrite(output_path, visualization)
    print(f"Visualization saved to {output_path}")
    
    return visualization

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Debug template matching for enemy detection")
    parser.add_argument("--canvas", default="canvas.png", help="Path to the canvas screenshot")
    parser.add_argument("--templates", default="templates/enemies", help="Directory containing enemy templates")
    parser.add_argument("--output", default="debug_result.png", help="Path to save visualization result")
    parser.add_argument("--threshold", type=float, default=0.7, help="Matching threshold (0.0 to 1.0)")
    
    args = parser.parse_args()
    
    # Run the debug visualization
    result = debug_template_matching(
        args.canvas, 
        args.templates, 
        args.output, 
        args.threshold
    )
    
    # Display the result if running in an environment with display
    try:
        cv2.imshow("Template Matching Debug", result)
        print("Press any key to close the visualization window...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except:
        print("Could not display the result - no display available or OpenCV display error.")
        print(f"The result has been saved to {args.output}") 