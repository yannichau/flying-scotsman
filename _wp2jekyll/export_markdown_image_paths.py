# ==========================================
# CONFIGURATION
# ==========================================
# Specify the directory you want to scan here. 
# Use "." for the current directory, or a full path like "C:/Users/Name/Projects"
SCAN_DIRECTORY = "."
OUTPUT_FILE_NAME = "markdown image paths.txt"
# ==========================================

import os
import re

def extract_images_from_markdown():
    # Regex to match the markdown image syntax: ![alt_text](image_path)
    image_regex = re.compile(r'!\[.*?\]\((.*?)\)')
    
    found_images = []

    # Resolve to absolute path for clearer logging
    abs_target_dir = os.path.abspath(SCAN_DIRECTORY)
    print(f"Scanning directory: {abs_target_dir}...")

    if not os.path.exists(abs_target_dir):
        print(f"Error: The directory '{abs_target_dir}' does not exist. Please check SCAN_DIRECTORY.")
        return

    # Recursively walk through all directories and files
    for dirpath, _, filenames in os.walk(abs_target_dir):
        for filename in filenames:
            # Check for markdown files (.md or .markdown)
            if filename.lower().endswith(('.md', '.markdown')):
                file_path = os.path.join(dirpath, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # Find all matching image paths in the current file
                        matches = image_regex.findall(content)
                        for match in matches:
                            found_images.append(match.strip())
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")

    # Write the results to the output text file
    if found_images:
        with open(OUTPUT_FILE_NAME, 'w', encoding='utf-8') as out_file:
            for img_path in found_images:
                out_file.write(img_path + '\n')
        print(f"\nSuccess! Found {len(found_images)} images.")
        print(f"Results saved to: {os.path.abspath(OUTPUT_FILE_NAME)}")
    else:
        print("\nNo markdown images found.")

if __name__ == "__main__":
    extract_images_from_markdown()