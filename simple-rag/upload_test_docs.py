#!/usr/bin/env python3
"""
Batch upload all supported documents from a directory to the Simple Arabic RAG server.

Usage:
  python upload_test_docs.py \
    --dir /media/hanafy/aa9ee400-c081-4d3b-b831-a2a8c83c9f444/MetaVR/EcommerceRag/test_docs \
    --base-url http://localhost:8000
"""

import argparse
import json
import os
from pathlib import Path
from typing import List, Tuple, Set

import requests


SUPPORTED_EXT = {".txt", ".pdf", ".docx", ".md"}


def find_files(directory: str) -> List[Path]:
    base = Path(directory)
    if not base.exists() or not base.is_dir():
        raise FileNotFoundError(f"Directory not found: {directory}")
    files: List[Path] = []
    for entry in sorted(base.iterdir()):
        if entry.is_file() and entry.suffix.lower() in SUPPORTED_EXT:
            files.append(entry)
    return files


def upload_file(base_url: str, file_path: Path) -> Tuple[bool, dict]:
    url = f"{base_url.rstrip('/')}/upload"
    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f)}
        try:
            resp = requests.post(url, files=files, timeout=120)
            ok = resp.status_code == 200
            try:
                data = resp.json()
            except Exception:
                data = {"raw": resp.text}
            return ok, {"status_code": resp.status_code, "data": data}
        except requests.RequestException as e:
            return False, {"error": str(e)}


def list_documents_dir(documents_path: str) -> Set[str]:
    p = Path(documents_path)
    if not p.exists():
        return set()
    return set(sorted(f.name for f in p.iterdir() if f.is_file()))


def main():
    parser = argparse.ArgumentParser(description="Batch upload documents to Simple Arabic RAG")
    parser.add_argument("--dir", required=True, help="Directory containing documents to upload")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL of the API server")
    parser.add_argument("--documents-path", default="./data/documents", help="Path to originals directory for verification")
    args = parser.parse_args()

    print(f"Scanning directory: {args.dir}")
    files = find_files(args.dir)
    if not files:
        print("No supported files found (.txt, .pdf, .docx, .md)")
        # continue to failure test below even if none supported

    print(f"Found {len(files)} supported files")
    results = []
    success_count = 0
    duplicate_count = 0
    fail_count = 0

    # Failure test: use an unsupported file (e.g., .html) if present, else create temp
    print("\n=== Failure test: unsupported file should NOT create original ===")
    # Snapshot before
    before_set = list_documents_dir(args.documents_path)

    # Find an existing unsupported file in the provided directory
    dir_path = Path(args.dir)
    unsupported = None
    for entry in sorted(dir_path.iterdir()):
        if entry.is_file() and entry.suffix.lower() not in SUPPORTED_EXT:
            unsupported = entry
            break

    temp_created = False
    if unsupported is None:
        # Create a temporary unsupported file
        unsupported = dir_path / "__unsupported_test__.html"
        try:
            unsupported.write_text("<html><body>test</body></html>", encoding="utf-8")
            temp_created = True
        except Exception as e:
            print(f"Could not create temp unsupported file: {e}")

    if unsupported and unsupported.exists():
        print(f"Uploading unsupported file: {unsupported.name}")
        ok, info = upload_file(args.base_url, unsupported)
        status_code = info.get("status_code")
        after_set = list_documents_dir(args.documents_path)
        unchanged = before_set == after_set
        outcome = "PASS" if (not ok and unchanged) else "FAIL"
        print("  Expected non-200 status and no new originals")
        print(f"  Status code: {status_code}")
        print(f"  Originals unchanged: {unchanged}")
        print(f"  Result: {outcome}")
        if temp_created:
            try:
                unsupported.unlink()
            except Exception:
                pass
    else:
        print("No unsupported file available and could not create one; skipping failure test.")

    for fp in files:
        print(f"\nUploading: {fp.name}")
        ok, info = upload_file(args.base_url, fp)
        if ok:
            success_count += 1
            print("  ✓ Success")
            print("  Response:")
            print("  " + json.dumps(info.get("data", {}), ensure_ascii=False))
        else:
            # Detect duplicate status (409) if available
            status_code = info.get("status_code")
            if status_code == 409 or (isinstance(info.get("data"), dict) and "Duplicate" in str(info.get("data"))):
                duplicate_count += 1
                print("  ≈ Duplicate (skipped)")
            else:
                fail_count += 1
                print("  ✗ Failed")
            print("  Details:")
            print("  " + json.dumps(info, ensure_ascii=False))
        results.append({"file": fp.name, **info})

    print("\nSummary:")
    print(f"  Uploaded OK : {success_count}")
    print(f"  Duplicates  : {duplicate_count}")
    print(f"  Failed      : {fail_count}")

    # Optionally write a results file next to the script
    try:
        out_path = Path(__file__).with_name("upload_results.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({
                "base_url": args.base_url,
                "directory": os.path.abspath(args.dir),
                "summary": {
                    "success": success_count,
                    "duplicates": duplicate_count,
                    "failed": fail_count,
                },
                "results": results,
            }, f, ensure_ascii=False, indent=2)
        print(f"Results saved to {out_path}")
    except Exception as e:
        print(f"Could not write results file: {e}")


if __name__ == "__main__":
    main()


