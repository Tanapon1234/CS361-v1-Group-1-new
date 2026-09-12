# CS361 V2 AWS Foundation

This folder contains the CloudFormation baseline for Issue #48.

It prepares:

- Aurora PostgreSQL Serverless v2 cluster
- RDS Data API via `EnableHttpEndpoint`
- RDS-managed master secret in AWS Secrets Manager for standard mode
- private DB subnet group and security group with no inbound public access for standard mode
- S3 data bucket with public access blocked
- Lambda runtime IAM roles for query, admin, import, and projection responsibilities
- Aurora PostgreSQL log export and CloudWatch log group naming baseline

The template also supports `AuroraProvisioningMode=external-express` for AWS accounts that require Aurora Express Configuration. In that mode, create the Aurora cluster and secret first, then let CloudFormation create IAM/S3/CloudWatch resources against the supplied cluster and secret ARNs.

## Files

| File | Purpose |
|---|---|
| `aws-foundation.yaml` | CloudFormation template for V2 AWS foundation |
| `parameters.dev.example.json` | Example parameter file; copy before filling real VPC/subnet values |

## Before Deploying

Do not paste AWS access keys or secret values into chat, GitHub, or committed files.

Required local tools:

- AWS CLI v2
- AWS credentials configured locally through `aws configure sso`, `aws configure`, or an approved team profile

Required AWS inputs:

- region: `ap-southeast-1`
- VPC ID
- at least two private subnet IDs in different Availability Zones
- selected Aurora PostgreSQL engine version available for `db.serverless`

Check available Aurora PostgreSQL Serverless v2 engine versions:

```bash
aws rds describe-orderable-db-instance-options \
  --region ap-southeast-1 \
  --engine aurora-postgresql \
  --db-instance-class db.serverless \
  --query 'OrderableDBInstanceOptions[].EngineVersion' \
  --output text
```

## Deploy

Copy the example parameter file if you want a record of the chosen values:

```bash
cp infra/v2/parameters.dev.example.json infra/v2/parameters.dev.local.json
```

Deploy:

```bash
aws cloudformation deploy \
  --region ap-southeast-1 \
  --stack-name cs361-v2-aws-foundation-dev \
  --template-file infra/v2/aws-foundation.yaml \
  --parameter-overrides \
    ProjectName=cs361-v2 \
    Environment=dev \
    VpcId=<vpc-id> \
    PrivateSubnetIds=<subnet-a>,<subnet-b> \
    DBName=cs361v2 \
    DBMasterUsername=cs361v2admin \
    DBEngineVersion=<aurora-postgresql-version> \
    MinCapacity=0.5 \
    MaxCapacity=2 \
    SecondsUntilAutoPause=600 \
    LogRetentionDays=14 \
  --capabilities CAPABILITY_NAMED_IAM
```

For AWS free-plan accounts that fail with `WithExpressConfiguration`, use external Express mode:

```bash
aws rds create-db-cluster \
  --region ap-southeast-1 \
  --db-cluster-identifier cs361-v2-dev-aurora \
  --engine aurora-postgresql \
  --with-express-configuration \
  --tags Key=Project,Value=cs361-v2 Key=Environment,Value=dev

aws rds enable-http-endpoint \
  --region ap-southeast-1 \
  --resource-arn <DBClusterArn>
```

Then create a Secrets Manager secret for the database username/password without printing or committing the password value, create database `cs361v2`, and deploy:

```bash
aws cloudformation deploy \
  --region ap-southeast-1 \
  --stack-name cs361-v2-aws-foundation-dev \
  --template-file infra/v2/aws-foundation.yaml \
  --parameter-overrides \
    ProjectName=cs361-v2 \
    Environment=dev \
    VpcId=<vpc-id> \
    PrivateSubnetIds=<subnet-a>,<subnet-b> \
    AuroraProvisioningMode=external-express \
    ExternalDBClusterIdentifier=cs361-v2-dev-aurora \
    ExternalDBClusterArn=<DBClusterArn> \
    ExternalDBSecretArn=<DBSecretArn> \
    DBName=cs361v2 \
    DBEngineVersion=<observed-engine-version> \
    LogRetentionDays=14 \
  --capabilities CAPABILITY_NAMED_IAM
```

Show stack outputs:

```bash
aws cloudformation describe-stacks \
  --region ap-southeast-1 \
  --stack-name cs361-v2-aws-foundation-dev \
  --query 'Stacks[0].Outputs'
```

## Verify Data API

Export the outputs into environment variables, then run:

```bash
AWS_REGION=ap-southeast-1 \
DB_CLUSTER_ARN=<stack-output-DBClusterArn> \
DB_SECRET_ARN=<stack-output-DBSecretArn> \
DB_NAME=<stack-output-DBName> \
scripts/check-v2-aws-foundation.sh
```

The minimum pass condition for Issue #48 is `SELECT 1` through RDS Data API.

## Cost Notes

- Dev/demo defaults use `MinCapacity=0.5`, `MaxCapacity=2` for broad Aurora PostgreSQL compatibility.
- If the selected engine supports auto-pause, set `MinCapacity=0` and keep `SecondsUntilAutoPause=600`.
- Aurora Express Configuration may choose its own engine version and capacity range; record the observed values in `docs/v2/aws-foundation.md`.
- Storage, snapshots, Secrets Manager, S3, CloudWatch, and minimum ACU usage may still incur costs.
- The template uses snapshot retention on DB replacement/deletion.

## Security Notes

- Frontend must not receive AWS credentials, DB credentials, cluster ARN, or secret ARN.
- Database credential is stored in Secrets Manager; do not retrieve or copy the secret value into docs.
- Runtime roles avoid `AdministratorAccess`, `rds:*`, `s3:*`, and `secretsmanager:*`.
- Public S3 access is blocked at bucket level.
- `external-express` mode is for dev/demo only when the AWS account requires Aurora Express Configuration. Use standard `cloudformation` mode for production private VPC placement.

## AWS References

- https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-rds-dbcluster.html
- https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-properties-rds-dbcluster-serverlessv2scalingconfiguration.html
- https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless-v2-auto-pause.html
