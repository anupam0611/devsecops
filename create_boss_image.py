from PIL import Image, ImageDraw, ImageFont
import os

def create_boss_speaker_image():
    # Create a new image with a white background
    width = 800
    height = 600
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Draw a speaker shape
    speaker_color = (50, 50, 50)  # Dark gray
    speaker_width = 400
    speaker_height = 300
    speaker_x = (width - speaker_width) // 2
    speaker_y = (height - speaker_height) // 2
    
    # Draw main speaker body
    draw.rectangle(
        [(speaker_x, speaker_y), (speaker_x + speaker_width, speaker_y + speaker_height)],
        fill=speaker_color,
        outline='black',
        width=2
    )
    
    # Draw speaker grille
    grille_color = (30, 30, 30)
    grille_spacing = 20
    for x in range(speaker_x + 20, speaker_x + speaker_width - 20, grille_spacing):
        for y in range(speaker_y + 20, speaker_y + speaker_height - 20, grille_spacing):
            draw.ellipse(
                [(x, y), (x + 10, y + 10)],
                fill=grille_color
            )
    
    # Add BOSS logo
    try:
        font = ImageFont.truetype("arial.ttf", 60)
    except:
        font = ImageFont.load_default()
    
    text = "BOSS"
    text_color = (255, 255, 255)  # White
    text_x = speaker_x + (speaker_width - draw.textlength(text, font=font)) // 2
    text_y = speaker_y + speaker_height + 50
    draw.text((text_x, text_y), text, fill=text_color, font=font)
    
    # Save the image
    if not os.path.exists('static/uploads'):
        os.makedirs('static/uploads')
    image.save('static/uploads/boss_speaker.jpg', 'JPEG')
    print("BOSS speaker image created successfully!")

if __name__ == '__main__':
    create_boss_speaker_image() 