"""
Download ViTPose ONNX model for inference.
Pre-exported models from MMDeploy for easy deployment.
"""

import os
import urllib.request
from tqdm import tqdm

class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)

def download_model(url: str, output_path: str):
    """Download model with progress bar."""
    print(f"Downloading from: {url}")
    print(f"Saving to: {output_path}")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with DownloadProgressBar(unit='B', unit_scale=True, miniters=1) as t:
        urllib.request.urlretrieve(url, filename=output_path, reporthook=t.update_to)
    
    print(f"✓ Download complete: {output_path}")

if __name__ == "__main__":
    # ViTPose-Base ONNX model from HuggingFace (JunkyByte/easy_ViTPose)
   # Using Base model for balance between accuracy and speed
    MODEL_URL = "https://huggingface.co/JunkyByte/easy_ViTPose/resolve/main/onnx/vitpose-b.onnx"
    OUTPUT_PATH = "checkpoints/vitpose-b.onnx"
    
    print("=" * 60)
    print("ViTPose ONNX Model Downloader")
    print("=" * 60)
    print(f"Model: ViTPose-Base")
    print(f"Size: ~200MB")
    print(f"Format: ONNX")
    print("=" * 60)
    
    if os.path.exists(OUTPUT_PATH):
        print(f"\n⚠ Model already exists at: {OUTPUT_PATH}")
        response = input("Do you want to re-download? (y/n): ")
        if response.lower() != 'y':
            print("Skipping download.")
            exit(0)
    
    try:
        download_model(MODEL_URL, OUTPUT_PATH)
        print("\n✓ Model ready for inference!")
        print(f"\nYou can now run:")
        print(f"  python main.py --detector vitpose --device cuda:0")
    except Exception as e:
        print(f"\n✗ Download failed: {e}")
        print("\nAlternative: Manual download")
        print(f"1. Visit: {MODEL_URL}")
        print(f"2. Save as: {OUTPUT_PATH}")
