"""
Import helper to properly load learning-coach-mcp modules with relative imports.
"""

import sys
import os
from pathlib import Path

# Get the learning-coach-mcp directory
learning_coach_dir = Path(__file__).parent.parent / "learning-coach-mcp"
src_dir = learning_coach_dir / "src"

# Add src to path and change to that directory for imports
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Change working directory temporarily for imports
_original_cwd = os.getcwd()
_original_path = sys.path.copy()

def setup_imports():
    """Setup environment for proper imports."""
    os.chdir(str(src_dir))
    return src_dir

def restore_imports():
    """Restore original environment."""
    os.chdir(_original_cwd)
    sys.path[:] = _original_path

