"""Image download module for boss character images.

This module provides functionality to download boss character images
from a specified URL and save them locally.
"""

import os
import requests

# Configuration constants
BOSS_IMAGE_URL = "https://example.com/boss_images"
OUTPUT_DIRECTORY = "static/uploads"


def download_boss_image(image_id, timeout=30):
    """
    Download a boss character image from the server.

    Args:
        image_id (str): The ID of the boss image to download
        timeout (int): Request timeout in seconds

    Returns:
        bool: True if download was successful, False otherwise
    """
    try:
        # Create output directory if it doesn't exist
        if not os.path.exists(OUTPUT_DIRECTORY):
            os.makedirs(OUTPUT_DIRECTORY)

        # Construct file paths
        image_url = f"{BOSS_IMAGE_URL}/{image_id}.jpg"
        output_path = os.path.join(OUTPUT_DIRECTORY, f"boss_{image_id}.jpg")

        # Download image
        response = requests.get(image_url, timeout=timeout)
        response.raise_for_status()

        # Save image
        with open(output_path, "wb") as f:
            f.write(response.content)

        return True
    except requests.RequestException as e:
        print(f"Error downloading boss image: {str(e)}")
        return False
    except IOError as e:
        print(f"Error saving boss image: {str(e)}")
        return False
