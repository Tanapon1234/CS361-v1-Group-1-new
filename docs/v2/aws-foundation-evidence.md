# V2 AWS Foundation Evidence Template

ใช้ไฟล์นี้เป็น checklist ตอนปิด Issue #48

ห้ามแนบ secret value หรือ credential

---

## Evidence Summary

| Requirement | Evidence | Status |
|---|---|---|
| Aurora PostgreSQL Serverless v2 cluster exists | screenshot / CLI output | Pending |
| Region is `ap-southeast-1` | screenshot / CLI output | Pending |
| Data API enabled | screenshot / CLI output | Pending |
| Secrets Manager secret exists | screenshot / CLI output without value | Pending |
| Query role exists | IAM role screenshot / policy summary | Pending |
| Admin role exists | IAM role screenshot / policy summary | Pending |
| Import role exists | IAM role screenshot / policy summary | Pending |
| Projection role exists | IAM role screenshot / policy summary | Pending |
| No broad runtime permissions | IAM policy review | Pending |
| CloudWatch log baseline exists | log group screenshot / CLI output | Pending |
| `SELECT 1` through Data API succeeds | command output | Pending |
| Resource names / ARNs documented | `docs/v2/aws-foundation.md` | Pending |

---

## Safe CLI Evidence Commands

Describe stack outputs:

```bash
aws cloudformation describe-stacks \
  --region ap-southeast-1 \
  --stack-name cs361-v2-aws-foundation-dev \
  --query 'Stacks[0].Outputs'
```

Verify Data API:

```bash
AWS_REGION=ap-southeast-1 \
DB_CLUSTER_ARN=<DBClusterArn> \
DB_SECRET_ARN=<DBSecretArn> \
DB_NAME=<DBName> \
scripts/check-v2-aws-foundation.sh
```

List IAM role names:

```bash
aws iam list-roles \
  --query "Roles[?starts_with(RoleName, 'CS361V2')].[RoleName,Arn]" \
  --output table
```

Check secret metadata without revealing value:

```bash
aws secretsmanager describe-secret \
  --region ap-southeast-1 \
  --secret-id <DBSecretArn> \
  --query '{Name:Name,ARN:ARN,RotationEnabled:RotationEnabled}'
```
