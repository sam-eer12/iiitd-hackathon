# TenderLens on AWS

## Current demo deployment (25 October 2026)

Website: https://6g7ptgvw64vlq4eh45qazt5g7y0ukdov.lambda-url.ap-south-1.on.aws/

The application stack is `tenderlens-live`. `tenderlens-https` supplies a public
Lambda Function URL proxy to its private ALB while CloudFront account verification
is pending. The proxy does not access the database or provider secrets. Browser
mutations still require the existing Firebase identity, and the hostname is in
Firebase's authorized domain list.

The account currently has a CodeBuild queue quota of zero, so this release was
built on the SSM-managed application host and published as immutable ECR images.
The normal release scripts applied migrations, validated readiness and saved the
healthy recovery bundle. `tenderlens-host-build` grants image-publishing access
only to the two project repositories. CodePipeline source retrieval works, but
automatic builds require a nonzero CodeBuild quota.

The key policy now permits the existing Auto Scaling service-linked role to use
the encrypted boot volume and create AWS-resource grants. This fixes the earlier
`InvalidKMSKey.InvalidState` host launch failure without replacing the data key.

Runtime configuration `/etc/tenderlens/runtime.json` includes `publicOrigin`.
The release passes it as `TENDERLENS_PUBLIC_ORIGIN` to Next.js so HTTPS browser
requests are checked against the public origin rather than the internal HTTP hop.
Keep that value and Firebase's authorized hostname aligned when changing URLs.

Optional proxy infrastructure is reproducible with `render_public_proxy.py`
and `templates/public-proxy.json`. The direct-build publishing policy is recorded
in `templates/host-build.json`.

## Original deployment design

The deployment uses the `tenderlens` AWS profile and `ap-south-1` region.

The current Next.js 16 application runs in Docker on EC2 alongside FastAPI and
the durable Python worker. Amplify's [documented native Next.js support](https://docs.aws.amazon.com/amplify/latest/userguide/ssr-amplify-support.html)
covers versions 12–15, so this configuration preserves the application's current
framework and streaming behavior. CloudFront supplies HTTPS through a private VPC
origin and internal ALB. The EC2 public IP is for outbound package/AWS access;
security groups provide no public ingress or SSH.

PostgreSQL storage is Amazon RDS: accounts, supplier profiles and their versions,
verification receipts, discovery jobs, observations, tender versions and evaluations.
Firebase remains the identity provider; the active Firebase Data Connect/Cloud SQL
write has been removed. Saved-list and sidebar preferences remain account-scoped
browser preferences. Public notices fall back to the bundled real-source snapshot
until a newer worker observation exists.

## Free-plan demo settings

The user selected `DeploymentMode=demo`: Single-AZ `db.t4g.micro`, 20 GiB gp3,
one-day automated backups, no storage autoscaling, and Performance Insights off.
The Docker host defaults to `t3.small`; builds use CodeBuild `general1.small`.
These settings consume available AWS credits; they are not a promise of zero cost
or permanent free hosting. The AWS account's Free plan initially reports $100 in
credits and expiry on 24 April 2027. RDS still has encryption, verified TLS,
deletion protection, private subnets, and IAM authentication.

Production mode explicitly enables Multi-AZ, seven-day backups, Performance Insights,
and storage autoscaling up to 100 GiB. It requires an account plan that permits those
features. The current single application host has brief deployment downtime; it is
a demo topology, not a highly available application tier.

## Infrastructure and releases

`render.py` generates three version-controlled CloudFormation templates:

1. `storage.json`: retained KMS key, private/versioned S3 buckets, ECR repositories,
   encrypted database logs, and server-only provider configuration.
2. `data.json`: VPC, subnets, security groups, TLS parameter group, and RDS PostgreSQL.
3. `service.json`: EC2/SSM, internal ALB, CloudFront VPC origin, and CI/CD roles/services
   in the `tenderlens-app` stack.

CodeConnections → CodePipeline V2 (`QUEUED`) → CodeBuild → ECR → native CodePipeline EC2 deployment over SSM.
The `main` branch runs backend lint/migrations/tests/benchmark, frontend quality
checks, production container builds, and web/API/database smoke tests before deploy.
The EC2 deployment action drains traffic, runs database migrations as `tl_migrator`, restarts API,
worker, and Next.js, and validates readiness. A failed health check restores the previous application release and skips older
Alembic migrations during rollback. Healthy releases are archived in S3 so replacement
hosts can recover them. Database migrations are forward-only; write backward-compatible migrations
because application rollback does not reverse schema changes.

Image tags include the source revision and unique build number and are immutable.
Old tagged releases remain available for rollback. The instance role uses `tl_app`
for CRUD; only the migration role owns schema objects. New database connections get
fresh short-lived IAM authentication tokens. The RDS master password is AWS-managed
and only used for initial role setup through the official `asm-exec` resolver.

Generate and check changes:

```sh
uv run python deploy/render.py
uv tool run --from cfn-lint==1.58.0 cfn-lint --format json --regions ap-south-1 --template deploy/templates/storage.json deploy/templates/data.json deploy/templates/service.json
uv run --no-project --with guardpycfn==0.1.0 python deploy/check_guard.py
uv run python deploy/manage.py storage
```

`manage.py` creates a reviewable change set. Add `--apply` to execute it. Apply
storage first, data second, then service with `--connection-arn <available-connection-arn>`.
The data helper queries currently available PostgreSQL 18 releases. CodeConnections
OAuth must be completed in the AWS console once; subsequent main pushes deploy
automatically. The helper never deletes stacks or retrieves secret values. Public hosting defaults
to disabled: after AWS Support verifies the account for CloudFront, apply the service
stack with `--enable-public-edge` to provision its HTTPS endpoint.

During initial deployment, the production RDS attempt was rejected by the Free
account plan. Its network rolled back and no database was created. The retained
storage was imported into `tenderlens-storage` and reused; the failed original
`tenderlens-data` stack remains as an audit record. No pre-existing project data was
deleted or migrated from a local database. The first service stack, `tenderlens-service`,
failed because CodeDeploy requires an unavailable subscription; it has no running host.
A second attempt, `tenderlens-web`, rolled back because AWS requires account verification
for CloudFront distributions. `tenderlens-app` uses the native EC2 action and defaults
to private hosting until that verification is complete.

## Provider setup and operations

Populate the stack's `IntegrationSecret` through AWS Secrets Manager with
`TINYFISH_API_KEY`, and, when available, distinct `SANDBOX_API_KEY` and
`SANDBOX_API_SECRET` values. Empty keys leave live collection/document verification
disabled. Never commit keys, pass them as Docker build arguments, or print resolved
secret values. Runtime uses `{{resolve:secretsmanager:...}}` with the vendored,
unmodified AWS `asm-exec`. See [document-verification.md](../docs/document-verification.md)
for HTTPS callbacks and the required trusted public issuer certificates before
enabling verified document badges.

After CloudFront creates its real hostname, add that hostname to Firebase
Authentication's authorized domains before testing Google sign-in. No custom domain
or ACM certificate is required for the supplied CloudFront HTTPS hostname.

Application/worker/build logs are encrypted in CloudWatch and retained 30 days.
No durable CloudTrail trail existed during setup; AWS management-event history is
limited to 90 days. Configure durable audit retention separately if needed.
RDS/S3/ECR/KMS/secrets are retained on stack removal. Stopping EC2 alone does not
stop RDS or load-balancer credit consumption; teardown needs an explicit retention
and database-backup decision.
