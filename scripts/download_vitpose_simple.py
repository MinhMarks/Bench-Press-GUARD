"""
Simpler download using huggingface_hub
"""
from huggingface_hub import hf_hub_download
import os

print("=" * 60)
print("Downloading ViTPose-Base ONNX Model")
print("=" * 60)

# Create checkpoints directory
os.makedirs("checkpoints", exist_ok=True)

try:
    print("\nDownloading from HuggingFace Hub...")
    print("Repository: JunkyByte/easy_ViTPose")
    print("File: onnx/vitpose-b.onnx")
    
    # Download the model
    model_path = hf_hub_download(
        repo_id="JunkyByte/easy_ViTPose",
        filename="onnx/vitpose-b.onnx",
        local_dir="checkpoints",
        local_dir_use_symlinks=False
    )
    
    print(f"\n✓ Model downloaded successfully!")
    print(f"Location: {model_path}")
    print("\nYou can now run:")
    print("  python main.py --detector vitpose --device cuda:0")
    
except Exception as e:
    print(f"\n✗ Download failed: {e}")
    print("\nTroubleshooting:")
    print("1. Check internet connection")
    print("2. Visit: https://huggingface.co/JunkyByte/easy_ViTPose")
    print("3. Manual download then place in: checkpoints/onnx/vitpose-b.onnx")
