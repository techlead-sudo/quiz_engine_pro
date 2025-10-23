# Simple script to create a basic icon - run this once to generate icon.png

from PIL import Image, ImageDraw, ImageFont

# Create a 128x128 icon
img = Image.new('RGB', (128, 128), color='#007bff')
draw = ImageDraw.Draw(img)

# Draw a simple quiz icon
draw.rectangle([20, 20, 108, 108], outline='white', width=3)
draw.rectangle([30, 35, 98, 45], fill='white')
draw.rectangle([30, 55, 98, 65], fill='white')
draw.rectangle([30, 75, 98, 85], fill='white')

# Add question mark
try:
    font = ImageFont.truetype("arial.ttf", 40)
except:
    font = ImageFont.load_default()

draw.text((75, 45), "?", fill='#007bff', font=font, anchor="mm")

# Save icon
img.save('/home/tl/code/custom_addons/quiz_engine_pro/static/description/icon.png')
print("Icon created successfully!")
