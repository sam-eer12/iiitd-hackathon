"""Render the reviewable CloudFormation templates. No AWS calls or credentials."""

import json
from pathlib import Path

ROOT = Path(__file__).parent


def R(name):
    return {"Ref": name}


def A(name, attr):
    return {"Fn::GetAtt": [name, attr]}


def S(text):
    return {"Fn::Sub": text}


def template(description, parameters):
    return {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": description,
        "Metadata": {"AWSToolsMetrics": {"AWSAgentToolkit": "aws-cloudformation@3"}},
        "Parameters": parameters,
        "Resources": {},
        "Outputs": {},
    }


def resource(t, name, kind, props, why, must=(), retain=False, **extra):
    entry = {
        "Type": "AWS::" + kind,
        "Metadata": {"com.aws.cloudformation.Context": {"why": why, "must": list(must)}},
        "Properties": props,
        **extra,
    }
    if retain:
        entry.update(DeletionPolicy="Retain", UpdateReplacePolicy="Retain")
    t["Resources"][name] = entry
    return R(name)


def output(t, name, value, description):
    t["Outputs"][name] = {"Value": value, "Description": description}


def statement(actions, resources, **extra):
    return {"Effect": "Allow", "Action": actions, "Resource": resources, **extra}


def role(t, name, service, statements, managed=()):
    return resource(
        t,
        name,
        "IAM::Role",
        {
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": service},
                        "Action": "sts:AssumeRole",
                    }
                ],
            },
            "ManagedPolicyArns": list(managed),
            "Policies": [
                {
                    "PolicyName": "project-access",
                    "PolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": statements,
                    },
                }
            ],
        },
        "Service-specific permissions for this deployment",
        ["Scope data access to project resources"],
    )


def bucket(t, name, kms):
    resource(
        t,
        name,
        "S3::Bucket",
        {
            "PublicAccessBlockConfiguration": {
                key: True
                for key in [
                    "BlockPublicAcls",
                    "BlockPublicPolicy",
                    "IgnorePublicAcls",
                    "RestrictPublicBuckets",
                ]
            },
            "BucketEncryption": {
                "ServerSideEncryptionConfiguration": [
                    {
                        "ServerSideEncryptionByDefault": {
                            "SSEAlgorithm": "aws:kms",
                            "KMSMasterKeyID": kms,
                        },
                        "BucketKeyEnabled": True,
                    }
                ]
            },
            "VersioningConfiguration": {"Status": "Enabled"},
            "OwnershipControls": {"Rules": [{"ObjectOwnership": "BucketOwnerEnforced"}]},
        },
        "Private encrypted durable storage",
        ["Retain data on stack removal", "Block public access"],
        retain=True,
    )
    resource(
        t,
        name + "TLS",
        "S3::BucketPolicy",
        {
            "Bucket": R(name),
            "PolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Deny",
                        "Principal": "*",
                        "Action": "s3:*",
                        "Resource": [A(name, "Arn"), S("${" + name + ".Arn}/*")],
                        "Condition": {"Bool": {"aws:SecureTransport": "false"}},
                    }
                ],
            },
        },
        "Reject cleartext object access",
        ["Keep the TLS deny policy"],
    )


def data():
    t = template(
        "TenderLens durable data and network - private Multi-AZ RDS PostgreSQL and encrypted S3",
        {
            "DeploymentMode": {
                "Type": "String",
                "Default": "demo",
                "AllowedValues": ["demo", "production"],
            },
            "DatabaseIdentifier": {
                "Type": "String",
                "Default": "tenderlens-data-postgres",
                "AllowedPattern": "[a-z][a-z0-9-]{0,62}",
            },
            "PostgresVersion": {"Type": "String", "Default": "18.6", "AllowedPattern": r"18\.\d+"},
            "DatabaseClass": {
                "Type": "String",
                "Default": "db.t4g.micro",
                "AllowedValues": ["db.t4g.micro", "db.t4g.small", "db.t4g.medium"],
            },
        },
    )
    t["Conditions"] = {"Production": {"Fn::Equals": [R("DeploymentMode"), "production"]}}
    resource(
        t,
        "Vpc",
        "EC2::VPC",
        {"CidrBlock": "10.42.0.0/16", "EnableDnsSupport": True, "EnableDnsHostnames": True},
        "Dedicated network; no default-VPC dependency",
    )
    resource(
        t,
        "Gateway",
        "EC2::InternetGateway",
        {},
        "Outbound access for build/deploy host and CloudFront VPC-origin prerequisite",
    )
    resource(
        t,
        "GatewayAttachment",
        "EC2::VPCGatewayAttachment",
        {"VpcId": R("Vpc"), "InternetGatewayId": R("Gateway")},
        "Attach project gateway",
    )
    resource(
        t,
        "PublicRoutes",
        "EC2::RouteTable",
        {"VpcId": R("Vpc")},
        "Outbound internet for EC2; databases have no internet route",
    )
    resource(
        t,
        "PublicDefaultRoute",
        "EC2::Route",
        {
            "RouteTableId": R("PublicRoutes"),
            "DestinationCidrBlock": "0.0.0.0/0",
            "GatewayId": R("Gateway"),
        },
        "Avoid a NAT gateway for a small deployment",
        DependsOn="GatewayAttachment",
    )
    for i in range(2):
        for prefix, octet, public in [("Public", i, True), ("Private", i + 10, False)]:
            name = f"{prefix}Subnet{i + 1}"
            resource(
                t,
                name,
                "EC2::Subnet",
                {
                    "VpcId": R("Vpc"),
                    "AvailabilityZone": {"Fn::Select": [i, {"Fn::GetAZs": ""}]},
                    "CidrBlock": f"10.42.{octet}.0/24",
                    "MapPublicIpOnLaunch": public,
                },
                "Separate availability zone for application and database placement",
            )
            if public:
                resource(
                    t,
                    name + "Route",
                    "EC2::SubnetRouteTableAssociation",
                    {"SubnetId": R(name), "RouteTableId": R("PublicRoutes")},
                    "Associate outbound route",
                )
    resource(
        t,
        "AppSecurityGroup",
        "EC2::SecurityGroup",
        {"VpcId": R("Vpc"), "GroupDescription": "Application host - no public inbound access"},
        "Host accepts application traffic only from the internal load balancer",
        ["Never expose SSH or database ports"],
    )
    resource(
        t,
        "DbSecurityGroup",
        "EC2::SecurityGroup",
        {
            "VpcId": R("Vpc"),
            "GroupDescription": "PostgreSQL from application host only",
            "SecurityGroupIngress": [
                {
                    "IpProtocol": "tcp",
                    "FromPort": 5432,
                    "ToPort": 5432,
                    "SourceSecurityGroupId": R("AppSecurityGroup"),
                }
            ],
        },
        "RDS has no public network path",
        ["Only application security group may connect"],
    )
    resource(
        t,
        "DataKey",
        "KMS::Key",
        {
            "EnableKeyRotation": True,
            "KeyPolicy": {
                "Version": "2012-10-17",
                "Statement": [
                    statement(
                        "kms:*",
                        "*",
                        Principal={"AWS": S("arn:${AWS::Partition}:iam::${AWS::AccountId}:root")},
                    ),
                    statement(
                        [
                            "kms:Encrypt",
                            "kms:Decrypt",
                            "kms:ReEncrypt*",
                            "kms:GenerateDataKey*",
                            "kms:DescribeKey",
                        ],
                        "*",
                        Principal={"Service": S("logs.${AWS::Region}.amazonaws.com")},
                        Condition={
                            "ArnLike": {
                                "kms:EncryptionContext:aws:logs:arn": S(
                                    "arn:${AWS::Partition}:logs:${AWS::Region}:${AWS::AccountId}:log-group:*"
                                )
                            }
                        },
                    ),
                ],
            },
        },
        "Customer-managed encryption for data, artifacts and database logs",
        ["Retain key while retained data exists"],
        retain=True,
    )
    for name in ["EvidenceBucket", "ArtifactBucket"]:
        bucket(t, name, A("DataKey", "Arn"))
    resource(
        t,
        "DatabaseLogs",
        "Logs::LogGroup",
        {
            "LogGroupName": S("/aws/rds/instance/${AWS::StackName}-postgres/postgresql"),
            "KmsKeyId": A("DataKey", "Arn"),
            "RetentionInDays": 30,
        },
        "Encrypted PostgreSQL security and error logs",
        retain=True,
    )
    resource(
        t,
        "DbSubnets",
        "RDS::DBSubnetGroup",
        {
            "DBSubnetGroupDescription": "Isolated PostgreSQL subnets",
            "SubnetIds": [R("PrivateSubnet1"), R("PrivateSubnet2")],
        },
        "Database failover spans two availability zones",
    )
    resource(
        t,
        "DbParameters",
        "RDS::DBParameterGroup",
        {
            "Family": "postgres18",
            "Description": "Require verified encrypted PostgreSQL connections",
            "Parameters": {"rds.force_ssl": "1"},
        },
        "Enforce database TLS",
        ["Keep rds.force_ssl enabled"],
    )
    resource(
        t,
        "Database",
        "RDS::DBInstance",
        {
            "DBInstanceIdentifier": R("DatabaseIdentifier"),
            "DBName": "tenderlens",
            "Engine": "postgres",
            "EngineVersion": R("PostgresVersion"),
            "DBInstanceClass": R("DatabaseClass"),
            "AllocatedStorage": "20",
            "MaxAllocatedStorage": {"Fn::If": ["Production", 100, R("AWS::NoValue")]},
            "StorageType": "gp3",
            "MasterUsername": "tl_owner",
            "ManageMasterUserPassword": True,
            "MasterUserSecret": {"KmsKeyId": A("DataKey", "Arn")},
            "StorageEncrypted": True,
            "KmsKeyId": A("DataKey", "Arn"),
            "MultiAZ": {"Fn::If": ["Production", True, False]},
            "PubliclyAccessible": False,
            "DBSubnetGroupName": R("DbSubnets"),
            "DBParameterGroupName": R("DbParameters"),
            "VPCSecurityGroups": [R("DbSecurityGroup")],
            "Port": "5432",
            "EnableIAMDatabaseAuthentication": True,
            "BackupRetentionPeriod": {"Fn::If": ["Production", 7, 1]},
            "DeletionProtection": True,
            "CopyTagsToSnapshot": True,
            "AutoMinorVersionUpgrade": True,
            "AllowMajorVersionUpgrade": False,
            "EnablePerformanceInsights": {"Fn::If": ["Production", True, False]},
            "PerformanceInsightsRetentionPeriod": {"Fn::If": ["Production", 7, R("AWS::NoValue")]},
            "PerformanceInsightsKMSKeyId": {
                "Fn::If": ["Production", A("DataKey", "Arn"), R("AWS::NoValue")]
            },
            "EnableCloudwatchLogsExports": ["postgresql"],
            "Tags": [
                {"Key": "Project", "Value": "TenderLens"},
                {"Key": "created_by", "Value": "rds-oss-skill"},
                {"Key": "generation_model", "Value": "gpt-6"},
            ],
        },
        "Single authoritative PostgreSQL store with automatic AZ failover",
        [
            "Retain on removal",
            "Use managed master credentials only for bootstrap",
            "Application uses a restricted IAM database role",
        ],
        retain=True,
        DependsOn="DatabaseLogs",
    )
    for name in ["BackendRepository", "FrontendRepository"]:
        resource(
            t,
            name,
            "ECR::Repository",
            {
                "ImageTagMutability": "IMMUTABLE",
                "ImageScanningConfiguration": {"ScanOnPush": True},
                "EncryptionConfiguration": {"EncryptionType": "KMS", "KmsKey": A("DataKey", "Arn")},
                "LifecyclePolicy": {
                    "LifecyclePolicyText": json.dumps(
                        {
                            "rules": [
                                {
                                    "rulePriority": 1,
                                    "description": "Expire untagged build layers after 7 days",
                                    "selection": {
                                        "tagStatus": "untagged",
                                        "countType": "sinceImagePushed",
                                        "countUnit": "days",
                                        "countNumber": 7,
                                    },
                                    "action": {"type": "expire"},
                                }
                            ]
                        }
                    )
                },
            },
            "Immutable release images; retained for rollback",
            retain=True,
        )
    resource(
        t,
        "IntegrationSecret",
        "SecretsManager::Secret",
        {
            "KmsKeyId": A("DataKey", "Arn"),
            "Description": "Server-side provider configuration; populate through Secrets Manager console",
            "GenerateSecretString": {
                "SecretStringTemplate": json.dumps(
                    {"TINYFISH_API_KEY": "", "SANDBOX_API_KEY": "", "SANDBOX_API_SECRET": ""}
                ),
                "GenerateStringKey": "bootstrapNonce",
                "PasswordLength": 32,
            },
        },
        "No provider keys in source, build logs or CloudFormation parameters",
        ["Resolve only at runtime through asm-exec", "Empty keys keep metered providers disabled"],
        retain=True,
    )
    for name in [
        "Vpc",
        "PublicSubnet1",
        "PublicSubnet2",
        "PrivateSubnet1",
        "PrivateSubnet2",
        "AppSecurityGroup",
        "EvidenceBucket",
        "ArtifactBucket",
        "IntegrationSecret",
    ]:
        output(t, name, R(name), name + " identifier")
    for name, value in {
        "DataKeyArn": A("DataKey", "Arn"),
        "DatabaseHost": A("Database", "Endpoint.Address"),
        "DatabaseResourceId": A("Database", "DbiResourceId"),
        "DatabaseSecretArn": A("Database", "MasterUserSecret.SecretArn"),
        "BackendRepositoryUri": A("BackendRepository", "RepositoryUri"),
        "FrontendRepositoryUri": A("FrontendRepository", "RepositoryUri"),
        "BackendRepositoryArn": A("BackendRepository", "Arn"),
        "FrontendRepositoryArn": A("FrontendRepository", "Arn"),
    }.items():
        output(t, name, value, name + " for the service stack")
    return t


def service():
    parameter_names = [
        "Vpc",
        "PublicSubnet1",
        "PublicSubnet2",
        "PrivateSubnet1",
        "PrivateSubnet2",
        "AppSecurityGroup",
        "EvidenceBucket",
        "ArtifactBucket",
        "IntegrationSecret",
        "DataKeyArn",
        "DatabaseHost",
        "DatabaseResourceId",
        "DatabaseSecretArn",
        "BackendRepositoryUri",
        "FrontendRepositoryUri",
        "BackendRepositoryArn",
        "FrontendRepositoryArn",
    ]
    parameters = {name: {"Type": "String", "MinLength": 1} for name in parameter_names}
    parameters.update(
        {
            "EnablePublicEdge": {
                "Type": "String",
                "Default": "false",
                "AllowedValues": ["false", "true"],
                "Description": "Enable after AWS approves CloudFront account verification",
            },
            "ConnectionArn": {
                "Type": "String",
                "AllowedPattern": r"arn:aws:codeconnections:.*:connection/.*",
            },
            "RepositoryId": {
                "Type": "String",
                "Default": "sam-eer12/iiitd-hackathon",
                "AllowedPattern": r"[\w.-]+/[\w.-]+",
            },
            "Branch": {"Type": "String", "Default": "main", "AllowedPattern": r"[\w./-]+"},
            "InstanceType": {
                "Type": "String",
                "Default": "t3.small",
                "AllowedValues": ["t3.small", "t3.medium", "t3.large"],
            },
            "ImageId": {
                "Type": "AWS::SSM::Parameter::Value<AWS::EC2::Image::Id>",
                "Default": "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64",
            },
            "CloudFrontPrefixList": {"Type": "String", "AllowedPattern": "pl-[a-f0-9]+"},
        }
    )
    t = template(
        "TenderLens containers and CI/CD - preserve Next.js 16 with private CloudFront ingress and EC2 API/worker",
        parameters,
    )
    t["Conditions"] = {"PublicEdge": {"Fn::Equals": [R("EnablePublicEdge"), "true"]}}
    resource(
        t,
        "Logs",
        "Logs::LogGroup",
        {"RetentionInDays": 30, "KmsKeyId": R("DataKeyArn")},
        "Central encrypted application, worker and build logs",
        retain=True,
    )
    role(
        t,
        "HostRole",
        "ec2.amazonaws.com",
        [
            statement(["ecr:GetAuthorizationToken"], "*"),
            statement(
                [
                    "ecr:BatchGetImage",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchCheckLayerAvailability",
                ],
                [R("BackendRepositoryArn"), R("FrontendRepositoryArn")],
            ),
            statement(["s3:GetObject"], S("arn:${AWS::Partition}:s3:::${ArtifactBucket}/*")),
            statement(
                ["s3:PutObject"],
                S("arn:${AWS::Partition}:s3:::${ArtifactBucket}/bootstrap/current.tar.gz"),
            ),
            statement(["s3:ListBucket"], S("arn:${AWS::Partition}:s3:::${EvidenceBucket}")),
            statement(
                ["s3:GetObject", "s3:PutObject"],
                S("arn:${AWS::Partition}:s3:::${EvidenceBucket}/*"),
            ),
            statement(
                ["secretsmanager:GetSecretValue"], [R("DatabaseSecretArn"), R("IntegrationSecret")]
            ),
            statement(["kms:Decrypt", "kms:GenerateDataKey", "kms:DescribeKey"], R("DataKeyArn")),
            statement(
                ["rds-db:connect"],
                [
                    S(
                        "arn:${AWS::Partition}:rds-db:${AWS::Region}:${AWS::AccountId}:dbuser:${DatabaseResourceId}/tl_app"
                    ),
                    S(
                        "arn:${AWS::Partition}:rds-db:${AWS::Region}:${AWS::AccountId}:dbuser:${DatabaseResourceId}/tl_migrator"
                    ),
                ],
            ),
            statement(["logs:CreateLogStream", "logs:PutLogEvents"], A("Logs", "Arn")),
        ],
        managed=[S("arn:${AWS::Partition}:iam::aws:policy/AmazonSSMManagedInstanceCore")],
    )
    resource(
        t,
        "HostProfile",
        "IAM::InstanceProfile",
        {"Roles": [R("HostRole")]},
        "Instance role replaces static AWS keys",
    )
    resource(
        t,
        "AlbSecurityGroup",
        "EC2::SecurityGroup",
        {
            "VpcId": R("Vpc"),
            "GroupDescription": "CloudFront origin traffic only",
            "SecurityGroupIngress": [
                {
                    "IpProtocol": "tcp",
                    "FromPort": 80,
                    "ToPort": 80,
                    "SourcePrefixListId": R("CloudFrontPrefixList"),
                }
            ],
        },
        "Internal ALB reachable only through CloudFront VPC origin",
        ["No public ALB or public ingress CIDR"],
    )
    resource(
        t,
        "HostIngress",
        "EC2::SecurityGroupIngress",
        {
            "GroupId": R("AppSecurityGroup"),
            "IpProtocol": "tcp",
            "FromPort": 8080,
            "ToPort": 8080,
            "SourceSecurityGroupId": R("AlbSecurityGroup"),
        },
        "Only ALB can reach the reverse proxy",
    )
    resource(
        t,
        "Alb",
        "ElasticLoadBalancingV2::LoadBalancer",
        {
            "Type": "application",
            "Scheme": "internal",
            "Subnets": [R("PrivateSubnet1"), R("PrivateSubnet2")],
            "SecurityGroups": [R("AlbSecurityGroup")],
            "LoadBalancerAttributes": [
                {"Key": "routing.http.drop_invalid_header_fields.enabled", "Value": "true"}
            ],
        },
        "Private origin keeps application hosts off the public request path",
    )
    resource(
        t,
        "Targets",
        "ElasticLoadBalancingV2::TargetGroup",
        {
            "VpcId": R("Vpc"),
            "Port": 8080,
            "Protocol": "HTTP",
            "TargetType": "instance",
            "HealthCheckPath": "/health/ready",
            "HealthCheckIntervalSeconds": 30,
            "HealthyThresholdCount": 2,
            "TargetGroupAttributes": [
                {"Key": "deregistration_delay.timeout_seconds", "Value": "30"}
            ],
        },
        "Health checks require both the web server and database-backed API",
    )
    resource(
        t,
        "Listener",
        "ElasticLoadBalancingV2::Listener",
        {
            "LoadBalancerArn": R("Alb"),
            "Port": 80,
            "Protocol": "HTTP",
            "DefaultActions": [{"Type": "forward", "TargetGroupArn": R("Targets")}],
        },
        "HTTP restricted to private VPC-origin transport; viewer traffic uses HTTPS",
    )
    userdata = """#!/bin/bash
set -euo pipefail
dnf install -y docker python3
aws --version
systemctl enable --now docker
mkdir -p /opt/tenderlens /etc/tenderlens
cat > /etc/tenderlens/runtime.json <<'CONFIG'
{"region":"${AWS::Region}","databaseHost":"${DatabaseHost}","databaseSecret":"${DatabaseSecretArn}","integrationSecret":"${IntegrationSecret}","evidenceBucket":"${EvidenceBucket}","logGroup":"${Logs}","backendRepository":"${BackendRepositoryUri}","frontendRepository":"${FrontendRepositoryUri}","artifactBucket":"${ArtifactBucket}"}
CONFIG
chmod 600 /etc/tenderlens/runtime.json
systemctl enable --now amazon-ssm-agent
if aws s3 cp s3://${ArtifactBucket}/bootstrap/current.tar.gz /opt/tenderlens/current.tar.gz --only-show-errors; then
  mkdir -p /opt/tenderlens/incoming
  tar -xzf /opt/tenderlens/current.tar.gz -C /opt/tenderlens/incoming
  cd /opt/tenderlens/incoming
  bash scripts/deploy.sh
fi
"""
    resource(
        t,
        "LaunchTemplate",
        "EC2::LaunchTemplate",
        {
            "LaunchTemplateData": {
                "ImageId": R("ImageId"),
                "InstanceType": R("InstanceType"),
                "IamInstanceProfile": {"Arn": A("HostProfile", "Arn")},
                "MetadataOptions": {
                    "HttpTokens": "required",
                    "HttpPutResponseHopLimit": 2,
                    "HttpEndpoint": "enabled",
                },
                "NetworkInterfaces": [
                    {
                        "DeviceIndex": 0,
                        "AssociatePublicIpAddress": True,
                        "Groups": [R("AppSecurityGroup")],
                    }
                ],
                "BlockDeviceMappings": [
                    {
                        "DeviceName": "/dev/xvda",
                        "Ebs": {
                            "VolumeSize": 30,
                            "VolumeType": "gp3",
                            "Encrypted": True,
                            "KmsKeyId": R("DataKeyArn"),
                            "DeleteOnTermination": True,
                        },
                    }
                ],
                "UserData": {"Fn::Base64": S(userdata)},
            }
        },
        "Replaceable SSM-managed Docker host; public IP provides outbound access only",
        ["No SSH key or inbound SSH", "IMDSv2 required; hop limit 2 for container IAM"],
    )
    resource(
        t,
        "Hosts",
        "AutoScaling::AutoScalingGroup",
        {
            "MinSize": "1",
            "MaxSize": "2",
            "DesiredCapacity": "1",
            "VPCZoneIdentifier": [R("PublicSubnet1"), R("PublicSubnet2")],
            "LaunchTemplate": {
                "LaunchTemplateId": R("LaunchTemplate"),
                "Version": A("LaunchTemplate", "LatestVersionNumber"),
            },
            "TargetGroupARNs": [R("Targets")],
            "HealthCheckType": "EC2",
            "HealthCheckGracePeriod": 900,
            "Tags": [
                {"Key": "Project", "Value": "TenderLens", "PropagateAtLaunch": True},
                {"Key": "DeploymentStack", "Value": R("AWS::StackName"), "PropagateAtLaunch": True},
            ],
        },
        "One recoverable host initially; capacity can grow after load testing",
        ["Persistent application data lives in RDS/S3, not instance disk"],
    )
    resource(
        t,
        "VpcOrigin",
        "CloudFront::VpcOrigin",
        {
            "VpcOriginEndpointConfig": {
                "Arn": R("Alb"),
                "Name": S("${AWS::StackName}-origin"),
                "HTTPPort": 80,
                "HTTPSPort": 443,
                "OriginProtocolPolicy": "http-only",
                "OriginSSLProtocols": ["TLSv1.2"],
            }
        },
        "Private CloudFront-to-ALB connectivity",
        DependsOn="Listener",
        Condition="PublicEdge",
    )
    resource(
        t,
        "Distribution",
        "CloudFront::Distribution",
        {
            "DistributionConfig": {
                "Enabled": True,
                "HttpVersion": "http2and3",
                "IPV6Enabled": True,
                "Origins": [
                    {
                        "Id": "application",
                        "DomainName": A("Alb", "DNSName"),
                        "VpcOriginConfig": {
                            "VpcOriginId": A("VpcOrigin", "Id"),
                            "OriginReadTimeout": 120,
                        },
                    }
                ],
                "DefaultCacheBehavior": {
                    "TargetOriginId": "application",
                    "ViewerProtocolPolicy": "redirect-to-https",
                    "AllowedMethods": ["GET", "HEAD", "OPTIONS", "PUT", "PATCH", "POST", "DELETE"],
                    "CachedMethods": ["GET", "HEAD"],
                    "Compress": True,
                    "CachePolicyId": "4135ea2d-6df8-44a3-9df3-4b5a84be39ad",
                    "OriginRequestPolicyId": "216adef6-5c7f-47e4-b989-5492eafa07d3",
                },
                "ViewerCertificate": {"CloudFrontDefaultCertificate": True},
                "PriceClass": "PriceClass_200",
            }
        },
        "Managed HTTPS endpoint without requiring a custom domain; Next.js handles caching",
        ["Never cache authenticated responses", "Forward viewer Host for same-origin checks"],
        Condition="PublicEdge",
    )
    role(
        t,
        "BuildRole",
        "codebuild.amazonaws.com",
        [
            statement(
                ["s3:GetObject", "s3:GetObjectVersion", "s3:PutObject"],
                S("arn:${AWS::Partition}:s3:::${ArtifactBucket}/*"),
            ),
            statement(
                ["s3:GetBucketLocation", "s3:GetBucketVersioning"],
                S("arn:${AWS::Partition}:s3:::${ArtifactBucket}"),
            ),
            statement(
                ["kms:Decrypt", "kms:Encrypt", "kms:GenerateDataKey", "kms:DescribeKey"],
                R("DataKeyArn"),
            ),
            statement(["ecr:GetAuthorizationToken"], "*"),
            statement(
                [
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage",
                    "ecr:InitiateLayerUpload",
                    "ecr:UploadLayerPart",
                    "ecr:CompleteLayerUpload",
                    "ecr:PutImage",
                ],
                [R("BackendRepositoryArn"), R("FrontendRepositoryArn")],
            ),
            statement(["logs:CreateLogStream", "logs:PutLogEvents"], A("Logs", "Arn")),
        ],
    )
    resource(
        t,
        "Build",
        "CodeBuild::Project",
        {
            "ServiceRole": A("BuildRole", "Arn"),
            "Artifacts": {"Type": "CODEPIPELINE"},
            "Source": {"Type": "CODEPIPELINE", "BuildSpec": "backend/deploy/buildspec.yml"},
            "Environment": {
                "Type": "LINUX_CONTAINER",
                "ComputeType": "BUILD_GENERAL1_SMALL",
                "Image": "aws/codebuild/standard:7.0",
                "PrivilegedMode": True,
                "EnvironmentVariables": [
                    {"Name": key, "Value": val, "Type": "PLAINTEXT"}
                    for key, val in {
                        "BACKEND_REPOSITORY": R("BackendRepositoryUri"),
                        "FRONTEND_REPOSITORY": R("FrontendRepositoryUri"),
                        "LOG_GROUP": R("Logs"),
                    }.items()
                ],
            },
            "TimeoutInMinutes": 45,
            "LogsConfig": {
                "CloudWatchLogs": {
                    "Status": "ENABLED",
                    "GroupName": R("Logs"),
                    "StreamName": "build",
                }
            },
        },
        "Docker-isolated lint, migrations, tests and image builds with no production secrets",
        [
            "No VPC attachment: build needs registry access",
            "Never pass provider keys as Docker build arguments",
        ],
    )
    resource(
        t,
        "PipelineLogs",
        "Logs::LogGroup",
        {
            "LogGroupName": S("/aws/codepipeline/${AWS::StackName}-pipeline"),
            "KmsKeyId": R("DataKeyArn"),
            "RetentionInDays": 30,
        },
        "Encrypted EC2 deployment execution logs",
        retain=True,
    )
    role(
        t,
        "PipelineRole",
        "codepipeline.amazonaws.com",
        [
            statement(
                ["s3:GetObject", "s3:GetObjectVersion", "s3:PutObject"],
                S("arn:${AWS::Partition}:s3:::${ArtifactBucket}/*"),
            ),
            statement(
                ["s3:GetBucketVersioning", "s3:GetBucketLocation"],
                S("arn:${AWS::Partition}:s3:::${ArtifactBucket}"),
            ),
            statement(
                ["kms:Decrypt", "kms:Encrypt", "kms:GenerateDataKey", "kms:DescribeKey"],
                R("DataKeyArn"),
            ),
            statement(
                ["codeconnections:UseConnection", "codestar-connections:UseConnection"],
                R("ConnectionArn"),
                Condition={
                    "StringEqualsIfExists": {
                        "codeconnections:FullRepositoryId": R("RepositoryId"),
                        "codeconnections:BranchName": R("Branch"),
                        "codeconnections:ProviderPermissionsRequired": "read_only",
                        "codeconnections:ProviderAction": [
                            "GitPull",
                            "GetBranch",
                            "GetCommit",
                            "GetRepository",
                            "StartUploadArchiveToS3",
                            "GetUploadArchiveToS3Status",
                            "GetFile",
                            "GetFolder",
                            "IsRepositoryEmpty",
                            "ListBranches",
                            "ListBranchCommits",
                            "ListCommitFiles",
                            "ListCommitStatuses",
                            "ListRepositories",
                            "ListOwners",
                            "GenerateReferenceLink",
                        ],
                    },
                },
            ),
            statement(["codeconnections:GetConnection"], R("ConnectionArn")),
            statement(["codebuild:StartBuild", "codebuild:BatchGetBuilds"], A("Build", "Arn")),
            statement(
                [
                    "ec2:DescribeInstances",
                    "elasticloadbalancing:DescribeTargetGroupAttributes",
                    "elasticloadbalancing:DescribeTargetGroups",
                    "elasticloadbalancing:DescribeTargetHealth",
                    "ssm:CancelCommand",
                    "ssm:DescribeInstanceInformation",
                    "ssm:ListCommandInvocations",
                ],
                "*",
            ),
            statement(
                ["elasticloadbalancing:DeregisterTargets", "elasticloadbalancing:RegisterTargets"],
                R("Targets"),
            ),
            statement(
                ["ssm:SendCommand"],
                S("arn:${AWS::Partition}:ec2:${AWS::Region}:${AWS::AccountId}:instance/*"),
                Condition={
                    "StringEquals": {"aws:ResourceTag/DeploymentStack": R("AWS::StackName")}
                },
            ),
            statement(
                ["ssm:SendCommand"],
                S("arn:${AWS::Partition}:ssm:${AWS::Region}::document/AWS-RunShellScript"),
            ),
            statement(
                ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
                A("PipelineLogs", "Arn"),
            ),
        ],
    )
    resource(
        t,
        "Pipeline",
        "CodePipeline::Pipeline",
        {
            "Name": S("${AWS::StackName}-pipeline"),
            "RoleArn": A("PipelineRole", "Arn"),
            "PipelineType": "V2",
            "ExecutionMode": "QUEUED",
            "ArtifactStore": {
                "Type": "S3",
                "Location": R("ArtifactBucket"),
                "EncryptionKey": {"Type": "KMS", "Id": R("DataKeyArn")},
            },
            "Stages": [
                {
                    "Name": "Source",
                    "Actions": [
                        {
                            "Name": "GitHub",
                            "ActionTypeId": {
                                "Category": "Source",
                                "Owner": "AWS",
                                "Provider": "CodeStarSourceConnection",
                                "Version": "1",
                            },
                            "Configuration": {
                                "ConnectionArn": R("ConnectionArn"),
                                "FullRepositoryId": R("RepositoryId"),
                                "BranchName": R("Branch"),
                                "DetectChanges": "true",
                                "OutputArtifactFormat": "CODE_ZIP",
                            },
                            "OutputArtifacts": [{"Name": "Source"}],
                        }
                    ],
                },
                {
                    "Name": "BuildAndTest",
                    "Actions": [
                        {
                            "Name": "Containers",
                            "ActionTypeId": {
                                "Category": "Build",
                                "Owner": "AWS",
                                "Provider": "CodeBuild",
                                "Version": "1",
                            },
                            "Configuration": {"ProjectName": R("Build")},
                            "InputArtifacts": [{"Name": "Source"}],
                            "OutputArtifacts": [{"Name": "Release"}],
                        }
                    ],
                },
                {
                    "Name": "Deploy",
                    "Actions": [
                        {
                            "Name": "EC2",
                            "ActionTypeId": {
                                "Category": "Deploy",
                                "Owner": "AWS",
                                "Provider": "EC2",
                                "Version": "1",
                            },
                            "Configuration": {
                                "InstanceTagKey": "DeploymentStack",
                                "InstanceTagValue": R("AWS::StackName"),
                                "InstanceType": "EC2",
                                "TargetDirectory": "/opt/tenderlens/incoming",
                                "PostScript": "scripts/deploy.sh",
                                "TargetGroupNameList": A("Targets", "TargetGroupName"),
                                "MaxBatch": "1",
                                "MaxError": "0",
                            },
                            "InputArtifacts": [{"Name": "Release"}],
                        }
                    ],
                },
            ],
        },
        "Every main-branch push runs quality gates before an ordered deployment",
        ["QUEUED mode prevents overlapping migrations and releases"],
    )
    output(
        t,
        "WebsiteUrl",
        S("https://${Distribution.DomainName}"),
        "Actual AWS-provisioned HTTPS website URL",
    )
    t["Outputs"]["WebsiteUrl"]["Condition"] = "PublicEdge"
    output(
        t,
        "PublicEdgeEnabled",
        R("EnablePublicEdge"),
        "Public HTTPS requires CloudFront account verification",
    )
    output(t, "PipelineName", R("Pipeline"), "Pipeline for main-branch deployments")
    output(t, "HostRoleArn", A("HostRole", "Arn"), "Runtime IAM role")
    output(t, "AutoScalingGroup", R("Hosts"), "Replaceable application hosts")
    return t


def split_storage(full):
    """Keep retained storage managed separately from replaceable network setup."""
    storage = template(
        "TenderLens retained storage - encrypted buckets, images, keys and provider configuration",
        {
            "DatabaseIdentifier": full["Parameters"]["DatabaseIdentifier"],
        },
    )
    names = [
        "DataKey",
        "EvidenceBucket",
        "EvidenceBucketTLS",
        "ArtifactBucket",
        "ArtifactBucketTLS",
        "BackendRepository",
        "FrontendRepository",
        "IntegrationSecret",
        "DatabaseLogs",
    ]
    for name in names:
        storage["Resources"][name] = full["Resources"].pop(name)
    storage["Resources"]["DatabaseLogs"]["Properties"]["LogGroupName"] = S(
        "/aws/rds/instance/${DatabaseIdentifier}/postgresql"
    )
    for name in [
        "EvidenceBucket",
        "ArtifactBucket",
        "IntegrationSecret",
        "DataKeyArn",
        "BackendRepositoryUri",
        "FrontendRepositoryUri",
        "BackendRepositoryArn",
        "FrontendRepositoryArn",
    ]:
        storage["Outputs"][name] = full["Outputs"].pop(name)
        full["Parameters"][name] = {"Type": "String", "MinLength": 1}
        output(full, name, R(name), "Storage-stack value for service deployment")
    full["Resources"]["Database"].pop("DependsOn", None)

    def replace(value):
        if value == A("DataKey", "Arn"):
            return R("DataKeyArn")
        if isinstance(value, dict):
            return {key: replace(child) for key, child in value.items()}
        if isinstance(value, list):
            return [replace(child) for child in value]
        return value

    full = replace(full)
    full["Description"] = (
        "TenderLens private PostgreSQL and network - demo defaults fit the AWS Free plan; production mode adds resilience"
    )
    return storage, full


if __name__ == "__main__":
    storage, database = split_storage(data())
    for name, body in [("storage", storage), ("data", database), ("service", service())]:
        destination = ROOT / "templates" / f"{name}.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(body, indent=2) + "\n")
        print(
            f"{destination.name}: {len(body['Resources'])} resources, {destination.stat().st_size} bytes"
        )
