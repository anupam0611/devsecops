"""
Image creation module for boss character images.

This module provides functionality to create boss character images
and save them locally.
"""

import os
from PIL import Image, ImageDraw, ImageFont

# Configuration constants
OUTPUT_DIRECTORY = "static/uploads"
FONT_PATH = "static/fonts/arial.ttf"
FONT_SIZE = 36


def create_boss_image(image_id, boss_name, boss_level):
    """
    Create a boss character image with text overlay.

    Args:
        image_id (str): The ID of the boss image to create
        boss_name (str): The name of the boss
        boss_level (int): The level of the boss

    Returns:
        bool: True if image creation was successful, False otherwise
    """
    try:
        # Create output directory if it doesn't exist
        if not os.path.exists(OUTPUT_DIRECTORY):
            os.makedirs(OUTPUT_DIRECTORY)

        # Create a blank image
        image = Image.new("RGB", (400, 300), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)

        # Load font
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

        # Add text to the image
        draw.text(
            (50, 100),
            f"Boss: {boss_name}\nLevel: {boss_level}",
            fill=(0, 0, 0),
            font=font,
        )

        # Save the image
        output_path = os.path.join(OUTPUT_DIRECTORY, f"boss_{image_id}.jpg")
        image.save(output_path)

        return True
    except IOError as e:
        print(f"Error creating boss image: {str(e)}")
        return False
