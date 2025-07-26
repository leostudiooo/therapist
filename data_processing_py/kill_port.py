#!/usr/bin/env python3
"""
Kill process using a specific port.
"""

import subprocess
import sys

def kill_port(port):
    """Kill process using the specified port."""
    try:
        # Find process using the port
        result = subprocess.run(['lsof', '-ti', f':{port}'], capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    print(f"Killing process {pid} using port {port}")
                    subprocess.run(['kill', '-9', pid])
            print(f"Port {port} is now free")
        else:
            print(f"No process found using port {port}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    port = sys.argv[1] if len(sys.argv) > 1 else "8765"
    kill_port(port)