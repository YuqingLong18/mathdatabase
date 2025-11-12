#!/usr/bin/env python3
"""
Script to migrate existing 2025 data to the new year-based structure.
"""

from pathlib import Path
import shutil
import json

def migrate_2025_data():
    """Move existing 2025 data from data/ to data/AMC8/2025/"""
    old_data_dir = Path("data")
    new_data_dir = Path("data/AMC8/2025")
    
    if not old_data_dir.exists():
        print("No existing data directory found.")
        return
    
    print("Migrating 2025 data to new structure...")
    
    # Create new directory structure
    new_data_dir.mkdir(parents=True, exist_ok=True)
    (new_data_dir / "images").mkdir(exist_ok=True)
    (new_data_dir / "html").mkdir(exist_ok=True)
    
    # Move JSON file
    old_json = old_data_dir / "amc8_2025_problems.json"
    if old_json.exists():
        new_json = new_data_dir / "amc8_2025_problems.json"
        if not new_json.exists():
            shutil.move(str(old_json), str(new_json))
            print(f"✓ Moved JSON file to {new_json}")
        else:
            print(f"  JSON file already exists at {new_json}, skipping...")
    
    # Move images
    old_images_dir = old_data_dir / "images"
    new_images_dir = new_data_dir / "images"
    if old_images_dir.exists():
        if not any(new_images_dir.iterdir()):
            # Move all images
            for img_file in old_images_dir.iterdir():
                if img_file.is_file():
                    shutil.move(str(img_file), str(new_images_dir / img_file.name))
            print(f"✓ Moved images to {new_images_dir}")
        else:
            print(f"  Images directory already has files, skipping...")
    
    # Move HTML files
    old_html_dir = old_data_dir / "html"
    new_html_dir = new_data_dir / "html"
    if old_html_dir.exists():
        if not any(new_html_dir.iterdir()):
            # Move all HTML files
            for html_file in old_html_dir.iterdir():
                if html_file.is_file():
                    shutil.move(str(html_file), str(new_html_dir / html_file.name))
            print(f"✓ Moved HTML files to {new_html_dir}")
        else:
            print(f"  HTML directory already has files, skipping...")
    
    # Update JSON file to include year field if needed
    json_file = new_data_dir / "amc8_2025_problems.json"
    if json_file.exists():
        with open(json_file, 'r', encoding='utf-8') as f:
            problems = json.load(f)
        
        # Check if year field exists
        needs_update = False
        for problem in problems:
            if 'year' not in problem:
                problem['year'] = 2025
                needs_update = True
        
        if needs_update:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(problems, f, indent=2, ensure_ascii=False)
            print("✓ Updated JSON file with year field")
    
    print("\n✓ Migration complete!")

if __name__ == "__main__":
    migrate_2025_data()


