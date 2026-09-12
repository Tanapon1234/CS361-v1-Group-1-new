# V2 AWS Foundation Evidence Template

ใช้ไฟล์นี้เป็น checklist ตอนปิด Issue #48

ห้ามแนบ secret value หรือ credential

---

## Evidence Summary

| Requirement | Evidence | Status |
|---|---|---|
| Aurora PostgreSQL Serverless v2 cluster exists | `cs361-v2-dev-aurora`, created with Aurora Express Configuration | Done |
| Region is `ap-southeast-1` | CloudFormation outputs / RDS metadata | Done |
| Data API enabled | `HttpEndpointEnabled=true` | Done |
| Secrets Manager secret exists | `cs361-v2/dev/aurora/master`, value not shown | Done |
| Query role exists | `CS361V2QueryLambdaRole-dev` | Done |
| Admin role exists | `CS361V2AdminLambdaRole-dev` | Done |
| Import role exists | `CS361V2ImportLambdaRole-dev` | Done |
| Projection role exists | `CS361V2ProjectionLambdaRole-dev` | Done |
| No broad runtime permissions | IAM inline policies use scoped cluster, secret, and S3 prefix ARNs | Done |
| CloudWatch log baseline exists | `/aws/lambda/cs361-v2-dev-*` log groups from stack | Done |
| `SELECT 1` through Data API succeeds | verification script returned `1` | Done |
| Resource names / ARNs documented | `docs/v2/aws-foundation.md` | Done |

Dev/free-plan caveat:

- This account required Aurora Express Configuration.
- CloudFormation cannot currently set `WithExpressConfiguration` for `AWS::RDS::DBCluster` in this account/region schema.
- The deployed cluster reports `VPCNetworkingEnabled=false` and `InternetAccessGatewayEnabled=true`; use this deployment as dev/demo evidence, not as production private-network posture.

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

Observed verification result:

```text
Running SELECT 1 through RDS Data API...
1

Running identity checks through RDS Data API...
current_database = cs361v2
current_user = postgres
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
