"""Create immutable deployment metadata without credentials."""

import json
import os
from pathlib import Path

tag = os.environ["RELEASE_TAG"]
Path("release/images.json").write_text(
    json.dumps(
        {
            "backend": f"{os.environ['BACKEND_REPOSITORY']}:{tag}",
            "frontend": f"{os.environ['FRONTEND_REPOSITORY']}:{tag}",
            "revision": tag,
        }
    )
)
