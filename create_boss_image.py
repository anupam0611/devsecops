"""Image creation module for generating boss character images.

This module provides functionality to create and manipulate boss character
images using PIL (Python Imaging Library)..
"""

import os
from PIL import Image, ImageDraw, ImageFont


def create_boss_image(name, health, attack, defense, output_path, width=800, height=600, 
                     background_color=(50, 50, 50), text_color=(255, 255, 255)):
    """
    Create a boss character image with stats.

    Args:
        name (str): Boss character name
        health (int): Boss health points
        attack (int): Boss attack power
        defense (int): Boss defense power
        output_path (str): Path to save the image
        width (int): Image width in pixels
        height (int): Image height in pixels
        background_color (tuple): RGB background color
        text_color (tuple): RGB text color

    Returns:
        bool: True if image was created successfully, False otherwise
    """
    try:
        # Create base image
        image = Image.new('RGB', (width, height), background_color)
        draw = ImageDraw.Draw(image)

        # Load font
        font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'arial.ttf')
        title_font = ImageFont.truetype(font_path, 40)
        stats_font = ImageFont.truetype(font_path, 30)

        # Draw title
        title = f"BOSS: {name}"
        title_width = draw.textlength(title, font=title_font)
        draw.text(
            ((width - title_width) // 2, 50),
            title,
            font=title_font,
            fill=text_color
        )

        # Draw stats
        stats = [
            f"Health: {health}",
            f"Attack: {attack}",
            f"Defense: {defense}"
        ]
        y_position = 150
        for stat in stats:
            draw.text(
                (50, y_position),
                stat,
                font=stats_font,
                fill=text_color
            )
            y_position += 50

        # Save image
        image.save(output_path)
        return True
    except Exception as e:
        print(f"Error creating boss image: {str(e)}")
        return False


if __name__ == '__main__':
    create_boss_image()
