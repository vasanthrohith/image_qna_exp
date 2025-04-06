# import cv2
# import numpy as np
# import os
# import time # Import time for potential timestamped filenames if needed

# from get_img_qna_response import get_image_qna # Import the function to get QnA response

# # --- Global variables ---
# drawing = False         # Flag for drawing state
# panning = False         # Flag for panning state
# ix, iy = -1, -1         # Initial starting coordinates (original image space)
# ex, ey = -1, -1         # Current/End coordinates (original image space)
# img = None              # Original, full-resolution image (rectangles drawn here)
# img_display = None      # Image currently being displayed (zoomed/panned view)
# window_name = "Image Viewer" # Define window name globally
# original_image_path = r"C:\Users\CVHS ADMIN\Documents\github_repos\image_qna\source_images\SID.jpg" # Store the original path

# # Zoom/Pan parameters
# zoom_scale = 1.0        # Current zoom level
# max_zoom = 10.0         # Maximum zoom factor
# min_zoom = 0.1          # Minimum zoom factor
# center_x, center_y = 0, 0 # Center coordinates of the view in the original image
# pan_start_x, pan_start_y = 0, 0 # Mouse position when panning starts
# center_start_x, center_start_y = 0, 0 # Image center when panning starts

# # --- Helper Functions ---

# def update_display_image():
#     """
#     Updates the img_display based on the current zoom_scale and center coordinates.
#     Handles cropping and resizing.
#     """
#     global img, img_display, zoom_scale, center_x, center_y, window_name

#     if img is None:
#         print("Error: Original image is None in update_display_image.")
#         return

#     # Get the current dimensions of the window
#     try:
#         # Use getWindowImageRect which returns (x, y, width, height)
#         rect = cv2.getWindowImageRect(window_name)
#         win_w, win_h = rect[2], rect[3]
#         if win_h <= 0 or win_w <= 0: # Handle case where window might not be ready or minimized
#              print("Warning: Window size reported as zero or negative. Using fallback.")
#              # Fallback to a default or previous known good size if possible
#              # If img_display exists, use its size, otherwise original image size
#              if img_display is not None and img_display.shape[0] > 0 and img_display.shape[1] > 0:
#                  win_h, win_w = img_display.shape[:2]
#              else:
#                  win_h, win_w = img.shape[0], img.shape[1] # Initial fallback
#     except cv2.error: # Handle cases where the window might not exist yet or is closed
#         print("Warning: cv2.getWindowImageRect error. Using fallback size.")
#         if img_display is not None and img_display.shape[0] > 0 and img_display.shape[1] > 0:
#              win_h, win_w = img_display.shape[:2]
#         else:
#              win_h, win_w = img.shape[0], img.shape[1] # Initial fallback

#     # Calculate the dimensions of the view in the original image coordinates
#     # Ensure view dimensions are at least 1 pixel
#     view_h = max(1, int(win_h / zoom_scale))
#     view_w = max(1, int(win_w / zoom_scale))

#     # Calculate the top-left corner of the view in the original image
#     top_left_x = max(0, int(center_x - view_w / 2))
#     top_left_y = max(0, int(center_y - view_h / 2))

#     # Calculate the bottom-right corner, ensuring it doesn't exceed image bounds
#     bottom_right_x = min(img.shape[1], top_left_x + view_w)
#     bottom_right_y = min(img.shape[0], top_left_y + view_h)

#     # Adjust top-left if bottom-right hit the boundary (to maintain view size as much as possible)
#     # This ensures the cropped width/height matches view_w/view_h unless at image edge
#     top_left_x = max(0, bottom_right_x - view_w)
#     top_left_y = max(0, bottom_right_y - view_h)

#     # Recalculate actual cropped dimensions based on adjusted top-left and bottom-right
#     cropped_w = bottom_right_x - top_left_x
#     cropped_h = bottom_right_y - top_left_y

#     if cropped_w <= 0 or cropped_h <= 0:
#         # Cannot crop a valid region, display black image or handle error
#         print(f"Warning: Invalid view dimensions calculated (w={cropped_w}, h={cropped_h}). Displaying black.")
#         img_display = np.zeros((max(1, win_h), max(1, win_w), 3), dtype=np.uint8)
#         return


#     # Crop the region from the original image
#     cropped_img = img[top_left_y:bottom_right_y, top_left_x:bottom_right_x]

#     # Resize the cropped region to fit the window
#     # Ensure target size for resize is positive
#     target_w = max(1, win_w)
#     target_h = max(1, win_h)
#     img_display = cv2.resize(cropped_img, (target_w, target_h), interpolation=cv2.INTER_LINEAR)

# def window_to_original(x_win, y_win):
#     """Converts window coordinates to original image coordinates."""
#     global zoom_scale, center_x, center_y, img_display, img

#     if img_display is None or img is None: # Check both images
#         print("Warning: Attempted coordinate conversion with invalid image state.")
#         return x_win, y_win # Fallback conversion

#     win_h, win_w = img_display.shape[:2]
#     if win_h <= 0 or win_w <= 0: # Prevent division by zero
#          print("Warning: Invalid display image dimensions in window_to_original.")
#          return 0, 0 # Or some other default

#     # Calculate the dimensions of the view in the original image coordinates
#     view_h_orig = max(1, int(win_h / zoom_scale))
#     view_w_orig = max(1, int(win_w / zoom_scale))

#     # Calculate the top-left corner of the view in the original image (consistent with update_display_image)
#     top_left_x_orig = max(0, int(center_x - view_w_orig / 2))
#     top_left_y_orig = max(0, int(center_y - view_h_orig / 2))
#     # Adjust based on potential boundary hits
#     bottom_right_x_orig = min(img.shape[1], top_left_x_orig + view_w_orig)
#     bottom_right_y_orig = min(img.shape[0], top_left_y_orig + view_h_orig)
#     top_left_x_orig = max(0, bottom_right_x_orig - view_w_orig)
#     top_left_y_orig = max(0, bottom_right_y_orig - view_h_orig)
#     actual_view_w_orig = bottom_right_x_orig - top_left_x_orig
#     actual_view_h_orig = bottom_right_y_orig - top_left_y_orig

#     if actual_view_w_orig <= 0 or actual_view_h_orig <= 0:
#         print("Warning: Invalid original view dimensions in window_to_original.")
#         return 0, 0

#     # Calculate the corresponding position in the original image
#     x_orig = int(top_left_x_orig + (x_win / win_w) * actual_view_w_orig)
#     y_orig = int(top_left_y_orig + (y_win / win_h) * actual_view_h_orig)

#     # Clamp coordinates to image bounds
#     x_orig = max(0, min(img.shape[1] - 1, x_orig))
#     y_orig = max(0, min(img.shape[0] - 1, y_orig))

#     return x_orig, y_orig

# def original_to_window(x_orig, y_orig):
#     """Converts original image coordinates to window coordinates."""
#     global zoom_scale, center_x, center_y, img_display, img

#     if img_display is None or img is None:
#         print("Warning: Attempted coordinate conversion with invalid image state.")
#         return x_orig, y_orig # Fallback

#     win_h, win_w = img_display.shape[:2]
#     if win_h <= 0 or win_w <= 0:
#         print("Warning: Invalid display image dimensions in original_to_window.")
#         return 0, 0

#     # Calculate the dimensions of the view in the original image coordinates
#     view_h_orig = max(1, int(win_h / zoom_scale))
#     view_w_orig = max(1, int(win_w / zoom_scale))

#     # Calculate the top-left corner of the view in the original image (consistent with update_display_image)
#     top_left_x_orig = max(0, int(center_x - view_w_orig / 2))
#     top_left_y_orig = max(0, int(center_y - view_h_orig / 2))
#     # Adjust based on potential boundary hits
#     bottom_right_x_orig = min(img.shape[1], top_left_x_orig + view_w_orig)
#     bottom_right_y_orig = min(img.shape[0], top_left_y_orig + view_h_orig)
#     top_left_x_orig = max(0, bottom_right_x_orig - view_w_orig)
#     top_left_y_orig = max(0, bottom_right_y_orig - view_h_orig)
#     actual_view_w_orig = bottom_right_x_orig - top_left_x_orig
#     actual_view_h_orig = bottom_right_y_orig - top_left_y_orig

#     if actual_view_w_orig <= 0 or actual_view_h_orig <= 0:
#          print("Warning: Invalid original view dimensions in original_to_window.")
#          return 0, 0

#     # Calculate relative position within the actual cropped original view
#     rel_x = x_orig - top_left_x_orig
#     rel_y = y_orig - top_left_y_orig

#     # Check if the original point is outside the current view
#     if rel_x < 0 or rel_x >= actual_view_w_orig or rel_y < 0 or rel_y >= actual_view_h_orig:
#         # Point is outside the current visible area, return (-1, -1) or clamp to edge?
#         # Returning (-1, -1) might be better to indicate it's off-screen
#         return -1, -1 # Indicate point is not visible

#     # Scale relative position to window coordinates
#     x_win = int((rel_x / actual_view_w_orig) * win_w)
#     y_win = int((rel_y / actual_view_h_orig) * win_h)

#     # Clamp to window bounds (should be within bounds if calculations are correct)
#     x_win = max(0, min(win_w - 1, x_win))
#     y_win = max(0, min(win_h - 1, y_win))

#     return x_win, y_win


# # --- Mouse callback function ---
# def handle_mouse_events(event, x, y, flags, param):
#     global drawing, panning, ix, iy, ex, ey, img, img_display
#     global zoom_scale, center_x, center_y, pan_start_x, pan_start_y, center_start_x, center_start_y

#     if img is None: return # Don't process events if image isn't loaded

#     current_x_orig, current_y_orig = window_to_original(x, y)

#     if event == cv2.EVENT_LBUTTONDOWN:
#         if not panning: # Only start drawing if not panning
#             drawing = True
#             ix, iy = current_x_orig, current_y_orig # Store original coords
#             ex, ey = ix, iy
#             # print(f"Draw Start (Orig): ({ix}, {iy})") # Debug

#     elif event == cv2.EVENT_MOUSEMOVE:
#         if drawing:
#             ex, ey = current_x_orig, current_y_orig # Update original coords
#             # print(f"Draw Move (Orig): ({ex}, {ey})") # Debug
#         elif panning:
#             # Calculate how much the mouse moved in window coordinates
#             dx = x - pan_start_x
#             dy = y - pan_start_y
#             # Convert the mouse movement to original image coordinate movement
#             # Note: Panning moves the *center* in the opposite direction of mouse drag
#             # Ensure zoom_scale is not zero before dividing
#             if zoom_scale != 0:
#                 center_x = center_start_x - dx / zoom_scale
#                 center_y = center_start_y - dy / zoom_scale
#             # Clamp center coordinates to valid range within the image
#             center_x = max(0, min(img.shape[1], center_x))
#             center_y = max(0, min(img.shape[0], center_y))
#             update_display_image() # Update view immediately during pan

#     elif event == cv2.EVENT_LBUTTONUP:
#         if drawing:
#             drawing = False
#             ex, ey = current_x_orig, current_y_orig # Final original coords
#             # print(f"Draw End (Orig): ({ex}, {ey})") # Debug
#             # Draw the permanent rectangle directly onto the *original* image
#             if img is not None:
#                 # Ensure coordinates are ordered correctly for drawing
#                 start_x, end_x = min(ix, ex), max(ix, ex)
#                 start_y, end_y = min(iy, ey), max(iy, ey)
#                 # Only draw if the rectangle has non-zero width and height
#                 if start_x < end_x and start_y < end_y:
#                     cv2.rectangle(img, (start_x, start_y), (end_x, end_y), color=(0, 0, 255), thickness=2) # Red permanent, adjust thickness as needed
#                     print(f"Rectangle drawn on original image at [({start_x},{start_y}), ({end_x},{end_y})]")
#                     update_display_image() # Update display to show the new permanent rectangle
#                 else:
#                     print("Rectangle not drawn (zero width or height).")


#     elif event == cv2.EVENT_MBUTTONDOWN: # Middle mouse button for panning
#         panning = True
#         pan_start_x, pan_start_y = x, y # Record mouse position in window coords
#         center_start_x, center_start_y = center_x, center_y # Record center position
#         cv2.setWindowProperty(window_name, cv2.WND_PROP_CURSOR, cv2.CURSOR_CROSSHAIR) # Change cursor during pan

#     elif event == cv2.EVENT_MBUTTONUP:
#         panning = False
#         cv2.setWindowProperty(window_name, cv2.WND_PROP_CURSOR, cv2.CURSOR_ARROW) # Restore cursor


#     elif event == cv2.EVENT_MOUSEWHEEL:
#         # Get current mouse position in original image coords BEFORE zoom changes
#         mouse_x_orig_before, mouse_y_orig_before = window_to_original(x, y)

#         # Determine zoom direction
#         if flags > 0: # Zoom in
#             zoom_factor = 1.1
#         else: # Zoom out
#             zoom_factor = 1 / 1.1

#         new_zoom_scale = zoom_scale * zoom_factor
#         # Clamp zoom scale
#         new_zoom_scale = max(min_zoom, min(max_zoom, new_zoom_scale))

#         # If zoom actually changed
#         if new_zoom_scale != zoom_scale:
#              old_zoom_scale = zoom_scale # Store old scale for center adjustment
#              zoom_scale = new_zoom_scale

#              # Adjust center to keep the point under the cursor stationary
#              # The amount the center needs to shift is proportional to the distance
#              # from the center to the mouse pointer, scaled by the change in zoom.
#              center_x = mouse_x_orig_before - (mouse_x_orig_before - center_x) * (old_zoom_scale / zoom_scale)
#              center_y = mouse_y_orig_before - (mouse_y_orig_before - center_y) * (old_zoom_scale / zoom_scale)


#              # Clamp center coordinates
#              center_x = max(0, min(img.shape[1], center_x))
#              center_y = max(0, min(img.shape[0], center_y))

#              # print(f"Zoom: {zoom_scale:.2f}, Center: ({center_x:.1f}, {center_y:.1f})") # Debug
#              update_display_image() # Update the display with new zoom/center

# # --- Function to Save Image ---
# def save_image():
#     """Saves the modified image (img) to the local directory."""
#     global img, original_image_path

#     if img is None or not original_image_path:
#         print("Error: Cannot save. Image not loaded or original path missing.")
#         return

#     try:
#         # Construct output path
#         directory = os.path.dirname(original_image_path)
#         filename, ext = os.path.splitext(os.path.basename(original_image_path))
#         output_filename = f"{filename}_modified{ext}"
#         output_path = os.path.join(directory, output_filename)

#         # Delete existing file if it exists
#         if os.path.exists(output_path):
#             try:
#                 os.remove(output_path)
#                 print(f"Old modified image removed: {output_path}")
#             except Exception as del_err:
#                 print(f"Warning: Could not delete old file: {del_err}")

#         # Save the new image
#         success = cv2.imwrite(output_path, img)

#         if success:
#             print(f"✅ Image successfully saved to: {output_path}")
#         else:
#             print(f"❌ Error: Failed to save image to {output_path}")
#             print("Check directory permissions and disk space.")

#     except Exception as e:
#         print(f"An error occurred during saving: {e}")
# # --- Main Program ---

# # !!! IMPORTANT: Replace this with the actual path to YOUR image !!!
# original_image_path = r"C:\Users\CVHS ADMIN\Documents\github_repos\image_qna\source_images\SID.jpg"
# # Store the path globally
# print(f"Attempting to load image from: {original_image_path}")

# # Check if the file exists before trying to load
# if not os.path.exists(original_image_path):
#     print(f"Error: Image file not found at path: {original_image_path}")
#     exit()
# if not os.path.isfile(original_image_path):
#      print(f"Error: Path exists but is not a file: {original_image_path}")
#      exit()

# try:
#     # Load the image
#     img = cv2.imread(original_image_path)
#     # Check immediately after loading
#     if img is None:
#         print(f"Error: cv2.imread returned None. Check the path, file integrity, and permissions: {original_image_path}")
#         exit()
#     else:
#         print(f"Image loaded successfully. Shape: {img.shape}")
#         # Initialize center to the middle of the image
#         center_y, center_x = img.shape[0] // 2, img.shape[1] // 2

# except Exception as e:
#     print(f"An error occurred during image loading: {e}")
#     exit()

# # Create a window and set the mouse callback
# cv2.namedWindow(window_name, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO | cv2.WINDOW_GUI_EXPANDED) # Flags for better resizing/GUI
# cv2.resizeWindow(window_name, 800, 600) # Set an initial reasonable window size
# cv2.setMouseCallback(window_name, handle_mouse_events) # Assign the callback function

# # Initial display update
# update_display_image()
# if img_display is None:
#      print("Error: Initial display update failed. Exiting.")
#      exit()


# print("-" * 30)
# print("Controls:")
# print(" - Left-click and drag: Draw rectangle.")
# print(" - Mouse wheel: Zoom in/out.")
# print(" - Middle-click and drag: Pan image.")
# print(" - 's': Save the image with drawn rectangles.")
# print(" - 'r': Reset view (zoom and pan).")
# print(" - ESC: Exit.")
# print("-" * 30)

# while True:
#     # Create a copy of the current display image for drawing temporary elements
#     if img_display is None:
#         # Attempt to recover if possible, or exit
#         print("Error: Display image became None in main loop. Attempting recovery.")
#         update_display_image()
#         if img_display is None:
#             print("Recovery failed. Exiting.")
#             break # Exit if display image isn't valid after recovery attempt

#     display_frame = img_display.copy()

#     # If currently drawing, draw the temporary rectangle on the display_frame
#     if drawing:
#         # Convert the original start/end rectangle coordinates to window coordinates
#         ix_win, iy_win = original_to_window(ix, iy)
#         ex_win, ey_win = original_to_window(ex, ey)

#         # Only draw temporary rectangle if it's within the window bounds
#         if ix_win != -1 and iy_win != -1 and ex_win != -1 and ey_win != -1:
#              # Draw the feedback rectangle (GREEN) on the *display* copy
#              cv2.rectangle(display_frame, (ix_win, iy_win), (ex_win, ey_win), color=(0, 255, 0), thickness=1) # Green temporary rectangle

#     # --- Show the potentially modified display frame ---
#     # Check if window still exists before showing
#     if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) >= 1:
#         cv2.imshow(window_name, display_frame)
#     else:
#         print("Window closed by user. Exiting loop.")
#         break # Exit loop if user closed the window

#     # --- Wait for key press & allow GUI event processing ---
#     key = cv2.waitKey(15) & 0xFF # Increased wait time slightly for smoother interaction

#     if key == 27: # ESC key
#         print("ESC key pressed. Exiting...")
#         break
#     elif key == ord('r'): # Reset view key
#         print("Resetting view...")
#         zoom_scale = 1.0
#         center_y, center_x = img.shape[0] // 2, img.shape[1] // 2
#         update_display_image()
#     elif key == ord('s'): # Save key
#         print("Save key pressed.")
#         save_image() # Call the save function


# # Release resources
# # Check if window still exists before trying to destroy it
# if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) >= 1:
#     cv2.destroyWindow(window_name)
# # cv2.destroyAllWindows() # Use destroyWindow for specific window if needed elsewhere
# print("Window closed.")
# get_image_qna()

# # addons
# # need to make the img bnw before drawing rectange as the org image has some color it may affect our marking