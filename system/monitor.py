"""
system/monitor.py
Monitors system resources like CPU, RAM, and Battery using psutil.
"""
import psutil
import subprocess
import re

def get_system_stats():
    """Returns a dictionary with current CPU, RAM, and Battery stats."""
    stats = {}
    
    # CPU and RAM percentages
    stats['cpu'] = psutil.cpu_percent(interval=0.1)
    stats['ram'] = psutil.virtual_memory().percent
    
    # Battery percentage (macOS specific pmset command)
    try:
        result = subprocess.run(['pmset', '-g', 'batt'], capture_output=True, text=True)
        match = re.search(r'(\d+)%', result.stdout)
        if match:
            stats['battery'] = int(match.group(1))
        else:
            stats['battery'] = 100
    except Exception:
        stats['battery'] = 100
        
    return stats
