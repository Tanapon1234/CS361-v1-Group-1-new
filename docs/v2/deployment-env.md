# V2 Deployment Environment Variables

เอกสารนี้บันทึก environment variables ที่การ์ด backend, import, projection และ integration ต้องใช้หลัง Issue #48 deploy สำเร็จ

ห้ามใส่ secret value จริงลง repo

---

## Backend / Lambda Runtime

| Variable | Required | Secret? | Source |
|---|---:|---:|---|
| `AWS_REGION` | yes | no | fixed as `ap-southeast-1` |
| `DB_CLUSTER_ARN` | yes | no | CloudFormation output `DBClusterArn` |
| `DB_SECRET_ARN` | yes | sensitive reference | CloudFormation output `DBSecretArn`; do not expose to frontend |
| `DB_NAME` | yes | no | CloudFormation output `DBName` |
| `DATA_BUCKET_NAME` | yes | no | CloudFormation output `DataBucketName` |
| `LOG_LEVEL` | yes | no | `INFO` for dev/demo |
| `ENVIRONMENT` | yes | no | `dev` or `demo` |

Example local operator file, not committed:

```text
AWS_REGION=ap-southeast-1
DB_CLUSTER_ARN=arn:aws:rds:ap-southeast-1:123456789012:cluster:cs361-v2-dev-aurora
DB_SECRET_ARN=arn:aws:secretsmanager:ap-southeast-1:123456789012:secret:rds!cluster-...
DB_NAME=cs361v2
DATA_BUCKET_NAME=cs361-v2-dev-data-example
LOG_LEVEL=INFO
ENVIRONMENT=dev
```

Current dev/demo values, with AWS account ID redacted for public docs:

```text
AWS_REGION=ap-southeast-1
DB_CLUSTER_ARN=arn:aws:rds:ap-southeast-1:<account-id>:cluster:cs361-v2-dev-aurora
DB_SECRET_ARN=arn:aws:secretsmanager:ap-southeast-1:<account-id>:secret:cs361-v2/dev/aurora/master-...
DB_NAME=cs361v2
DATA_BUCKET_NAME=cs361-v2-aws-foundation-dev-v2databucket-itl5uq2sozge
LOG_LEVEL=INFO
ENVIRONMENT=dev
```

---

## FastAPI Backend Lambda (#199)

Set by `infra/v2/backend-api.yaml`; the full list with defaults is in `backend/.env.example`.

| Variable | Value |
|---|---|
| `ENVIRONMENT` | `dev` / `demo` / `prod` |
| `DB_HOST`, `DB_PORT`, `DB_NAME` | Aurora writer endpoint, `5432`, `cs361v2` |
| `DB_SSLMODE` | `require` |
| `DB_SECRET_ARN` | DB secret; user and password are read from it at connect time (no `DB_PASSWORD`) |
| `DB_POOL_SIZE`, `DB_MAX_OVERFLOW` | `1`, `0` (one request per warm Lambda) |
| `DATA_BUCKET_NAME` | foundation output `DataBucketName` |
| `DEV_AUTH_HEADER_ENABLED` | `true` until Cognito is wired; ignored when `ENVIRONMENT=prod` |

---

## Lambda Role Outputs

| Responsibility | CloudFormation Output |
|---|---|
| Query/read API | `QueryLambdaRoleArn` |
| Admin create/edit/soft delete | `AdminLambdaRoleArn` |
| Import pipeline | `ImportLambdaRoleArn` |
| Public projection writer | `ProjectionLambdaRoleArn` |

---

## Future Frontend Variables

Issue #48 does not configure frontend auth/API values yet. These are reserved for later cards:

| Variable | Scope |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | API Gateway public base URL |
| `NEXT_PUBLIC_COGNITO_USER_POOL_ID` | Cognito admin auth, future card |
| `NEXT_PUBLIC_COGNITO_CLIENT_ID` | Cognito admin auth, future card |

Frontend must never receive:

- AWS access key
- AWS secret access key
- database password
- `DB_SECRET_ARN`
- raw Secrets Manager value
