# V2 Security Notes

เอกสารนี้สรุป security boundary สำหรับ Issue #48

---

## Secret Handling

- Database password is managed by RDS and stored in AWS Secrets Manager.
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

- Aurora is placed in private subnets.
- The DB security group has no inbound public access.
- Lambda accesses Aurora through RDS Data API, not direct public DB networking.
- Browser/frontend must not call Aurora, Secrets Manager, or S3 private resources directly.

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
