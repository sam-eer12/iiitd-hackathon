"""Render the optional public HTTPS demo entry point; no AWS calls."""

import json
from pathlib import Path

from render import A, R, S, output, resource, role, statement, template

root = Path(__file__).parent
t = template(
    "TenderLens demo HTTPS entry point to the private application ALB",
    {
        "Vpc": {"Type": "AWS::EC2::VPC::Id"},
        "Subnets": {"Type": "List<AWS::EC2::Subnet::Id>"},
        "AlbSecurityGroup": {"Type": "AWS::EC2::SecurityGroup::Id"},
        "OriginDns": {"Type": "String"},
        "DataKeyArn": {"Type": "String"},
    },
)
resource(
    t,
    "Logs",
    "Logs::LogGroup",
    {
        "LogGroupName": S("/aws/lambda/${AWS::StackName}"),
        "RetentionInDays": 30,
        "KmsKeyId": R("DataKeyArn"),
    },
    "Encrypted request execution logs; do not log request payloads",
    retain=True,
)
resource(
    t,
    "ProxyGroup",
    "EC2::SecurityGroup",
    {
        "VpcId": R("Vpc"),
        "GroupDescription": "HTTPS demo proxy to private ALB only",
        "SecurityGroupEgress": [
            {
                "IpProtocol": "tcp",
                "FromPort": 80,
                "ToPort": 80,
                "DestinationSecurityGroupId": R("AlbSecurityGroup"),
            }
        ],
    },
    "Proxy can only connect to the private application ALB",
)
resource(
    t,
    "AlbIngress",
    "EC2::SecurityGroupIngress",
    {
        "GroupId": R("AlbSecurityGroup"),
        "IpProtocol": "tcp",
        "FromPort": 80,
        "ToPort": 80,
        "SourceSecurityGroupId": R("ProxyGroup"),
    },
    "Allow only this proxy into the private ALB",
)
role(
    t,
    "Role",
    "lambda.amazonaws.com",
    [
        statement(
            [
                "ec2:CreateNetworkInterface",
                "ec2:DescribeNetworkInterfaces",
                "ec2:DescribeSubnets",
                "ec2:DeleteNetworkInterface",
                "ec2:AssignPrivateIpAddresses",
                "ec2:UnassignPrivateIpAddresses",
            ],
            "*",
        ),
        statement(["logs:CreateLogStream", "logs:PutLogEvents"], A("Logs", "Arn")),
    ],
)
resource(
    t,
    "Proxy",
    "Lambda::Function",
    {
        "FunctionName": R("AWS::StackName"),
        "Runtime": "python3.13",
        "Handler": "index.handler",
        "Role": A("Role", "Arn"),
        "MemorySize": 512,
        "Timeout": 120,
        "Architectures": ["arm64"],
        "LoggingConfig": {"LogGroup": R("Logs")},
        "Environment": {"Variables": {"ORIGIN_DNS": R("OriginDns")}},
        "VpcConfig": {"SubnetIds": R("Subnets"), "SecurityGroupIds": [R("ProxyGroup")]},
        "Code": {"ZipFile": (root / "scripts/public_proxy.py").read_text()},
    },
    "Public browser HTTPS only; app mutations retain Firebase authentication",
    DependsOn=["AlbIngress"],
)
resource(
    t,
    "Url",
    "Lambda::Url",
    {
        "TargetFunctionArn": A("Proxy", "Arn"),
        "AuthType": "NONE",
        "InvokeMode": "BUFFERED",
    },
    "Public hackathon website with application-level sign-in",
)
resource(
    t,
    "UrlPermission",
    "Lambda::Permission",
    {
        "FunctionName": R("Proxy"),
        "Action": "lambda:InvokeFunctionUrl",
        "Principal": "*",
        "FunctionUrlAuthType": "NONE",
    },
    "Visitors can open the public demo website",
)
resource(
    t,
    "InvokePermission",
    "Lambda::Permission",
    {
        "FunctionName": R("Proxy"),
        "Action": "lambda:InvokeFunction",
        "Principal": "*",
        "InvokedViaFunctionUrl": True,
    },
    "Invocation permission is limited to HTTPS Function URL requests",
)
resource(
    t,
    "Errors",
    "CloudWatch::Alarm",
    {
        "AlarmDescription": "TenderLens HTTPS proxy invocation errors",
        "Namespace": "AWS/Lambda",
        "MetricName": "Errors",
        "Dimensions": [{"Name": "FunctionName", "Value": R("Proxy")}],
        "Statistic": "Sum",
        "Period": 300,
        "EvaluationPeriods": 1,
        "Threshold": 5,
        "ComparisonOperator": "GreaterThanOrEqualToThreshold",
        "TreatMissingData": "notBreaching",
    },
    "Monitor demo proxy failures",
)
output(t, "WebsiteUrl", A("Url", "FunctionUrl"), "Public HTTPS demo website")
(root / "templates/public-proxy.json").write_text(json.dumps(t, indent=2) + "\n")
