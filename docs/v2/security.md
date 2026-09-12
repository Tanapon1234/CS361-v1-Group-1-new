# V2 Security Notes

เอกสารนี้สรุป security boundary สำหรับ Issue #48

---

## Secret Handling

- Standard CloudFormation mode: database password is managed by RDS and stored in AWS Secrets Manager.
- Dev/free-plan `external-express` mode: Aurora Express Configuration does not allow `ManageMasterUserPassword` during create, so a random master password was generated locally without printing it, applied to the cluster, and stored in AWS Secrets Manager.
- Secret value must not be copied into docs, `.env`, screenshots, GitHub comments, or frontend config.
- It is acceptable to record the secret ARN as an internal backend/runtime reference.
- `DB_SECRET_ARN` must not be exposed to browser-side code.

---

## IAM Role Boundary

Runtime roles are separated by responsibility:

| Role | Allowed baseline |
|---|---|
| Query Lambda role | `rds-data:ExecuteStatement`, `secretsmanager:GetSecretValue` |
| Admin Lambda role | Data API execute and transaction actions, `secretsmanager:GetSecretValue` |
| Import Lambda role | Data API transaction actions, read `landing/*`, write `archive/*` and `metadata/*` |
| Projection Lambda role | Data API read, write `public-serving/*` |

Runtime roles must not use:

- `AdministratorAccess`
- `rds:*`
- `s3:*`
- `secretsmanager:*`
- broad unrelated resource ARNs

---

## Network Boundary

- Standard CloudFormation mode places Aurora in the selected VPC/subnets and creates a DB security group with no inbound public access.
- The deployed dev/free-plan `external-express` cluster reports `VPCNetworkingEnabled=false` and `InternetAccessGatewayEnabled=true`; this is a documented AWS account-plan limitation, not the intended production network model.
- Backend access should still use RDS Data API and Secrets Manager, not direct browser/database access.
- Browser/frontend must not call Aurora, Secrets Manager, or S3 private resources directly.

Production/security follow-up:

- Use a standard AWS account plan that allows CloudFormation-managed Aurora creation.
- Redeploy in `cloudformation` mode with private subnet placement and DB security group control.
- Treat the current Express deployment as dev/demo evidence only.

---

## Evidence Rules

Allowed evidence:

- CloudFormation stack output without secret values
- Aurora cluster page showing Data API enabled
- Secrets Manager page showing secret name/ARN only
- IAM policy summary
- `SELECT 1` command output through RDS Data API

Forbidden evidence:

- database password
- access key / secret access key
- session token
- full JWT
- screenshots showing secret value
