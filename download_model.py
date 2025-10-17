#!/usr/bin/env python3
"""
Script to download the EGTTS-V0.1 model files from Hugging Face.
"""

import os
import sys
from pathlib import Path
from huggingface_hub import hf_hub_download, snapshot_download

def download_model():
    """Download the EGTTS-V0.1 model files."""
    repo_id = "OmarSamir/EGTTS-V0.1"
    repo_root = Path(__file__).parent
    model_dir = repo_root / "OmarSamir" / "EGTTS-V0.1"
    
    print(f"Downloading model from {repo_id}...")
    print(f"Target directory: {model_dir}")
    
    # Create the directory structure
    model_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Download all files from the repository
        snapshot_download(
            repo_id=repo_id,
            local_dir=str(model_dir),
            local_dir_use_symlinks=False
        )
        
        print("✅ Model downloaded successfully!")
        print(f"Files downloaded to: {model_dir}")
        
        # List downloaded files
        print("\nDownloaded files:")
        for file_path in model_dir.rglob("*"):
            if file_path.is_file():
                print(f"  - {file_path.relative_to(repo_root)}")
                
    except Exception as e:
        print(f"❌ Failed to download model: {e}")
        sys.exit(1)

if __name__ == "__main__":
    download_model()
