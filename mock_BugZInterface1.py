# -*- coding: utf-8 -*-
"""
mock_BugZInterface1.py  --  Python 2 / 3 compatible mock of BugZInterface1.py
------------------------------------------------------------------------------
Replaces the real Bugzilla interface for external users.
Reads mock_bugs.json from the same directory and prints its contents to stdout
in exactly the same format that BugZInterface1.py produces:
 
    <Response [200]>
    [ { "Bug Id": "...", ... }, ... ]
 
The build version argument is used to filter bugs — only bugs whose
"Build" field matches the supplied version are returned.
 
Usage (called internally by bug_info.py --mock):
    python2 mock_BugZInterface1.py <build_version>
    python3 mock_BugZInterface1.py <build_version>
"""
 
from __future__ import print_function
 
import json
import os
import sys
 
 
def main():
    if len(sys.argv) < 2:
        print("Usage: mock_BugZInterface1.py <build_version>", file=sys.stderr)
        sys.exit(1)
 
    build_version = sys.argv[1]
 
    # Locate mock_bugs.json relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mock_file = os.path.join(script_dir, "mock_bugs.json")
 
    if not os.path.isfile(mock_file):
        print("ERROR: mock_bugs.json not found at: " + mock_file, file=sys.stderr)
        sys.exit(1)
 
    with open(mock_file, "r") as f:
        bug_data = json.load(f)
 
    # Filter bugs by the specified build version
    filtered = [b for b in bug_data if b.get("Build", "") == build_version]
 
    # Mimic the real BugZInterface1.py stdout format:
    #   line 1  →  <Response [200]>   (from "print response" in login/getRequest)
    #   line 2+ →  JSON array
    print("<Response [200]>")
    print(json.dumps(filtered, indent=2))
 
 
if __name__ == "__main__":
    main()