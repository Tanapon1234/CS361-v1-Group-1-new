# V2 AWS Foundation

เอกสารนี้เป็น working record สำหรับ Issue #48 - Provision Aurora, Data API, Secrets & IAM Foundation

สถานะปัจจุบัน: **Prepared for AWS deployment**

ยังไม่ถือว่าปิดการ์ดจนกว่าจะ deploy AWS จริงและมีหลักฐาน `SELECT 1` ผ่าน RDS Data API

---

## Target Region

| Field | Value |
|---|---|
| AWS Region | `ap-southeast-1` |
| Environment | `dev` หรือ `demo` |
| Stack Name | `cs361-v2-aws-foundation-dev` |
| IaC Template | `infra/v2/aws-foundation.yaml` |

---

## Prepared AWS Resources

CloudFormation template เตรียม resource ต่อไปนี้:

| Resource | Purpose |
|---|---|
| Aurora PostgreSQL Serverless v2 cluster | V2 repository database |
| Aurora writer instance class `db.serverless` | Serverless v2 runtime instance |
| RDS Data API / HTTP endpoint | SQL access from Lambda via AWS SDK |
| RDS-managed Secrets Manager secret | Database credential storage |
| DB subnet group | Private subnet placement |
| DB security group | No inbound public DB access |
| S3 data bucket | source landing, archive, metadata, public projection |
| Query Lambda role | read/query API access |
| Admin Lambda role | create/edit/soft-delete API access |
| Import Lambda role | controlled import access |
| Projection Lambda role | public projection writer |
| Aurora PostgreSQL log export | database log visibility in CloudWatch |
| CloudWatch log groups | runtime log naming baseline |

---

## Resource Naming

Default names from the template:

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

Fill this after deployment:

| Field | Value |
|---|---|
| Deployed date | TBD |
| AWS account alias/id | TBD |
| Stack name | TBD |
| Cluster identifier | TBD |
| Cluster ARN | TBD |
| Database name | TBD |
| Secret name | TBD |
| Secret ARN | TBD |
| Data bucket name | TBD |
| Query role ARN | TBD |
| Admin role ARN | TBD |
| Import role ARN | TBD |
| Projection role ARN | TBD |
| Data API verification result | TBD |

---

## Cost / Risk Notes

- Dev/demo default uses `MinCapacity=0.5` and `MaxCapacity=2` for broad Aurora PostgreSQL compatibility.
- If the selected engine version supports Aurora Serverless v2 auto-pause, use `MinCapacity=0` and keep `SecondsUntilAutoPause=600`.
- Auto-pause can reduce compute cost but may add cold resume latency.
- Storage, snapshots, Secrets Manager, S3, and CloudWatch may still incur cost.
- The template uses `DeletionPolicy: Snapshot` for the DB cluster to avoid accidental data loss.
- Do not keep dev/demo stacks running if they are no longer needed.

---

## Current Blockers

- AWS CLI is not installed on the local machine yet.
- AWS account login/profile is not configured in this workspace yet.
- Real VPC/private subnet IDs still need to be selected.
- Live AWS resources and `SELECT 1` evidence are still pending.

---

## AWS References

- AWS CloudFormation `AWS::RDS::DBCluster` supports `EnableHttpEndpoint` for the RDS Data API.
- AWS CloudFormation `ServerlessV2ScalingConfiguration` supports `MinCapacity`, `MaxCapacity`, and `SecondsUntilAutoPause`.
- Aurora Serverless v2 auto-pause uses `MinCapacity=0` on engine versions that support scaling to zero ACUs.

Reference links:

- https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-rds-dbcluster.html
- https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-properties-rds-dbcluster-serverlessv2scalingconfiguration.html
- https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless-v2-auto-pause.html
