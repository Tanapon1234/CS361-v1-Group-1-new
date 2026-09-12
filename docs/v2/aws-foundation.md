# V2 AWS Foundation

เอกสารนี้เป็น working record สำหรับ Issue #48 - Provision Aurora, Data API, Secrets & IAM Foundation

สถานะปัจจุบัน: **Deployed for dev/demo**

Deploy จริงแล้วบน AWS account dev และมีหลักฐาน `SELECT 1` ผ่าน RDS Data API

หมายเหตุ: account นี้ถูก RDS บังคับให้ใช้ Aurora Express Configuration สำหรับ Aurora cluster บน free-plan account ดังนั้น Aurora cluster ถูกสร้างด้วย AWS CLI แล้ว CloudFormation stack ใช้ `AuroraProvisioningMode=external-express` เพื่อสร้าง S3, IAM roles และ CloudWatch log groups โดยอ้าง cluster/secret ที่มีอยู่

---

## Target Region

| Field | Value |
|---|---|
| AWS Region | `ap-southeast-1` |
| Environment | `dev` หรือ `demo` |
| Stack Name | `cs361-v2-aws-foundation-dev` |
| IaC Template | `infra/v2/aws-foundation.yaml` |
| Aurora provisioning mode | `external-express` |

---

## Prepared AWS Resources

Resource ที่เตรียมจริง:

| Resource | Purpose |
|---|---|
| Aurora PostgreSQL Serverless v2 cluster | V2 repository database, created with AWS CLI Express Configuration |
| Aurora writer instance | Created automatically by Express Configuration |
| RDS Data API / HTTP endpoint | SQL access from Lambda via AWS SDK |
| Secrets Manager secret | Database credential storage, created separately because Express Configuration does not support RDS-managed master password on create |
| DB subnet group | Standard CloudFormation mode only |
| DB security group | Standard CloudFormation mode only |
| S3 data bucket | source landing, archive, metadata, public projection |
| Query Lambda role | read/query API access |
| Admin Lambda role | create/edit/soft-delete API access |
| Import Lambda role | controlled import access |
| Projection Lambda role | public projection writer |
| Aurora PostgreSQL log export | database log visibility in CloudWatch |
| CloudWatch log groups | runtime log naming baseline |

---

## Resource Naming

Default/current names:

| Item | Name Pattern |
|---|---|
| DB cluster | `cs361-v2-dev-aurora` |
| DB writer | `cs361-v2-dev-aurora-writer` |
| Query role | `CS361V2QueryLambdaRole-dev` |
| Admin role | `CS361V2AdminLambdaRole-dev` |
| Import role | `CS361V2ImportLambdaRole-dev` |
| Projection role | `CS361V2ProjectionLambdaRole-dev` |
| Query log group | `/aws/lambda/cs361-v2-dev-query` |
| Admin log group | `/aws/lambda/cs361-v2-dev-admin` |
| Import log group | `/aws/lambda/cs361-v2-dev-import` |
| Projection log group | `/aws/lambda/cs361-v2-dev-projection` |

---

## Deployment Inputs Needed

ก่อน deploy ต้องรู้ค่าเหล่านี้จาก AWS account:

| Input | Secret? | Example |
|---|---:|---|
| AWS profile / login method | no | `aws configure sso` profile |
| VPC ID | no | `vpc-xxxxxxxxxxxxxxxxx` |
| Private subnet IDs | no | `subnet-aaa,subnet-bbb` |
| Aurora PostgreSQL engine version | no | `16.6` |

ห้ามส่งหรือ commit:

- AWS access key
- AWS secret access key
- database password
- Secrets Manager secret value
- session token

---

## Deployment Command

Copy and edit the parameter file:

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

For free-plan accounts that require Aurora Express Configuration, create the Aurora cluster with AWS CLI first, then deploy the stack with `AuroraProvisioningMode=external-express`.

Observed dev command shape:

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

Then create/update the Secrets Manager secret without exposing the password value, create database `cs361v2`, and deploy:

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

---

## Verification Command

After deployment, get stack outputs:

```bash
aws cloudformation describe-stacks \
  --region ap-southeast-1 \
  --stack-name cs361-v2-aws-foundation-dev \
  --query 'Stacks[0].Outputs'
```

Then verify Data API:

```bash
AWS_REGION=ap-southeast-1 \
DB_CLUSTER_ARN=<DBClusterArn> \
DB_SECRET_ARN=<DBSecretArn> \
DB_NAME=<DBName> \
scripts/check-v2-aws-foundation.sh
```

Minimum expected result:

```text
1
```

---

## Live Resource Record

Public docs redact the AWS account ID. Use CloudFormation stack outputs locally for exact ARNs.

| Field | Value |
|---|---|
| Deployed date | 2026-09-12 |
| AWS account alias/id | `33417799****` |
| Stack name | `cs361-v2-aws-foundation-dev` |
| Cluster identifier | `cs361-v2-dev-aurora` |
| Cluster ARN | `arn:aws:rds:ap-southeast-1:<account-id>:cluster:cs361-v2-dev-aurora` |
| Database name | `cs361v2` |
| Secret name | `cs361-v2/dev/aurora/master` |
| Secret ARN | `arn:aws:secretsmanager:ap-southeast-1:<account-id>:secret:cs361-v2/dev/aurora/master-...` |
| Data bucket name | `cs361-v2-aws-foundation-dev-v2databucket-itl5uq2sozge` |
| Query role ARN | `arn:aws:iam::<account-id>:role/CS361V2QueryLambdaRole-dev` |
| Admin role ARN | `arn:aws:iam::<account-id>:role/CS361V2AdminLambdaRole-dev` |
| Import role ARN | `arn:aws:iam::<account-id>:role/CS361V2ImportLambdaRole-dev` |
| Projection role ARN | `arn:aws:iam::<account-id>:role/CS361V2ProjectionLambdaRole-dev` |
| Data API verification result | Passed: `SELECT 1` returned `1` |

Observed Aurora metadata:

| Field | Value |
|---|---|
| Engine version | `17.7` |
| Data API | enabled |
| Serverless v2 capacity | min `0.0`, max `4.0`, auto-pause `300s` |
| Master username | `postgres` |
| IAM database authentication | enabled |
| VPC networking | `false` |
| Internet access gateway | `true` |

---

## Cost / Risk Notes

- Dev/demo default uses `MinCapacity=0.5` and `MaxCapacity=2` for broad Aurora PostgreSQL compatibility.
- If the selected engine version supports Aurora Serverless v2 auto-pause, use `MinCapacity=0` and keep `SecondsUntilAutoPause=600`.
- Auto-pause can reduce compute cost but may add cold resume latency.
- Storage, snapshots, Secrets Manager, S3, and CloudWatch may still incur cost.
- The template uses `DeletionPolicy: Snapshot` for the DB cluster to avoid accidental data loss.
- Do not keep dev/demo stacks running if they are no longer needed.
- Express Configuration selected Aurora PostgreSQL `17.7`, min `0`, max `4`, and auto-pause `300s`.
- Express Configuration on this account reports `VPCNetworkingEnabled=false` and `InternetAccessGatewayEnabled=true`. This is acceptable only as a dev/demo free-plan exception. For production or stricter security review, use a standard account plan and deploy the CloudFormation-managed private VPC mode.

---

## Current Blockers

- None for dev/demo functional verification.
- Production-grade private VPC Aurora placement is deferred until the AWS account can create standard Aurora clusters without the free-plan Express Configuration limitation.

---

## AWS References

- AWS CloudFormation `AWS::RDS::DBCluster` supports `EnableHttpEndpoint` for the RDS Data API.
- AWS CloudFormation `ServerlessV2ScalingConfiguration` supports `MinCapacity`, `MaxCapacity`, and `SecondsUntilAutoPause`.
- Aurora Serverless v2 auto-pause uses `MinCapacity=0` on engine versions that support scaling to zero ACUs.

Reference links:

- https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-rds-dbcluster.html
- https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-properties-rds-dbcluster-serverlessv2scalingconfiguration.html
- https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless-v2-auto-pause.html
