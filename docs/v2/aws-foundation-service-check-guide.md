# V2 AWS Foundation Service Check Guide

เอกสารนี้ใช้สำหรับคนในทีมที่ต้องมาตรวจหรือทำงานต่อจาก Issue #48

ห้ามใส่หรือเปิดเผย secret value, AWS access key, secret access key, session token หรือ database password ใน GitHub comment, screenshot หรือเอกสาร

---

## สรุปสิ่งที่ทำไว้

Issue #48 เตรียม AWS foundation สำหรับ V2 dev/demo แล้ว

สิ่งที่มีแล้ว:

- Aurora PostgreSQL Serverless v2 cluster สำหรับ V2 repository
- RDS Data API เปิดใช้งานแล้ว
- Database ชื่อ `cs361v2`
- Secrets Manager secret สำหรับ database credential
- CloudFormation stack สำหรับ S3, IAM roles และ CloudWatch log groups
- IAM runtime roles แยกตามหน้าที่ Query, Admin, Import และ Projection
- S3 data bucket สำหรับ landing/archive/metadata/public-serving
- CloudWatch log group baseline
- Verification ผ่านแล้วด้วย `SELECT 1` ผ่าน RDS Data API

หมายเหตุ: AWS account นี้บังคับใช้ Aurora Express Configuration สำหรับ Aurora cluster จึงสร้าง Aurora ด้วย AWS CLI แล้วใช้ CloudFormation โหมด `external-express` เพื่อสร้างส่วนประกอบอื่นต่อจาก cluster ที่มีอยู่

---

## Region ที่ต้องใช้

ทุกครั้งที่เปิด AWS Console หรือรัน CLI ให้ใช้ region:

```text
Asia Pacific (Singapore)
ap-southeast-1
```

ถ้าเปิดคนละ region จะหา resource ไม่เจอ

---

## Resource หลักที่ควรรู้

| Resource | Value |
|---|---|
| CloudFormation stack | `cs361-v2-aws-foundation-dev` |
| Aurora cluster | `cs361-v2-dev-aurora` |
| Database name | `cs361v2` |
| Secret name | `cs361-v2/dev/aurora/master` |
| Data bucket | `cs361-v2-aws-foundation-dev-v2databucket-itl5uq2sozge` |
| Query role | `CS361V2QueryLambdaRole-dev` |
| Admin role | `CS361V2AdminLambdaRole-dev` |
| Import role | `CS361V2ImportLambdaRole-dev` |
| Projection role | `CS361V2ProjectionLambdaRole-dev` |

ดู ARN แบบ exact ได้จาก CloudFormation stack outputs

---

## 1. เช็ค CloudFormation

Console:

1. เปิด `CloudFormation`
2. ไปที่ `Stacks`
3. เลือก `cs361-v2-aws-foundation-dev`
4. เช็คสถานะต้องเป็น `CREATE_COMPLETE`
5. เปิดแท็บ `Outputs`

สิ่งที่ควรเห็นใน Outputs:

- `Region`
- `DBClusterIdentifier`
- `DBClusterArn`
- `DBSecretArn`
- `DBName`
- `DataBucketName`
- `QueryLambdaRoleArn`
- `AdminLambdaRoleArn`
- `ImportLambdaRoleArn`
- `ProjectionLambdaRoleArn`
- log group names

CLI:

```bash
aws cloudformation describe-stacks \
  --region ap-southeast-1 \
  --stack-name cs361-v2-aws-foundation-dev \
  --query 'Stacks[0].{Status:StackStatus,Outputs:Outputs}' \
  --output table
```

---

## 2. เช็ค Aurora / RDS

Console:

1. เปิด `RDS`
2. ไปที่ `Databases`
3. เลือก `cs361-v2-dev-aurora`
4. เช็คว่า status เป็น `Available`
5. เช็คว่า engine เป็น Aurora PostgreSQL
6. เช็คว่า Data API / HTTP endpoint enabled

CLI:

```bash
aws rds describe-db-clusters \
  --region ap-southeast-1 \
  --db-cluster-identifier cs361-v2-dev-aurora \
  --query 'DBClusters[0].{Status:Status,EngineVersion:EngineVersion,HttpEndpointEnabled:HttpEndpointEnabled,MasterUsername:MasterUsername,Serverless:ServerlessV2ScalingConfiguration}' \
  --output table
```

ค่าที่ควรเห็น:

- `Status`: `available`
- `HttpEndpointEnabled`: `true`
- `MasterUsername`: `postgres`
- Serverless v2 capacity มี min `0.0`, max `4.0`, auto-pause `300`

หมายเหตุเรื่อง cost:

- `MinCapacity=0` แปลว่า compute pause เองได้เมื่อว่าง
- auto-pause ประมาณ 5 นาที
- ยังอาจมีค่าใช้จ่ายจาก storage, backup, secret, S3 และ CloudWatch

---

## 3. ดู / ทดสอบ Database

วิธีแนะนำคือทดสอบผ่าน RDS Data API ไม่ต้องเปิด database password

จาก repo root:

```bash
AWS_REGION=ap-southeast-1 \
DB_CLUSTER_ARN=<CloudFormation output DBClusterArn> \
DB_SECRET_ARN=<CloudFormation output DBSecretArn> \
DB_NAME=cs361v2 \
scripts/check-v2-aws-foundation.sh
```

ผลที่ถูกต้อง:

```text
Running SELECT 1 through RDS Data API...
1

current_database = cs361v2
current_user = postgres
```

ถ้าต้องการลอง query เอง:

```bash
aws rds-data execute-statement \
  --region ap-southeast-1 \
  --resource-arn <DBClusterArn> \
  --secret-arn <DBSecretArn> \
  --database cs361v2 \
  --sql 'select current_database(), current_user, now();' \
  --output table
```

ดูผ่าน AWS Console:

1. เปิด `RDS`
2. ไปที่ `Query Editor` หรือ `Query Editor v2`
3. เลือก cluster `cs361-v2-dev-aurora`
4. เลือก database `cs361v2`
5. เลือก secret `cs361-v2/dev/aurora/master`
6. รัน:

```sql
select current_database(), current_user, now();
```

ห้ามกดแสดง secret value เพื่อนำไปแปะใน comment หรือ screenshot

---

## 4. เช็ค Secrets Manager

Console:

1. เปิด `Secrets Manager`
2. ค้นหา `cs361-v2/dev/aurora/master`
3. ดูได้เฉพาะ metadata เช่น name, ARN, tags
4. ไม่ต้องกดดู secret value

CLI แบบไม่เปิดเผย value:

```bash
aws secretsmanager describe-secret \
  --region ap-southeast-1 \
  --secret-id cs361-v2/dev/aurora/master \
  --query '{Name:Name,ARN:ARN,RotationEnabled:RotationEnabled,Tags:Tags}' \
  --output table
```

สิ่งที่ควรเห็น:

- secret มีอยู่จริง
- มี tag `Project=cs361-v2`
- ไม่ต้องมี rotation enabled สำหรับ dev/demo ตอนนี้

---

## 5. เช็ค IAM Roles

Console:

1. เปิด `IAM`
2. ไปที่ `Roles`
3. ค้นหา `CS361V2`
4. ควรเจอ 4 roles:

```text
CS361V2QueryLambdaRole-dev
CS361V2AdminLambdaRole-dev
CS361V2ImportLambdaRole-dev
CS361V2ProjectionLambdaRole-dev
```

สิ่งที่ควรเช็ค:

- Trusted entity เป็น `AWS Service: lambda`
- มี managed policy `AWSLambdaBasicExecutionRole`
- มี inline policy เฉพาะหน้าที่
- ไม่มี `AdministratorAccess`
- ไม่มี wildcard กว้างแบบ `rds:*`, `s3:*`, `secretsmanager:*`

CLI:

```bash
aws iam list-roles \
  --query "Roles[?starts_with(RoleName, 'CS361V2')].[RoleName,Arn]" \
  --output table
```

ดู policy ของ Query role:

```bash
aws iam get-role-policy \
  --role-name CS361V2QueryLambdaRole-dev \
  --policy-name cs361-v2-query-data-api \
  --query 'PolicyDocument.Statement[].{Sid:Sid,Action:Action,Resource:Resource}' \
  --output table
```

---

## 6. เช็ค S3 Bucket

Console:

1. เปิด `S3`
2. ค้นหา bucket `cs361-v2-aws-foundation-dev-v2databucket-itl5uq2sozge`
3. เช็คว่า block public access เปิดอยู่
4. เช็คว่า encryption เปิดอยู่
5. เช็คว่า versioning เปิดอยู่

CLI:

```bash
aws s3api get-public-access-block \
  --region ap-southeast-1 \
  --bucket cs361-v2-aws-foundation-dev-v2databucket-itl5uq2sozge
```

```bash
aws s3api get-bucket-versioning \
  --region ap-southeast-1 \
  --bucket cs361-v2-aws-foundation-dev-v2databucket-itl5uq2sozge
```

Prefix ที่ออกแบบไว้:

```text
landing/
archive/
metadata/
public-serving/
```

prefix อาจยังไม่โผล่ถ้ายังไม่มีไฟล์จริง upload เข้าไป

---

## 7. เช็ค CloudWatch Logs

Console:

1. เปิด `CloudWatch`
2. ไปที่ `Logs`
3. เลือก `Log Management`
4. ค้นหา `cs361-v2-dev`

ควรเจอ:

```text
/aws/lambda/cs361-v2-dev-query
/aws/lambda/cs361-v2-dev-admin
/aws/lambda/cs361-v2-dev-import
/aws/lambda/cs361-v2-dev-projection
```

ตอนนี้อาจยังไม่มี log events เพราะยังไม่ได้สร้าง Lambda functions จริง

CLI:

```bash
aws logs describe-log-groups \
  --region ap-southeast-1 \
  --log-group-name-prefix /aws/lambda/cs361-v2-dev \
  --query 'logGroups[].logGroupName' \
  --output table
```

---

## 8. คนอื่นจะทำต่อได้ไหม

ทำต่อได้ ถ้ามีสิ่งเหล่านี้:

- อยู่ใน AWS account เดียวกัน
- IAM user มีสิทธิ์พอสำหรับงานที่ทำ
- ใช้ region `ap-southeast-1`
- มี repo branch ล่าสุดที่รวม commit ของ Issue #48 แล้ว
- ใช้ CloudFormation outputs เป็นแหล่งอ้างอิง ARN/env vars

ไม่ต้องขอ database password จากเจ้าของงาน เพราะ backend/Lambda ควรใช้ Secrets Manager ผ่าน `DB_SECRET_ARN`

---

## 9. สิทธิ์ IAM สำหรับคนในทีม

สำหรับ user ที่ต้องทำงาน V2 ต่อ ตอนนี้ policy set ที่ใช้ได้คือ:

```text
AmazonAPIGatewayAdministrator
AmazonRDSFullAccess
AmazonS3FullAccess
AWSCloudFormationFullAccess
AWSLambda_FullAccess
CloudWatchLogsFullAccess
CS361V1DeveloperPolicy
IAMFullAccess
IAMReadOnlyAccess
SecretsManagerReadWrite
```

ข้อควรรู้:

- IAM user มี managed policies ได้ default 10 policies
- list ด้านบนครบ 10 แล้ว
- `IAMReadOnlyAccess` ซ้ำกับ `IAMFullAccess`
- ถ้าอนาคตต้องเพิ่ม `AmazonCognitoPowerUser` ให้ถอด `IAMReadOnlyAccess` ออกก่อน

---

## 10. Troubleshooting

ถ้าหา resource ไม่เจอ:

- เช็ค region ต้องเป็น `ap-southeast-1`
- เช็คว่าอยู่ AWS account เดียวกัน
- เช็ค CloudFormation stack ก่อน เพราะเป็น source of truth

ถ้า query DB แล้ว timeout หรือช้า:

- Aurora Serverless v2 อาจกำลัง resume จาก auto-pause
- รอแล้วรันอีกครั้ง

ถ้า Data API error เรื่อง secret:

- เช็คว่าใช้ `DBSecretArn` จาก CloudFormation output
- ห้ามใช้ secret value แทน secret ARN

ถ้าเพิ่ม IAM policy ไม่ได้:

- เช็คว่า user มี managed policies ครบ 10 แล้วหรือยัง
- ถ้าครบ ให้ถอด policy ที่ซ้ำ เช่น `IAMReadOnlyAccess`

---

## เอกสารที่เกี่ยวข้อง

- [aws-foundation.md](./aws-foundation.md)
- [aws-foundation-evidence.md](./aws-foundation-evidence.md)
- [deployment-env.md](./deployment-env.md)
- [security.md](./security.md)
- [../../infra/v2/README.md](../../infra/v2/README.md)
