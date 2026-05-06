#!/bin/bash
# setup.sh - Run after pip install

echo "Installing Python packages..."
pip install -r requirements.txt

echo "Pre-downloading PaddleOCR models..."
python -c "
from paddleocr import PaddleOCR
print('Downloading PaddleOCR models...')
ocr = PaddleOCR(use_angle_cls=True, lang='en')
print('Models downloaded successfully!')
"

echo "Setup complete!"

# how to run:
# chmod +x setup.sh
# ./setup.sh