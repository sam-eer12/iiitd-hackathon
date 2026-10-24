"""Launch containers; never print resolved configuration or save it to disk."""

import json
import os
import subprocess
from pathlib import Path

config = json.loads(Path("/etc/tenderlens/runtime.json").read_text())
images = json.loads(Path("images.json").read_text())
provider = json.loads(os.environ.pop("PROVIDER_CONFIG"))


def run(*args, **kwargs):
    subprocess.run(list(args), check=True, **kwargs)


def db_url(user):
    return f"postgresql+asyncpg://{user}@{config['databaseHost']}:5432/tenderlens"


backend_env = {
    "APP_ENV": "production",
    "DATABASE_URL": db_url("tl_app"),
    "DATABASE_IAM_AUTH": "true",
    "DATABASE_SSL_CA_FILE": "/app/certs/rds-ca.pem",
    "AWS_REGION": config["region"],
    "STORAGE_BACKEND": "s3",
    "S3_BUCKET": config["evidenceBucket"],
    "TINYFISH_MODE": "live",
    "FIREBASE_PROJECT_ID": "tenderlens-app-2026",
}
allowed = {
    "TINYFISH_API_KEY",
    "SANDBOX_API_KEY",
    "SANDBOX_API_SECRET",
    "SANDBOX_ENVIRONMENT",
    "SANDBOX_RETURN_URL",
    "DIGILOCKER_SIGNING_CERTIFICATE_PATH",
    "ENTITYLOCKER_SIGNING_CERTIFICATE_PATH",
}
backend_env.update({key: str(value) for key, value in provider.items() if key in allowed and value})
if config.get("publicOrigin") and not backend_env.get("SANDBOX_RETURN_URL"):
    backend_env["SANDBOX_RETURN_URL"] = config["publicOrigin"] + "/dashboard/profile"
os.environ.update(backend_env)
os.environ["DATABASE_HOST"] = config["databaseHost"]
docker_env = [part for key in backend_env for part in ["-e", key]]
if os.environ.get("SKIP_MIGRATIONS") != "1":
    mount = f"{Path.cwd()}:/deployment:ro"
    run(
        "docker",
        "run",
        "--rm",
        "-v",
        mount,
        "-e",
        "DATABASE_HOST",
        "-e",
        "AWS_REGION",
        "-e",
        "BOOTSTRAP_USERNAME",
        "-e",
        "BOOTSTRAP_PASSWORD",
        images["backend"],
        "/app/.venv/bin/python",
        "/deployment/scripts/bootstrap_db.py",
    )
    os.environ["DATABASE_URL"] = db_url("tl_migrator")
    run(
        "docker",
        "run",
        "--rm",
        *docker_env,
        images["backend"],
        "sh",
        "-ec",
        "/app/.venv/bin/alembic upgrade head && /app/.venv/bin/python -m app.cli.seed",
    )
os.environ.pop("BOOTSTRAP_PASSWORD", None)
os.environ.pop("BOOTSTRAP_USERNAME", None)
os.environ["DATABASE_URL"] = db_url("tl_app")
if subprocess.run(
    ["docker", "network", "inspect", "tenderlens"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
).returncode:
    run("docker", "network", "create", "tenderlens")
log_args = [
    "--log-driver",
    "awslogs",
    "--log-opt",
    f"awslogs-region={config['region']}",
    "--log-opt",
    f"awslogs-group={config['logGroup']}",
]
for name in ["gateway", "web", "api", "worker"]:
    subprocess.run(
        ["docker", "rm", "-f", "tenderlens-" + name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
common = [
    "--restart",
    "unless-stopped",
    "--network",
    "tenderlens",
    "--security-opt",
    "no-new-privileges:true",
    "--cap-drop",
    "ALL",
]
for name, command in [("api", []), ("worker", ["/app/.venv/bin/python", "-m", "app.worker"])]:
    run(
        "docker",
        "run",
        "-d",
        "--name",
        "tenderlens-" + name,
        "--network-alias",
        name,
        *common,
        *log_args,
        "--log-opt",
        f"awslogs-stream={name}",
        *docker_env,
        images["backend"],
        *command,
    )
run(
    "docker",
    "run",
    "-d",
    "--name",
    "tenderlens-web",
    "--network-alias",
    "web",
    *common,
    *log_args,
    "--log-opt",
    "awslogs-stream=web",
    "-e",
    "TENDERLENS_API_URL=http://api:8000",
    "-e",
    "TENDERLENS_REMOTE_WORKSPACE=true",
    "-e",
    "TENDERLENS_PUBLIC_ORIGIN=" + config.get("publicOrigin", ""),
    images["frontend"],
)
run(
    "docker",
    "run",
    "-d",
    "--name",
    "tenderlens-gateway",
    "--restart",
    "unless-stopped",
    "--network",
    "tenderlens",
    *log_args,
    "--log-opt",
    "awslogs-stream=gateway",
    "-p",
    "8080:8080",
    "-v",
    f"{Path.cwd()}/scripts/nginx.conf:/etc/nginx/conf.d/default.conf:ro",
    "nginx:1.28-alpine",
)
