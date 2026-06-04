import os

# --- Configuration ---
# Use '.' to scan the current directory and its subfolders
FOLDER_TO_SCAN = './assets' 
OUTPUT_FILE = 'all_file_paths.txt'

def export_file_paths(target_directory, output_text_file):
    """
    Recursively finds all files in target_directory and writes their paths
    (relative to the execution directory) into output_text_file.
    """
    try:
        with open(output_text_file, 'w', encoding='utf-8') as f:
            for root, dirs, files in os.walk(target_directory):
                for filename in files:
                    # Combine the current directory path with the filename
                    full_path = os.path.join(root, filename)
                    
                    # Force the path to be relative to the current execution directory ('.')
                    relative_path = os.path.relpath(full_path, start='.')
                    
                    f.write(relative_path + '\n')
                    
        print(f"Success! All relative file paths have been exported to '{output_text_file}'.")
        
    except Exception as e:
        print(f"An error occurred: {e}")

# Run the script
export_file_paths(FOLDER_TO_SCAN, OUTPUT_FILE)