"""Plan/apply the three stacks using the tenderlens profile; never retrieve secrets."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("stack", choices=["storage", "data", "service"])
parser.add_argument("--apply", action="store_true", help="Execute the reviewed change set")
parser.add_argument("--profile", default="tenderlens")
parser.add_argument("--region", default="ap-south-1")
parser.add_argument("--mode", choices=["demo", "production"], default="demo")
parser.add_argument("--connection-arn")
parser.add_argument("--enable-public-edge", action="store_true")
args = parser.parse_args()
session = boto3.Session(profile_name=args.profile, region_name=args.region)
cf = session.client("cloudformation")
names = {"storage": "tenderlens-storage", "data": "tenderlens-db", "service": "tenderlens-app"}
body = json.loads((Path(__file__).parent / "templates" / f"{args.stack}.json").read_text())


def stack_outputs(name):
    response = cf.describe_stacks(StackName=name)["Stacks"][0]
    return {item["OutputKey"]: item["OutputValue"] for item in response.get("Outputs", [])}


values = {}
if args.stack in {"data", "service"}:
    values.update(stack_outputs(names["storage"]))
if args.stack == "data":
    values["DeploymentMode"] = args.mode
    versions = session.client("rds").describe_db_engine_versions(Engine="postgres")[
        "DBEngineVersions"
    ]
    supported = [
        v["EngineVersion"]
        for v in versions
        if v["EngineVersion"].startswith("18.") and v.get("Status") == "available"
    ]
    values["PostgresVersion"] = max(supported, key=lambda value: tuple(map(int, value.split("."))))
if args.stack == "service":
    values.update(stack_outputs(names["data"]))
    if not args.connection_arn:
        parser.error("--connection-arn is required for the service stack")
    connection = session.client("codeconnections").get_connection(
        ConnectionArn=args.connection_arn
    )["Connection"]
    if connection["ConnectionStatus"] != "AVAILABLE":
        raise SystemExit("Complete GitHub OAuth for the CodeConnection before deploying.")
    values["ConnectionArn"] = args.connection_arn
    if args.enable_public_edge:
        values["EnablePublicEdge"] = "true"
    prefix = session.client("ec2").describe_managed_prefix_lists(
        Filters=[
            {
                "Name": "prefix-list-name",
                "Values": ["com.amazonaws.global.cloudfront.origin-facing"],
            }
        ]
    )["PrefixLists"]
    values["CloudFrontPrefixList"] = prefix[0]["PrefixListId"]
try:
    current = cf.describe_stacks(StackName=names[args.stack])["Stacks"][0]
    change_type = "UPDATE"
    if current["StackStatus"] in {"ROLLBACK_COMPLETE", "IMPORT_ROLLBACK_COMPLETE"}:
        raise SystemExit(
            "The stack needs explicit recovery; this script never deletes retained resources."
        )
except ClientError as exc:
    if "does not exist" not in str(exc):
        raise
    change_type = "CREATE"
change_name = "release-" + datetime.now(UTC).strftime("%Y%m%d-%H%M%S-") + uuid4().hex[:6]
response = cf.create_change_set(
    StackName=names[args.stack],
    ChangeSetName=change_name,
    ChangeSetType=change_type,
    TemplateBody=json.dumps(body),
    Capabilities=["CAPABILITY_IAM"],
    Parameters=[
        {"ParameterKey": key, "ParameterValue": value}
        for key, value in values.items()
        if key in body["Parameters"]
    ],
    Tags=[{"Key": "Project", "Value": "TenderLens"}],
)
change_id = response["Id"]
cf.get_waiter("change_set_create_complete").wait(ChangeSetName=change_id)
change = cf.describe_change_set(ChangeSetName=change_id)
print(
    json.dumps(
        {
            "changeSet": change_id,
            "changes": [v["ResourceChange"] for v in change.get("Changes", [])],
        },
        default=str,
        indent=2,
    )
)
if args.apply:
    cf.execute_change_set(ChangeSetName=change_id)
    waiter = "stack_create_complete" if change_type == "CREATE" else "stack_update_complete"
    cf.get_waiter(waiter).wait(StackName=names[args.stack])
    print(json.dumps(stack_outputs(names[args.stack]), indent=2))
