@echo off
cd /d "%~dp0"
python -c "from PIL import Image; img = Image.open('icon.png'); img.save('icon.ico', format='ICO', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)], append_images=[]); print('Created icon.ico')"
pause