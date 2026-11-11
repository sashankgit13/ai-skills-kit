#!/bin/bash
# Double-click to start the guided AI setup on a Mac.
cd "$(dirname "$0")" || exit 1
if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys; sys.exit(sys.version_info < (3, 9))' 2>/dev/null; then
  python3 tools/setup.py
else
  echo "Python 3.9 or newer is needed and was not found."
  echo "If macOS offers to install 'command line developer tools', accept and run this again."
  echo "Otherwise please ask IT for help."
fi
echo
read -r -p "Press Enter to close this window." _
