# AWS Access And Project Setup

ไฟล์นี้อธิบายวิธีเตรียมเครื่องและ AWS access สำหรับทีมที่ต้องพัฒนา V2 ต่อ

## Important Security Rule

ห้ามใส่ค่าเหล่านี้ใน GitHub, docs, screenshot, chat หรือ commit:

- AWS Access Key ID
- AWS Secret Access Key
- AWS session token
- database password
- Secrets Manager secret value
- private S3 object content

สิ่งที่ใส่ใน docs/evidence ได้:

- AWS region
- stack name
- API endpoint
- Lambda name
- CloudWatch log group
- S3 bucket name
- ARN แบบ redacted หรือใช้ placeholder `<account-id>`

ถ้าต้องใส่ ARN จริงใน GitHub issue ให้ระวังว่า ARN ไม่ใช่ password แต่เปิดเผย account id ได้ ควรใช้แบบ redacted เมื่อไม่จำเป็น

## Tools Required

ต้องมี:

- Git
- Node.js/npm สำหรับ frontend
- Python 3 สำหรับ backend Lambda tests/scripts
- AWS CLI v2
- editor เช่น VS Code

เช็ค AWS CLI:

```bash
aws --version
```

ควรเห็นประมาณ:

```text
aws-cli/2.x.x ...
```

## Configure AWS Credentials

ถ้าใช้ IAM user access key:

```bash
aws configure
```

กรอก:

```text
AWS Access Key ID: <ได้จาก IAM user ของตัวเอง>
AWS Secret Access Key: <ได้จาก IAM user ของตัวเอง>
Default region name: ap-southeast-1
Default output format: json
```

ถ้าใช้ SSO:

```bash
aws configure sso
```

เช็คว่า login ใช้ได้:

```bash
aws sts get-caller-identity
```

ควรเห็น account/ARN ของตัวเอง เช่น:

```text
arn:aws:iam::<account-id>:user/<your-user>
```

ถ้าเจอ `ExpiredToken`:

1. credential/session หมดอายุ
2. รัน `aws configure` ใหม่ หรือ login SSO ใหม่
3. เช็ค `aws configure list`

## IAM Permissions Needed

สำหรับคนที่ทำแค่ดู/รีวิว:

- CloudFormation read-only
- RDS read-only
- CloudWatch read-only
- S3 read-only เฉพาะ bucket ที่เกี่ยวข้อง
- IAM read-only

สำหรับคนทำ backend/Lambda/API:

- Lambda full/manage permission เฉพาะ project
- API Gateway manage permission
- CloudFormation deploy permission
- S3 put/get สำหรับ artifact bucket
- CloudWatch logs permission
- `iam:PassRole` สำหรับ role ที่ใช้ deploy Lambda
- `rds-data:ExecuteStatement`
- `secretsmanager:GetSecretValue` เฉพาะ DB secret

สำหรับคนทำ admin/migration:

- เพิ่ม `rds-data:BeginTransaction`
- `rds-data:CommitTransaction`
- `rds-data:RollbackTransaction`
- S3 landing/archive/metadata permissions ตาม scope

อย่าใช้ root account ถ้าไม่จำเป็น

## Current AWS Resources

Region:

```text
ap-southeast-1
```

Foundation stack:

```text
cs361-v2-aws-foundation-dev
```

Master Data API stack:

```text
cs361-v2-master-data-api-dev
```

Master Data API endpoint:

```text
https://n89gqgnqw2.execute-api.ap-southeast-1.amazonaws.com
```

Core resource names:

| Resource | Name |
|---|---|
| Aurora cluster | `cs361-v2-dev-aurora` |
| Database | `cs361v2` |
| Secret name | `cs361-v2/dev/aurora/master` |
| S3 data bucket | `cs361-v2-aws-foundation-dev-v2databucket-itl5uq2sozge` |
| Query Lambda role | `CS361V2QueryLambdaRole-dev` |
| Admin Lambda role | `CS361V2AdminLambdaRole-dev` |
| Import Lambda role | `CS361V2ImportLambdaRole-dev` |
| Projection Lambda role | `CS361V2ProjectionLambdaRole-dev` |
| Query Lambda | `cs361-v2-dev-query` |
| Query log group | `/aws/lambda/cs361-v2-dev-query` |

## How To Get Stack Outputs

Foundation outputs:

```bash
aws cloudformation describe-stacks \
  --region ap-southeast-1 \
  --stack-name cs361-v2-aws-foundation-dev \
  --query 'Stacks[0].Outputs'
```

Master Data API outputs:

```bash
aws cloudformation describe-stacks \
  --region ap-southeast-1 \
  --stack-name cs361-v2-master-data-api-dev \
  --query 'Stacks[0].Outputs'
```

Useful outputs:

- `DBClusterArn`
- `DBSecretArn`
- `DBName`
- `DataBucketName`
- `QueryLambdaRoleArn`
- `AdminLambdaRoleArn`
- `MasterDataApiEndpoint`
- `QueryLambdaName`
- `QueryLogGroupName`

## How To See Database Data

V2 does not require opening a public DB port. Use RDS Data API:

```bash
DB_CLUSTER_ARN=$(aws cloudformation describe-stacks \
  --region ap-southeast-1 \
  --stack-name cs361-v2-aws-foundation-dev \
  --query "Stacks[0].Outputs[?OutputKey=='DBClusterArn'].OutputValue | [0]" \
  --output text)

DB_SECRET_ARN=$(aws cloudformation describe-stacks \
  --region ap-southeast-1 \
  --stack-name cs361-v2-aws-foundation-dev \
  --query "Stacks[0].Outputs[?OutputKey=='DBSecretArn'].OutputValue | [0]" \
  --output text)

DB_NAME=$(aws cloudformation describe-stacks \
  --region ap-southeast-1 \
  --stack-name cs361-v2-aws-foundation-dev \
  --query "Stacks[0].Outputs[?OutputKey=='DBName'].OutputValue | [0]" \
  --output text)
```

Then:

```bash
aws rds-data execute-statement \
  --region ap-southeast-1 \
  --resource-arn "$DB_CLUSTER_ARN" \
  --secret-arn "$DB_SECRET_ARN" \
  --database "$DB_NAME" \
  --sql "select id, public_slug, name_th from faculty order by public_slug"
```

ถ้าอยากใช้ GUI/database client:

- ปกติ Aurora Serverless Data API ไม่ใช่การเปิด TCP database port ให้ client ต่อโดยตรง
- ให้ใช้ AWS Console RDS Query Editor/Data API ถ้า account/region รองรับ
- ถ้าจะใช้ client แบบ DBeaver/TablePlus ต้องมี endpoint/network/credential path ที่ปลอดภัย ซึ่ง project นี้ยังไม่ได้ออกแบบเป็น default
- สำหรับทีมนี้ แนะนำใช้ RDS Data API ผ่าน AWS CLI หรือเขียน script เฉพาะงาน

## How To Deploy Master Data API Again

ถ้าแก้ Lambda #64 แล้วต้อง deploy ใหม่:

```bash
AWS_REGION=ap-southeast-1 \
FOUNDATION_STACK=cs361-v2-aws-foundation-dev \
API_STACK=cs361-v2-master-data-api-dev \
scripts/deploy-v2-master-data-api.sh
```

script จะ:

1. compile Python handler
2. zip Lambda artifact
3. upload ไป S3 artifact path
4. deploy `infra/v2/master-data-api.yaml`
5. print stack outputs

## How To Smoke Test Master Data API

```bash
AWS_REGION=ap-southeast-1 \
API_STACK=cs361-v2-master-data-api-dev \
scripts/smoke-v2-master-data-api.sh
```

Expected:

```text
PASS /api/v2/academic-periods count=5
PASS /api/v2/evaluation-periods count=3
PASS /api/v2/work-categories count=6
PASS /api/v2/work-types count=26
PASS /api/v2/faculties count=3
PASS /api/v2/work-types?category=UNKNOWN returned 400 INVALID_QUERY
```

If the first run returns 500 after the DB has been idle:

- likely Aurora is resuming from auto-pause
- wait 15-30 seconds
- run the smoke test again
- if still failing, open CloudWatch log group `/aws/lambda/cs361-v2-dev-query`

## Where To Check Each Service In AWS Console

### CloudFormation

Use CloudFormation to see stack status and outputs:

- `cs361-v2-aws-foundation-dev`
- `cs361-v2-master-data-api-dev`

Check:

- stack status is `CREATE_COMPLETE` or `UPDATE_COMPLETE`
- Outputs tab has API endpoint, DB ARN, role ARN, bucket name
- Events tab shows deploy failures if any

### API Gateway

Find API:

```text
cs361-v2-dev-master-data-api
```

Check:

- routes include all `GET /api/v2/...`
- integration points to Lambda `cs361-v2-dev-query`
- endpoint matches stack output

### Lambda

Find function:

```text
cs361-v2-dev-query
```

Check:

- runtime `python3.12`
- handler `master_data.handler`
- environment variables: `DB_CLUSTER_ARN`, `DB_SECRET_ARN`, `DB_NAME`
- role: `CS361V2QueryLambdaRole-dev`
- monitor/logs tab links to CloudWatch

Do not copy secret values. Env var `DB_SECRET_ARN` is an ARN, not the secret value.

### RDS / Aurora

Find cluster:

```text
cs361-v2-dev-aurora
```

Check:

- Data API / HTTP endpoint enabled
- cluster can auto-pause/resume
- engine is Aurora PostgreSQL

### Secrets Manager

Find secret:

```text
cs361-v2/dev/aurora/master
```

Use only ARN/name in docs. Do not reveal secret value.

### S3

Find data/artifact bucket:

```text
cs361-v2-aws-foundation-dev-v2databucket-itl5uq2sozge
```

Used for:

- data landing/archive/metadata
- Lambda artifact upload path
- future projection/export paths

### CloudWatch

Important log groups:

```text
/aws/lambda/cs361-v2-dev-query
/aws/lambda/cs361-v2-dev-admin
/aws/lambda/cs361-v2-dev-import
/aws/lambda/cs361-v2-dev-projection
```

For #64, check `/aws/lambda/cs361-v2-dev-query`.

## Local Project Setup

Clone/pull repo:

```bash
git clone <repo-url>
cd CS361-v1-Group-1
```

Install frontend dependencies:

```bash
cd frontend
npm install
```

Run local frontend tests:

```bash
npm run test:v2:master-data
```

Run backend tests from repo root:

```bash
python3 -m unittest backend.v2.query.test_master_data
```

Run Python compile check:

```bash
PYTHONPYCACHEPREFIX=/tmp/codex-pycache \
python3 -m compileall -q backend/v2/query
```

## Common Problems

### `ExpiredToken`

Credential/session expired.

Fix:

```bash
aws configure
aws sts get-caller-identity
```

or login through SSO again.

### `DatabaseResumingException`

Aurora auto-paused.

Fix:

```bash
sleep 20
scripts/smoke-v2-master-data-api.sh
```

### `AccessDenied` on deploy

Likely missing one of:

- CloudFormation permission
- S3 put/get for artifact bucket
- Lambda permission
- API Gateway permission
- `iam:PassRole` for Lambda role
- RDS Data API permission
- Secrets Manager read permission

### `No policy was attached`

IAM user may already have 10 managed policies attached. AWS IAM has a managed policy attachment limit per identity. Prefer a project-specific group/role/policy rather than piling many broad policies onto one user.
