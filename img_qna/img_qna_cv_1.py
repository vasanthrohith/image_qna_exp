import cv2
import numpy as np
import os
import time

# --- Global variables ---
drawing = False         # Flag for drawing state
panning = False         # Flag for panning state
ix, iy = -1, -1         # Initial starting coordinates (original image space)
ex, ey = -1, -1         # Current/End coordinates (original image space)
img = None              # Original image (starts grayscale, becomes BGR after 1st rect)
img_display = None      # Image currently being displayed (zoomed/panned view)
window_name = "Image Viewer (Grayscale Base)" # Updated window name
original_image_path = r"C:\Users\CVHS ADMIN\Documents\github_repos\image_qna\source_images\SID.jpg" # Store the original path

# Zoom/Pan parameters
zoom_scale = 1.0        # Current zoom level
max_zoom = 10.0         # Maximum zoom factor
min_zoom = 0.1          # Minimum zoom factor
center_x, center_y = 0, 0 # Center coordinates of the view in the original image
pan_start_x, pan_start_y = 0, 0 # Mouse position when panning starts
center_start_x, center_start_y = 0, 0 # Image center when panning starts

# --- Configuration ---
RECT_COLOR = (0, 0, 255)  # Red color for permanent rectangles (BGR)
RECT_THICKNESS = 4        # Thickness for permanent rectangles
TEMP_RECT_COLOR = (0, 255, 0) # Green color for temporary rectangle (BGR)
TEMP_RECT_THICKNESS = 1


# --- Helper Functions ---

def update_display_image():
    """
    Updates the img_display based on the current zoom_scale and center coordinates.
    Handles cropping and resizing from img (which can be grayscale or BGR).
    """
    global img, img_display, zoom_scale, center_x, center_y, window_name

    if img is None:
        print("Error: Original image is None in update_display_image.")
        return

    # Determine if image is grayscale (2D) or BGR (3D)
    is_bgr = len(img.shape) == 3
    img_h, img_w = img.shape[:2]

    # Get the current dimensions of the window
    try:
        rect = cv2.getWindowImageRect(window_name)
        win_w, win_h = rect[2], rect[3]
        if win_h <= 0 or win_w <= 0:
             print("Warning: Window size reported as zero or negative. Using fallback.")
             if img_display is not None and img_display.shape[0] > 0 and img_display.shape[1] > 0:
                 win_h, win_w = img_display.shape[:2]
             else:
                 win_h, win_w = img_h, img_w
    except cv2.error:
        print("Warning: cv2.getWindowImageRect error. Using fallback size.")
        if img_display is not None and img_display.shape[0] > 0 and img_display.shape[1] > 0:
             win_h, win_w = img_display.shape[:2]
        else:
             win_h, win_w = img_h, img_w

    # Calculate the dimensions of the view in the original image coordinates
    view_h = max(1, int(win_h / zoom_scale))
    view_w = max(1, int(win_w / zoom_scale))

    # Calculate the top-left corner of the view in the original image
    top_left_x = max(0, int(center_x - view_w / 2))
    top_left_y = max(0, int(center_y - view_h / 2))

    # Calculate the bottom-right corner, ensuring it doesn't exceed image bounds
    bottom_right_x = min(img_w, top_left_x + view_w)
    bottom_right_y = min(img_h, top_left_y + view_h)

    # Adjust top-left if bottom-right hit the boundary
    top_left_x = max(0, bottom_right_x - view_w)
    top_left_y = max(0, bottom_right_y - view_h)

    # Recalculate actual cropped dimensions
    cropped_w = bottom_right_x - top_left_x
    cropped_h = bottom_right_y - top_left_y

    if cropped_w <= 0 or cropped_h <= 0:
        print(f"Warning: Invalid view dimensions calculated (w={cropped_w}, h={cropped_h}). Displaying black.")
        # Create a black image matching the expected channels
        num_channels = 3 if is_bgr else 1
        img_display = np.zeros((max(1, win_h), max(1, win_w), num_channels) if is_bgr else (max(1, win_h), max(1, win_w)), dtype=np.uint8)
        return

    # Crop the region from the original image (grayscale or BGR)
    cropped_img = img[top_left_y:bottom_right_y, top_left_x:bottom_right_x]

    # Resize the cropped region to fit the window
    target_w = max(1, win_w)
    target_h = max(1, win_h)
    img_display = cv2.resize(cropped_img, (target_w, target_h), interpolation=cv2.INTER_LINEAR)

def window_to_original(x_win, y_win):
    """Converts window coordinates to original image coordinates."""
    global zoom_scale, center_x, center_y, img_display, img

    if img_display is None or img is None:
        print("Warning: Attempted coordinate conversion with invalid image state.")
        return x_win, y_win

    win_h, win_w = img_display.shape[:2]
    img_h, img_w = img.shape[:2]

    if win_h <= 0 or win_w <= 0:
         print("Warning: Invalid display image dimensions in window_to_original.")
         return 0, 0

    view_h_orig = max(1, int(win_h / zoom_scale))
    view_w_orig = max(1, int(win_w / zoom_scale))

    top_left_x_orig = max(0, int(center_x - view_w_orig / 2))
    top_left_y_orig = max(0, int(center_y - view_h_orig / 2))
    bottom_right_x_orig = min(img_w, top_left_x_orig + view_w_orig)
    bottom_right_y_orig = min(img_h, top_left_y_orig + view_h_orig)
    top_left_x_orig = max(0, bottom_right_x_orig - view_w_orig)
    top_left_y_orig = max(0, bottom_right_y_orig - view_h_orig)
    actual_view_w_orig = bottom_right_x_orig - top_left_x_orig
    actual_view_h_orig = bottom_right_y_orig - top_left_y_orig

    if actual_view_w_orig <= 0 or actual_view_h_orig <= 0:
        print("Warning: Invalid original view dimensions in window_to_original.")
        return 0, 0

    x_orig = int(top_left_x_orig + (x_win / win_w) * actual_view_w_orig)
    y_orig = int(top_left_y_orig + (y_win / win_h) * actual_view_h_orig)

    x_orig = max(0, min(img_w - 1, x_orig))
    y_orig = max(0, min(img_h - 1, y_orig))

    return x_orig, y_orig

def original_to_window(x_orig, y_orig):
    """Converts original image coordinates to window coordinates."""
    global zoom_scale, center_x, center_y, img_display, img

    if img_display is None or img is None:
        print("Warning: Attempted coordinate conversion with invalid image state.")
        return x_orig, y_orig

    win_h, win_w = img_display.shape[:2]
    img_h, img_w = img.shape[:2]

    if win_h <= 0 or win_w <= 0:
        print("Warning: Invalid display image dimensions in original_to_window.")
        return 0, 0

    view_h_orig = max(1, int(win_h / zoom_scale))
    view_w_orig = max(1, int(win_w / zoom_scale))

    top_left_x_orig = max(0, int(center_x - view_w_orig / 2))
    top_left_y_orig = max(0, int(center_y - view_h_orig / 2))
    bottom_right_x_orig = min(img_w, top_left_x_orig + view_w_orig)
    bottom_right_y_orig = min(img_h, top_left_y_orig + view_h_orig)
    top_left_x_orig = max(0, bottom_right_x_orig - view_w_orig)
    top_left_y_orig = max(0, bottom_right_y_orig - view_h_orig)
    actual_view_w_orig = bottom_right_x_orig - top_left_x_orig
    actual_view_h_orig = bottom_right_y_orig - top_left_y_orig

    if actual_view_w_orig <= 0 or actual_view_h_orig <= 0:
         print("Warning: Invalid original view dimensions in original_to_window.")
         return 0, 0

    rel_x = x_orig - top_left_x_orig
    rel_y = y_orig - top_left_y_orig

    if rel_x < 0 or rel_x >= actual_view_w_orig or rel_y < 0 or rel_y >= actual_view_h_orig:
        return -1, -1 # Indicate point is not visible

    x_win = int((rel_x / actual_view_w_orig) * win_w)
    y_win = int((rel_y / actual_view_h_orig) * win_h)

    x_win = max(0, min(win_w - 1, x_win))
    y_win = max(0, min(win_h - 1, y_win))

    return x_win, y_win


# --- Mouse callback function ---
def handle_mouse_events(event, x, y, flags, param):
    global drawing, panning, ix, iy, ex, ey, img, img_display
    global zoom_scale, center_x, center_y, pan_start_x, pan_start_y, center_start_x, center_start_y

    if img is None: return

    img_h, img_w = img.shape[:2] # Get original image dimensions

    current_x_orig, current_y_orig = window_to_original(x, y)

    if event == cv2.EVENT_LBUTTONDOWN:
        if not panning:
            drawing = True
            ix, iy = current_x_orig, current_y_orig
            ex, ey = ix, iy

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            ex, ey = current_x_orig, current_y_orig
        elif panning:
            dx = x - pan_start_x
            dy = y - pan_start_y
            if zoom_scale != 0:
                center_x = center_start_x - dx / zoom_scale
                center_y = center_start_y - dy / zoom_scale
            center_x = max(0, min(img_w, center_x))
            center_y = max(0, min(img_h, center_y))
            update_display_image()

    elif event == cv2.EVENT_LBUTTONUP:
        if drawing:
            drawing = False
            ex, ey = current_x_orig, current_y_orig
            if img is not None:
                start_x, end_x = min(ix, ex), max(ix, ex)
                start_y, end_y = min(iy, ey), max(iy, ey)

                if start_x < end_x and start_y < end_y:
                    # --- Convert img to BGR if it's still Grayscale ---
                    if len(img.shape) == 2:
                        print("Converting base image to BGR to draw color rectangle...")
                        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

                    # --- Draw permanent THICK RED rectangle on the BGR image ---
                    cv2.rectangle(img, (start_x, start_y), (end_x, end_y), color=RECT_COLOR, thickness=RECT_THICKNESS)
                    print(f"Red rectangle drawn on original image at [({start_x},{start_y}), ({end_x},{end_y})]")
                    update_display_image() # Update display to show the new permanent rectangle
                else:
                    print("Rectangle not drawn (zero width or height).")


    elif event == cv2.EVENT_MBUTTONDOWN:
        panning = True
        pan_start_x, pan_start_y = x, y
        center_start_x, center_start_y = center_x, center_y
        cv2.setWindowProperty(window_name, cv2.WND_PROP_CURSOR, cv2.CURSOR_CROSSHAIR)

    elif event == cv2.EVENT_MBUTTONUP:
        panning = False
        cv2.setWindowProperty(window_name, cv2.WND_PROP_CURSOR, cv2.CURSOR_ARROW)


    elif event == cv2.EVENT_MOUSEWHEEL:
        mouse_x_orig_before, mouse_y_orig_before = window_to_original(x, y)

        if flags > 0: zoom_factor = 1.1
        else: zoom_factor = 1 / 1.1

        new_zoom_scale = zoom_scale * zoom_factor
        new_zoom_scale = max(min_zoom, min(max_zoom, new_zoom_scale))

        if new_zoom_scale != zoom_scale:
             old_zoom_scale = zoom_scale
             zoom_scale = new_zoom_scale

             center_x = mouse_x_orig_before - (mouse_x_orig_before - center_x) * (old_zoom_scale / zoom_scale)
             center_y = mouse_y_orig_before - (mouse_y_orig_before - center_y) * (old_zoom_scale / zoom_scale)

             center_x = max(0, min(img_w, center_x))
             center_y = max(0, min(img_h, center_y))

             update_display_image()

# --- Function to Save Image ---
def save_image():
    """Saves the modified image (img) to the local directory."""
    global img, original_image_path

    if img is None or not original_image_path:
        print("Error: Cannot save. Image not loaded or original path missing.")
        return

    try:
        # Construct output path
        directory = os.path.dirname(original_image_path)
        filename, ext = os.path.splitext(os.path.basename(original_image_path))
        output_filename = f"{filename}_modified_rects{ext}"
        output_path = os.path.join(directory, output_filename)

        # Delete existing file if it exists
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
                print(f"Old modified image removed: {output_path}")
            except Exception as del_err:
                print(f"Warning: Could not delete old file: {del_err}")

        # Save the new image
        success = cv2.imwrite(output_path, img)

        if success:
            print(f"✅ Image successfully saved to: {output_path}")
        else:
            print(f"❌ Error: Failed to save image to {output_path}")
            print("Check directory permissions and disk space.")

    except Exception as e:
        print(f"An error occurred during saving: {e}")

# --- Main Program ---

# !!! IMPORTANT: Replace this with the actual path to YOUR image !!!
original_image_path = r"C:\Users\CVHS ADMIN\Documents\github_repos\image_qna\source_images\SID.jpg"
print(f"Attempting to load image from: {original_image_path}")

if not os.path.exists(original_image_path):
    print(f"Error: Image file not found at path: {original_image_path}")
    exit()
if not os.path.isfile(original_image_path):
     print(f"Error: Path exists but is not a file: {original_image_path}")
     exit()

try:
    # Load the image in color first
    loaded_img = cv2.imread(original_image_path)
    if loaded_img is None:
        print(f"Error: cv2.imread returned None. Check path, integrity, permissions: {original_image_path}")
        exit()
    else:
        print(f"Image loaded successfully. Original shape: {loaded_img.shape}")
        # --- Convert to Grayscale INITIALLY ---
        img = cv2.cvtColor(loaded_img, cv2.COLOR_BGR2GRAY)
        print(f"Image initially converted to grayscale. Shape: {img.shape}")
        # Initialize center for the grayscale image
        center_y, center_x = img.shape[0] // 2, img.shape[1] // 2
        del loaded_img # Release color image memory

except Exception as e:
    print(f"An error occurred during image loading or conversion: {e}")
    exit()

# Create a window and set the mouse callback
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO | cv2.WINDOW_GUI_EXPANDED)
cv2.resizeWindow(window_name, 800, 600)
cv2.setMouseCallback(window_name, handle_mouse_events)

# Initial display update
update_display_image()
if img_display is None:
     print("Error: Initial display update failed. Exiting.")
     exit()


print("-" * 30)
print("Controls:")
print(f" - Left-click and drag: Draw rectangle (thick red, thickness={RECT_THICKNESS}).")
print(" - Mouse wheel: Zoom in/out.")
print(" - Middle-click and drag: Pan image.")
print(" - 's': Save the image with drawn rectangles.")
print(" - 'r': Reset view (zoom and pan).")
print(" - ESC: Exit.")
print("-" * 30)

while True:
    if img_display is None:
        print("Error: Display image became None in main loop. Attempting recovery.")
        update_display_image()
        if img_display is None:
            print("Recovery failed. Exiting.")
            break

    # Base frame to display is the current view (can be grayscale or BGR)
    frame_to_show = img_display.copy() # Work on a copy

    # If currently drawing, draw the temporary rectangle
    if drawing:
        # Convert the original start/end rectangle coordinates to window coordinates
        ix_win, iy_win = original_to_window(ix, iy)
        ex_win, ey_win = original_to_window(ex, ey)

        # Only draw temporary rectangle if it's within the window bounds
        if ix_win != -1 and iy_win != -1 and ex_win != -1 and ey_win != -1:
             # --- Convert frame_to_show to color if it's grayscale ---
             # This ensures we can draw the green temporary rectangle
             if len(frame_to_show.shape) == 2:
                 frame_to_show = cv2.cvtColor(frame_to_show, cv2.COLOR_GRAY2BGR)

             # Draw the feedback rectangle (GREEN) on the BGR frame_to_show
             cv2.rectangle(frame_to_show, (ix_win, iy_win), (ex_win, ey_win), color=TEMP_RECT_COLOR, thickness=TEMP_RECT_THICKNESS)

    # --- Show the frame (grayscale, BGR, or BGR with temp rectangle) ---
    if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) >= 1:
        cv2.imshow(window_name, frame_to_show)
    else:
        print("Window closed by user. Exiting loop.")
        break

    # --- Wait for key press & allow GUI event processing ---
    key = cv2.waitKey(15) & 0xFF

    if key == 27: # ESC key
        print("ESC key pressed. Exiting...")
        break
    elif key == ord('r'): # Reset view key
        print("Resetting view...")
        zoom_scale = 1.0
        if img is not None:
            center_y, center_x = img.shape[0] // 2, img.shape[1] // 2
        update_display_image()
    elif key == ord('s'): # Save key
        print("Save key pressed.")
        save_image()

from get_img_qna_response import get_image_qna 


# Release resources
if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) >= 1:
    cv2.destroyWindow(window_name)
print("Window closed.")

get_image_qna()


