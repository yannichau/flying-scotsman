import os
import re
import csv

# ==========================================
# GLOBAL CONFIGURATIONS
# ==========================================
DRY_RUN = False  # Set to False to apply permanent updates to your Markdown files
SCAN_DIRECTORY = "./"  # Root directory containing your Markdown documents and assets
REPORT_CSV_PATH = "image_mapping_report.csv"

# Regex to capture Markdown image formats: ![alt text](image_path)
MD_IMAGE_REGEX = re.compile(r'(!\[.*?\]\()([^\s)]+)(.*?\))')

def normalize_markdown_path(raw_path):
    """
    Standardizes old domain variants, build site artifact paths, or standalone 
    strings into a unified asset repository root path.
    CRITICAL: This strips out /_site/ from any image paths completely.
    """
    cleaned_path = raw_path.strip()
    
    # Match any legacy domains/hosts prefix leading to wp-content
    cleaned_path = re.sub(r'^(https?:)?//[^/]+/wp-content/', '/assets/wp-content/', cleaned_path)
    
    # Handle the jekyll /_site/ build output path prefix duplication
    if cleaned_path.startswith('/_site/assets/wp-content/'):
        cleaned_path = cleaned_path.replace('/_site/assets/wp-content/', '/assets/wp-content/', 1)
    elif cleaned_path.startswith('_site/assets/wp-content/'):
        cleaned_path = cleaned_path.replace('_site/assets/wp-content/', '/assets/wp-content/', 1)
        
    # Handle direct wp-content references missing assets root
    if cleaned_path.startswith('wp-content/'):
        cleaned_path = '/assets/' + cleaned_path
    elif cleaned_path.startswith('/wp-content/'):
        cleaned_path = '/assets' + cleaned_path
        
    return cleaned_path

def clean_wp_filename(filename):
    """
    Strips out WordPress-specific optimization artifacts (e.g., -1024x768, -scaled, resize600)
    to reveal the original baseline file name.
    """
    name, ext = os.path.splitext(filename)
    
    # Remove dimension variants like -1024x768 or -768x1024
    name = re.sub(r'-\d+x\d+$', '', name)
    # Remove scale rules like -scaled
    name = re.sub(r'-scaled$', '', name)
    # Remove unique resize strings like .jpgresize400
    name = re.sub(r'resize\d+$', '', name)
    
    return name.lower(), ext.lower()

def build_repo_image_registry(scan_dir):
    """
    Scans the repository to index all real images matching 'assets/wp-content/uploads/...'
    Keyed contextually by (parent_folder, cleaned_filename) to honor correct directory mapping constraints.
    """
    registry = {}
    normalized_scan_dir = os.path.normpath(scan_dir)
    
    print("Indexing existing repository images...")
    for root, _, files in os.walk(normalized_scan_dir):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg')):
                full_path = os.path.join(root, file)
                
                # Standardize path structure to forward slashes
                rel_url_path = os.path.relpath(full_path, normalized_scan_dir).replace('\\', '/')
                if not rel_url_path.startswith('/'):
                    rel_url_path = '/' + rel_url_path
                
                if 'wp-content/uploads/' in rel_url_path:
                    # Isolate parent directory names to restrict matching scope (e.g., '01' from '2024/01')
                    parent_dir = os.path.basename(os.path.dirname(rel_url_path))
                    base_name, _ = clean_wp_filename(file)
                    
                    # Target unique composite tracking rule
                    lookup_key = (parent_dir, base_name)
                    
                    # Store mapping (prefer original / clean filenames over scaled versions if conflict emerges)
                    if lookup_key not in registry or "-scaled" in registry[lookup_key]:
                        registry[lookup_key] = rel_url_path

    print(f"Indexed {len(registry)} directory-isolated image rules in your repository.")
    return registry

def find_best_match(raw_path, registry):
    """
    Normalizes markdown links and parses them strictly against trusted directory namespaces.
    """
    normalized_url = normalize_markdown_path(raw_path)
    
    # Isolate parent directory and filename from URL string
    url_parts = normalized_url.split('?')[0].split('/')
    if len(url_parts) < 2:
        return None
        
    filename = url_parts[-1]
    parent_dir = url_parts[-2]
    
    base_name, _ = clean_wp_filename(filename)
    lookup_key = (parent_dir, base_name)
    
    # Return context-verified matching path from registry
    return registry.get(lookup_key, None)

def process_markdown_files():
    # Build context-aware map of files currently living on disk
    repo_images = build_repo_image_registry(SCAN_DIRECTORY)
    
    csv_logs = []
    total_links_found = 0
    total_links_fixed = 0
    
    print("\nProcessing Markdown files...")
    for root, _, files in os.walk(SCAN_DIRECTORY):
        for file in files:
            if file.lower().endswith(('.md', '.markdown')):
                file_path = os.path.join(root, file)
                
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                modified = False
                new_content_chunks = []
                last_idx = 0
                
                for match in MD_IMAGE_REGEX.finditer(content):
                    total_links_found += 1
                    prefix, old_path, suffix = match.groups()
                    
                    best_match = find_best_match(old_path, repo_images)
                    
                    if best_match:
                        # Use the clean match found (guaranteed to be /assets/ because of how the repo index maps it)
                        resolved_path = best_match
                        
                        # Fix applied if the old path explicitly matches the wrong state (like containing /_site/)
                        if old_path != resolved_path:
                            status = "Matched & Updated"
                            total_links_fixed += 1
                            modified = True
                        else:
                            status = "Already Correct"
                    else:
                        status = "No Match Found in Folder"
                        # Fall back to standard folder normalization rule as safety default (which strips /_site/)
                        resolved_path = normalize_markdown_path(old_path)
                        if old_path != resolved_path:
                            status = "Cleaned Path (No Direct Repo File Match)"
                            total_links_fixed += 1
                            modified = True
                    
                    csv_logs.append({
                        'Markdown File': os.path.relpath(file_path, SCAN_DIRECTORY),
                        'Original Link Reference': old_path,
                        'Inferred Best Match': resolved_path,
                        'Match Status': status
                    })
                    
                    if not DRY_RUN:
                        start, end = match.span()
                        new_content_chunks.append(content[last_idx:start])
                        new_content_chunks.append(f"{prefix}{resolved_path}{suffix}")
                        last_idx = end
                
                if not DRY_RUN and modified:
                    new_content_chunks.append(content[last_idx:])
                    updated_file_content = "".join(new_content_chunks)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(updated_file_content)
                    print(f"Updated references in: {file_path}")

    # Write metrics breakdown to CSV
    with open(REPORT_CSV_PATH, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Markdown File', 'Original Link Reference', 'Inferred Best Match', 'Match Status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_logs)

    print("\n" + "="*50)
    print("EXECUTION SUMMARY")
    print("="*50)
    print(f"Mode: {'DRY RUN (No files modified)' if DRY_RUN else 'LIVE UPDATE (Files modified in-place)'}")
    print(f"Total Markdown image links processed: {total_links_found}")
    print(f"Total links requiring corrections: {total_links_fixed}")
    print(f"Detailed diagnostics exported to: {REPORT_CSV_PATH}")
    print("="*50)

if __name__ == "__main__":
    process_markdown_files()