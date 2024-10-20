import os
from PIL import Image

"""
add opacity + padding to all icons in './icons' and save them to './frontend/static/assets/icons
"""

# Define the path to the folder containing the images
folder_path = "icons"

# Define the new canvas size
new_width = 850
new_height = 850

# Loop through each image in the folder
for filename in os.listdir(folder_path):
    # Open the image
    img = Image.open(os.path.join(folder_path, filename))

    # Get the original image size
    width, height = img.size

    # Create a new image with the desired canvas size
    new_img = Image.new("RGBA", (new_width, new_height), (0, 0, 0, 0))

    # Calculate the position of the original image in the new canvas
    left = (new_width - width) // 2
    top = (new_height - height) // 2

    # Paste the original image in the center of the new canvas
    new_img.paste(img, (left, top))

    # Add transparency (alpha channel) to the new image
    pixels = new_img.load()
    for x in range(new_width):
        for y in range(new_height):
            r, g, b, a = pixels[x, y]
            if a > 0:
                pixels[x, y] = (r, g, b, 100)

    # Save the new image
    new_img.save(os.path.join("frontend/static/assets/icons", filename))
