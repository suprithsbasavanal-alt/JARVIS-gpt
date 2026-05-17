"""
utils/file_system.py  —  JARVIS 3.0 ULTIMATE
Provides find-file and read-file helpers.
"""

import os
import logging

logger = logging.getLogger("JARVIS.utils.fs")

# Directories to search (user's home, Documents, Desktop, Downloads)
SEARCH_ROOTS = [
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Desktop"),
    os.path.expanduser("~/Downloads"),
]


def find_file(filename: str) -> str | None:
    """
    Recursively searches common directories for a file matching the given name.
    Returns the absolute path if found, or None.
    """
    for root in SEARCH_ROOTS:
        for dirpath, _, files in os.walk(root):
            for f in files:
                if filename.lower() in f.lower():
                    return os.path.join(dirpath, f)
    logger.warning(f"File not found: {filename}")
    return None


def read_file_content(path: str, max_chars: int = 3000) -> str:
    """
    Reads and returns the text content of a file.
    Truncates to max_chars to avoid overloading the LLM context.
    """
    try:
        with open(path, "r", errors="ignore") as f:
            content = f.read(max_chars)
        return content
    except Exception as e:
        logger.error(f"read_file error: {e}")
        return f"Could not read file: {e}"
