#!/bin/bash
# setup.sh - Install dependencies and optionally run training/app

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

if [ "$1" = "train" ]; then
	echo "Running section detector training..."
	python method_trained_sectioned/src/train_section_detector.py
elif [ "$1" = "run" ]; then
	echo "Launching Streamlit app..."
	streamlit run app.py
else
	echo "Usage: ./setup.sh [train|run]"
	echo "  train: run section detector training"
	echo "  run: launch Streamlit app"
fi

# how to run:
# chmod +x setup.sh
# ./setup.sh
# ./setup.sh train
# ./setup.sh run