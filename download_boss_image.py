import requests
import os

url = 'https://files.oaiusercontent.com/file-0e1b1e7e-2e2e-4e2e-8e2e-0e1b1e7e2e2e.jpg'
output_path = 'static/uploads/boss_speaker.jpg'

os.makedirs('static/uploads', exist_ok=True)

response = requests.get(url)
if response.status_code == 200:
    with open(output_path, 'wb') as f:
        f.write(response.content)
    print('Image downloaded successfully!')
else:
    print('Failed to download image:', response.status_code) 