from PIL import Image

# Open the PNG
img = Image.open("icon.png")

# Convert to RGBA if needed
if img.mode != 'RGBA':
    img = img.convert('RGBA')

# Resize and save as ICO with multiple sizes
sizes = [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]
img.save("icon.ico", format="ICO", sizes=sizes, append_images=[])

print("Created icon.ico successfully!")