"""Find the LFE engine: $LFE_ENGINE, or an `engine/lfe` folder in a parent directory."""
import os
import sys
from pathlib import Path


def load():
    candidates = [Path(os.environ["LFE_ENGINE"])] if os.environ.get("LFE_ENGINE") else []
    candidates += [parent / "engine" for parent in Path(__file__).resolve().parents]
    for candidate in candidates:
        if (candidate / "lfe" / "__main__.py").is_file():
            sys.path.insert(0, str(candidate))
            return
    raise ImportError("LFE engine not found: set LFE_ENGINE=/path/to/layout-first-engineering/engine")
