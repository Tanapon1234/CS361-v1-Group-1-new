# V2 AWS Foundation Evidence

เก็บหลักฐานสำหรับ Issue #48 หลัง deploy AWS จริง

Allowed:

- sanitized CloudFormation outputs
- Aurora cluster screenshot without credentials
- Data API enabled screenshot
- Secrets Manager metadata screenshot without secret value
- IAM policy summary
- `SELECT 1` Data API command output

Forbidden:

- database password
- AWS access key / secret access key
- session token
- raw Secrets Manager value
- full JWT/token
