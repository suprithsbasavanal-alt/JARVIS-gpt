"""
utils/file_system.py
Allows JARVIS to search for, read, and manage local files on macOS.
"""
import os
import glob

def find_file(filename, search_dir=None):
    """
    Searches for a file by name starting from the given directory (defaulting to Documents).
    Returns the absolute path if found.
    """
    if not search_dir:
        search_dir = os.path.expanduser("~/Documents")
        
    print(f"Searching for {filename} in {search_dir}...")
    
    # Recursive search using glob
    search_pattern = os.path.join(search_dir, f"**/*{filename}*")
    matches = glob.glob(search_pattern, recursive=True)
    
    # Filter out directories
    files_only = [f for f in matches if os.path.isfile(f)]
    
    if files_only:
        return files_only[0] # Return the first match
    return None

def read_file_content(filepath):
    """
    Reads the content of a text file safely.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # Truncate if too long to prevent LLM context overflow
            if len(content) > 5000:
                content = content[:5000] + "\n...[CONTENT TRUNCATED]"
            return content
    except Exception as e:
        return f"Could not read file. Error: {e}"
