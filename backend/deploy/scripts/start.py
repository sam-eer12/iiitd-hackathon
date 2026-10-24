"""Resolve AWS-managed secrets only inside the official resolver subprocess."""

import json
import os
import subprocess
import sys
from pathlib import Path

config = json.loads(Path("/etc/tenderlens/runtime.json").read_text())
images = json.loads(Path("images.json").read_text())
os.environ["AWS_REGION"] = config["region"]
os.environ["AWS_DEFAULT_REGION"] = config["region"]
registry = config["backendRepository"].split("/")[0]
password = subprocess.run(
    ["aws", "ecr", "get-login-password", "--region", config["region"]],
    check=True,
    capture_output=True,
).stdout
subprocess.run(
    ["docker", "login", "--username", "AWS", "--password-stdin", registry],
    input=password,
    check=True,
)
for image in [images["backend"], images["frontend"], "nginx:1.28-alpine"]:
    subprocess.run(["docker", "pull", image], check=True)
env = dict(os.environ)
env["BOOTSTRAP_USERNAME"] = (
    "{{resolve:secretsmanager:" + config["databaseSecret"] + ":SecretString:username}}"
)
env["BOOTSTRAP_PASSWORD"] = (
    "{{resolve:secretsmanager:" + config["databaseSecret"] + ":SecretString:password}}"
)
env["PROVIDER_CONFIG"] = (
    "{{resolve:secretsmanager:" + config["integrationSecret"] + ":SecretString}}"
)
subprocess.run(
    [sys.executable, "vendor/asm-exec", "--", sys.executable, "scripts/launch.py"],
    env=env,
    check=True,
)
