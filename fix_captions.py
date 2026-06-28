import os
import re
from pathlib import Path

def fix_markdown_captions(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    fixed_lines = []
    changes_made = False

    # Pattern breakdown for a single line:
    # 1. !\[\] - Empty image brackets
    # 2. (\([^)]+\)) - The image URL/path captured in group 1
    # 3. (.*?) - Lazy match for the caption text captured in group 2
    # 4. (?=\s*!\[\]|$) - Lookahead: stops if it sees another image syntax or the end of the line
    pattern = r'!\[\](\([^)]+\))(.*?)(?=\s*!\[\]|$)'

    def replace_caption(match):
        url_part = match.group(1)
        caption_part = match.group(2).strip()
        
        # If there is no caption text at all, leave the image tag untouched
        if not caption_part:
            return f"![]{url_part}"
        
        # Otherwise, insert the caption into the brackets
        return f"![{caption_part}]{url_part}"

    for line in lines:
        # Only process lines that actually contain an empty image tag
        if '![]' in line:
            new_line = re.sub(pattern, replace_caption, line)
            if new_line != line:
                changes_made = True
            fixed_lines.append(new_line)
        else:
            fixed_lines.append(line)

    # Only save if changes were actually made
    if changes_made:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)
        print(f"Fixed captions in: {file_path}")

def main():
    current_dir = Path.cwd()
    print(f"Scanning for Markdown files in: {current_dir}\n")

    for md_file in current_dir.rglob('*.md'):
        try:
            fix_markdown_captions(md_file)
        except Exception as e:
            print(f"Error processing {md_file}: {e}")

if __name__ == "__main__":
    main()
