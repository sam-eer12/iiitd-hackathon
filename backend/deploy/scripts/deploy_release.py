"""Versioned EC2 releases with health-gated promotion and application rollback."""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

incoming = Path("/opt/tenderlens/incoming")
root = Path("/opt/tenderlens")
images = json.loads((incoming / "images.json").read_text())
revision = images["revision"]
if not re.fullmatch(r"[a-f0-9]{40}-\d+", revision):
    raise ValueError("Invalid immutable release revision")
release = root / "releases" / revision
current = root / "current"
previous = current.resolve() if current.is_symlink() else None
if release != incoming:
    shutil.copytree(incoming, release, dirs_exist_ok=True)


def start(path, rollback=False):
    env = dict(os.environ)
    if rollback:
        env["SKIP_MIGRATIONS"] = "1"
    subprocess.run(["bash", "scripts/prepare.sh"], cwd=path, env=env, check=True)
    subprocess.run([sys.executable, "scripts/start.py"], cwd=path, env=env, check=True)
    subprocess.run(["bash", "scripts/validate.sh"], cwd=path, env=env, check=True)


try:
    start(release)
except subprocess.CalledProcessError:
    if previous and previous != release and previous.is_dir():
        print("Readiness failed; restoring the previous application release.", flush=True)
        start(previous, rollback=True)
    raise
link = root / "next"
if link.is_symlink():
    link.unlink()
link.symlink_to(release, target_is_directory=True)
os.replace(link, current)
config = json.loads(Path("/etc/tenderlens/runtime.json").read_text())
# Only a healthy revision becomes the recovery bundle for replacement EC2 hosts.
with tempfile.TemporaryDirectory() as temporary:
    archive = shutil.make_archive(str(Path(temporary) / "current"), "gztar", root_dir=release)
    subprocess.run(
        [
            "aws",
            "s3",
            "cp",
            archive,
            f"s3://{config['artifactBucket']}/bootstrap/current.tar.gz",
            "--region",
            config["region"],
            "--only-show-errors",
        ],
        check=True,
    )
print("Healthy application release promoted.", flush=True)
