import os
import re
import sys
import shutil
from pathlib import Path
from collections import defaultdict
from PIL import Image

try:
    import pillow_avif
except ImportError:
    print("[Error] Please install the avif plugin first by running: pip install pillow-avif-plugin")
    sys.exit(1)

class SelectiveLogger(object):
    """Logs EVERYTHING to the terminal, but ONLY commits warnings and actions to the log file."""
    def __init__(self, log_file):
        self.terminal = sys.stdout
        self.log = open(log_file, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        lower_msg = message.lower()
        if any(k in lower_msg for k in ["warning", "unused", "[error]", "===", "###", "task complete", "updated"]):
            self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

def find_image_line_numbers(md_path, stem_name):
    """Scans markdown for instances of the base filename stem, regardless of extension."""
    line_numbers = []
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            for line_idx, line in enumerate(f, 1):
                if stem_name in line.lower():
                    line_numbers.append(line_idx)
    except Exception:
        pass
    return line_numbers

def run_unified_optimization():
    repo_root = Path(__file__).parent.resolve()
    assets_dir = repo_root / "assets"
    assets_raw_dir = repo_root / "assets_raw"
    content_dirs = [repo_root / "_posts", repo_root / "_pages"]
    log_file = repo_root / "site_optimization.log"
    
    sys.stdout = SelectiveLogger(log_file)
    sys.stderr = sys.stdout
    
    print("=" * 80)
    print("RUNNING MASTER SITE ASSET OPTIMIZATION & LINK SYNC")
    print("=" * 80)

    valid_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.avif'}
    
    if not assets_raw_dir.exists():
        print(f"[Error] Source folder 'assets_raw' not found at: {assets_raw_dir}")
        print("Please place your raw original images there first.")
        return

    # 1. DISCOVER RAW INPUTS AND IDENTIFY SAME-FOLDER CONFLICTS
    all_raw_images = []
    global_stem_map = defaultdict(list)
    collision_stems_per_dir = defaultdict(set)

    for root, _, files in os.walk(assets_raw_dir):
        folder_stem_count = defaultdict(int)
        folder_images = []
        
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() in valid_extensions:
                folder_images.append(file_path)
                folder_stem_count[file_path.stem.lower()] += 1
        
        for file_path in folder_images:
            stem_lower = file_path.stem.lower()
            if folder_stem_count[stem_lower] > 1:
                collision_stems_per_dir[root].add(stem_lower)
            
            all_raw_images.append(file_path)
            global_stem_map[stem_lower].append(file_path)

    # 2. READ ALL MARKDOWN FILES INTO MEMORY
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

    # 3. DIAGNOSTICS & SYSTEM WARNINGS
    print("\n" + "### GLOBAL WARNINGS AND UNUSED IMAGE AUDIT ###")
    
    stem_usage_map = defaultdict(set)
    for md_path, content in md_contents.items():
        content_lower = content.lower()
        for stem_lower in global_stem_map.keys():
            if stem_lower in content_lower:
                stem_usage_map[stem_lower].add(md_path)

    # A. Multi-folder naming conflicts
    for stem_lower, paths in global_stem_map.items():
        if len(paths) > 1:
            print(f"\n[WARNING] Ambiguous filename base '{stem_lower}' exists in multiple folders:")
            for p in paths:
                print(f"  Location: {p.relative_to(repo_root)}")

    # B. Shared files across multiple markdown pages
    for stem_lower, posts in stem_usage_map.items():
        if len(posts) > 1:
            print(f"\n[WARNING] Image asset '{stem_lower}.*' is shared across {len(posts)} different markdown files:")
            for p in posts:
                print(f"  - {p.relative_to(repo_root)}")

    # C. Unused file checking
    print("\nListing entirely unused raw images:")
    for img_path in all_raw_images:
        if img_path.stem.lower() not in stem_usage_map:
            print(f"  - [UNUSED IMAGE]: {img_path.relative_to(repo_root)}")

    # 4. RESET PRODUCTION ASSETS DIRECTORY
    if assets_dir.exists():
        print(f"\nWiping production output path to ensure a clean build: {assets_dir}")
        shutil.rmtree(assets_dir)
    assets_dir.mkdir(parents=True, exist_ok=True)

    # 5. CONVERT IMAGES TO AVIF (RAW SOURCE -> PRODUCTION TARGET)
    print("\nCompressing assets to AVIF...")
    conversion_map = {}

    for img_path in all_raw_images:
        orig_size = img_path.stat().st_size
        relative_to_raw = img_path.relative_to(assets_raw_dir)
        target_folder = assets_dir / relative_to_raw.parent
        target_folder.mkdir(parents=True, exist_ok=True)
        
        parent_str = str(img_path.parent)
        orig_stem = img_path.stem
        
        if orig_stem.lower() in collision_stems_per_dir[parent_str]:
            clean_suffix = img_path.suffix.replace('.', '')
            avif_name = f"{orig_stem}-{clean_suffix}.avif"
        else:
            avif_name = f"{orig_stem}.avif"
            
        target_avif_path = target_folder / avif_name
        
        if img_path.suffix.lower() == '.avif':
            shutil.copy2(str(img_path), str(target_folder / img_path.name))
            continue

        try:
            with Image.open(img_path) as im:
                if im.mode in ("RGBA", "P"):
                    im = im.convert("RGBA")
                im.save(target_avif_path, 'AVIF', quality=70)
                
            avif_size = target_avif_path.stat().st_size
            
            if avif_size < orig_size:
                conversion_map[img_path] = target_avif_path.name
                print(f"Compressed: {relative_to_raw} -> {target_avif_path.name} (Saved {((orig_size - avif_size)/orig_size)*100:.1f}%)")
            else:
                os.remove(target_avif_path)
                shutil.copy2(str(img_path), str(target_folder / img_path.name))
                conversion_map[img_path] = img_path.name
                print(f"Kept Original Layout: {img_path.name} is smaller than its AVIF profile")
                
        except Exception as e:
            print(f"[Error] Processing failed for {img_path.name}: {e}")
            if target_avif_path.exists():
                os.remove(target_avif_path)
            shutil.copy2(str(img_path), str(target_folder / img_path.name))
            conversion_map[img_path] = img_path.name

    # 6. EXTENSION-AGNOSTIC REWRITE FOR ALL MARKDOWN LINKS
    print("\nScanning markdown contents to find and update image extensions...")
    updated_files_count = 0
    extensions_regex_pattern = "|".join([ext.replace('.', '') for ext in valid_extensions])

    for md_path, content in md_contents.items():
        file_modified = False
        updated_content = content
        
        for orig_path, final_asset_name in conversion_map.items():
            orig_stem = orig_path.stem
            stem_lower = orig_stem.lower()
            
            if stem_lower in updated_content.lower():
                pattern = re.compile(rf"\b{re.escape(orig_stem)}\.({extensions_regex_pattern})\b", re.IGNORECASE)
                
                # FIXED HERE: Correctly checking global_stem_map 
                is_unique = len(global_stem_map[stem_lower]) == 1
                path_parts = orig_path.parent.parts
                path_clue = "/".join(path_parts[-2:]) if len(path_parts) >= 2 else orig_stem
                
                if is_unique or (path_clue in updated_content.replace('\\', '/')):
                    new_content, count = pattern.subn(final_asset_name, updated_content)
                    if count > 0:
                        updated_content = new_content
                        file_modified = True
                        print(f"  - Updated link: '{orig_stem}.*' -> '{final_asset_name}' in {md_path.relative_to(repo_root)}")

        if file_modified:
            try:
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                updated_files_count += 1
            except Exception as e:
                print(f"[Error] Failed writing updates to file {md_path}: {e}")

    print("=" * 80)
    print(f"Task Complete! Processed images and updated links across {updated_files_count} Markdown files.")
    print(f"Clean log saved to: {log_file}")
    print("=" * 80)

if __name__ == '__main__':
    run_unified_optimization()
