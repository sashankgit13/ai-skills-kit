#!/bin/bash
# Start the guided AI setup on Linux (or any system with bash and Python 3.9+).
cd "$(dirname "$0")" || exit 1
exec python3 tools/setup.py "$@"
