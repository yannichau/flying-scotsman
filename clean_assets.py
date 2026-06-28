import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

class Logger(object):
    """Dual-output logger to print to the terminal and write to a file simultaneously."""
    def __init__(self, log_file):
        self.terminal = sys.stdout
        self.log = open(log_file, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

def archive_unused_images():
    repo_root = Path(__file__).parent.resolve()
    assets_dir = repo_root / "assets"
    archive_dir = repo_root / "_archive"
    
    # Setup logging
    log_file = repo_root / "clean_assets_run.log"
    sys.stdout = Logger(log_file)
    sys.stderr = sys.stdout  # Capture any errors in the log file too

    print("=" * 60)
    print(f"Run Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    content_dirs = [repo_root / "_posts", repo_root / "_pages"]
    valid_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'}
    
    if not assets_dir.exists():
        print(f"[Error] 'assets' folder not found at: {assets_dir}")
        return

    # 1. Collect asset images
    all_images = []
    for root, _, files in os.walk(assets_dir):
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() in valid_extensions:
                all_images.append(file_path)
                
    if not all_images:
        print("No images found in the assets folder.")
        return
        
    print(f"Found {len(all_images)} total images in 'assets'.")

    # 2. Extract text from Jekyll content files
    print("Scanning Markdown files...")
    combined_markdown_content = ""
    for folder in content_dirs:
        if folder.exists():
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.endswith((".md", ".html")):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                combined_markdown_content += f.read() + "\n"
                        except Exception as e:
                            print(f"Skipping file due to read error {file_path}: {e}")

    # 3. Exact filename match and move logic
    moved_count = 0
    for img_path in all_images:
        # Strictly checking the raw filename (e.g. 'image-14.png') 
        # This completely ignores path slashes, variations, or formatting differences
        filename = img_path.name
        
        if filename not in combined_markdown_content:
            relative_path = img_path.relative_to(repo_root)
            target_path = archive_dir / relative_path
            
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(img_path), str(target_path))
            
            print(f"Moved unused image: {relative_path} -> {target_path}")
            moved_count += 1

    print(f"\nTask completed! Moved {moved_count} unused images to '_archive'.")
    print(f"Log written to: {log_file}\n")

if __name__ == '__main__':
    archive_unused_images()
