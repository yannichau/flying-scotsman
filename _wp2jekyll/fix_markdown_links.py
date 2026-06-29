import os
import sys
from pathlib import Path
from collections import defaultdict

class SelectiveLogger(object):
    def __init__(self, log_file):
        self.terminal = sys.stdout
        self.log = open(log_file, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        lower_msg = message.lower()
        if "warning" in lower_msg or "updated" in lower_msg or "===" in lower_msg:
            self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

def fix_links_agnostic_of_extension():
    repo_root = Path(__file__).parent.resolve()
    assets_raw_dir = repo_root / "assets_raw"
    content_dirs = [repo_root / "_posts", repo_root / "_pages"]
    log_file = repo_root / "avif_link_fix.log"
    
    sys.stdout = SelectiveLogger(log_file)
    sys.stderr = sys.stdout
    
    print("=" * 80)
    print("FIXING MARKDOWN LINKS BY STRIPPING EXTENSION MATCHES")
    print("=" * 80)

    valid_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
    
    if not assets_raw_dir.exists():
        print(f"[Error] 'assets_raw' directory not found at: {assets_raw_dir}")
        return

    # 1. Map out the original image paths from assets_raw
    raw_images = []
    global_stem_map = defaultdict(list)
    
    for root, _, files in os.walk(assets_raw_dir):
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() in valid_extensions:
                raw_images.append(file_path)
                # Key on the filename without extension (lowercased)
                global_stem_map[file_path.stem.lower()].append(file_path)

    # 2. Index Markdown contents
    markdown_files = []
    md_contents = {}
    for folder in content_dirs:
        if folder.exists():
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.endswith((".md", ".html")):
                        md_path = Path(root) / file
                        markdown_files.append(md_path)
                        try:
                            with open(md_path, 'r', encoding='utf-8') as f:
                                md_contents[md_path] = f.read()
                        except Exception as e:
                            print(f"[Warning] Failed to read {md_path.relative_to(repo_root)}: {e}")

    # 3. Search and replace using extension-agnostic logic
    updated_files_count = 0
    
    # We will search for common image format structures or just the stem with an extension
    # To catch things like 'image-name.webp' or 'image-name.jpg' and swap to 'image-name.avif'
    # We use regex to find the filename stem followed by any of our valid extensions
    import re

    for md_path, content in md_contents.items():
        file_modified = False
        updated_content = content
        
        for stem_lower, orig_paths in global_stem_map.items():
            # Check if this base filename is mentioned anywhere in the markdown file
            if stem_lower in updated_content.lower():
                # We need to target the image file specifically.
                # Loop through each path that shares this stem (usually just 1)
                for orig_path in orig_paths:
                    orig_stem = orig_path.stem
                    
                    # Create a regex pattern that looks for: orig_stem + (any valid image extension)
                    # e.g., P1151909-edited-2-scaled\.(webp|jpg|jpeg|png|gif|bmp)
                    extensions_pattern = "|".join([ext.replace('.', '') for ext in valid_extensions])
                    pattern = re.compile(rf"\b{re.escape(orig_stem)}\.({extensions_pattern})\b", re.IGNORECASE)
                    
                    # Target name could be regular, or collision-renamed if you have local conflicts
                    # We check what exists in the actual 'assets' folder to see what name was given to it.
                    relative_to_raw = orig_path.relative_to(assets_raw_dir)
                    actual_assets_folder = repo_root / "assets" / relative_to_raw.parent
                    
                    # Look for the generated file in your actual assets directory
                    target_name = f"{orig_stem}.avif"
                    # If it was a collision file (e.g. image-jpg.avif), look for it
                    collision_suffix = orig_path.suffix.replace('.', '')
                    if (actual_assets_folder / f"{orig_stem}-{collision_suffix}.avif").exists():
                        target_name = f"{orig_stem}-{collision_suffix}.avif"
                    
                    # Apply contextual directory path matching if the filename isn't globally unique
                    is_unique = len(global_stem_map[stem_lower]) == 1
                    path_parts = orig_path.parent.parts
                    path_clue = "/".join(path_parts[-2:]) if len(path_parts) >= 2 else orig_stem
                    
                    if is_unique or (path_clue in updated_content.replace('\\', '/')):
                        # Perform the regex sub
                        new_content, count = pattern.subn(target_name, updated_content)
                        if count > 0:
                            updated_content = new_content
                            file_modified = True
                            print(f"  - Updated {count} link(s): '{orig_stem}.*' -> '{target_name}' in {md_path.relative_to(repo_root)}")

        if file_modified:
            try:
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                updated_files_count += 1
            except Exception as e:
                print(f"[Error] Failed writing updates to file {md_path}: {e}")

    print("=" * 80)
    print(f"Task Complete! Cleaned up image links across {updated_files_count} Markdown files.")
    print(f"Log report saved to: {log_file}")
    print("=" * 80)

if __name__ == '__main__':
    fix_links_agnostic_of_extension()
