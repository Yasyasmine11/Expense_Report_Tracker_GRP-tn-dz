#!/bin/bash
# =============================================================================
# setup-infrastructure.sh
# Script de déploiement complet de l'infrastructure AWS pour Expense Tracker
# Usage: bash setup-infrastructure.sh
# =============================================================================

set -e  # stoppe le script si une commande échoue

REGION="eu-west-3"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
TABLE_NAME="ExpenseReports"
BUCKET_NAME="expense-tracker-receipts-${ACCOUNT_ID}"
POOL_NAME="ExpenseTrackerPool"

echo "========================================"
echo " Expense Tracker — Infrastructure Setup"
echo " Region   : $REGION"
echo " Account  : $ACCOUNT_ID"
echo "========================================"

# ── 1. S3 Bucket ─────────────────────────────────────────────────────────────
echo ""
echo "[1/5] Creating S3 bucket: $BUCKET_NAME"

aws s3api create-bucket \
  --bucket "$BUCKET_NAME" \
  --region "$REGION" \
  --create-bucket-configuration LocationConstraint="$REGION"

# Bloquer tout accès public (les reçus ne sont jamais publics)
aws s3api put-public-access-block \
  --bucket "$BUCKET_NAME" \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

echo "✅ Bucket created: $BUCKET_NAME"

# ── 2. DynamoDB Table ─────────────────────────────────────────────────────────
echo ""
echo "[2/5] Creating DynamoDB table: $TABLE_NAME"

aws dynamodb create-table \
  --region "$REGION" \
  --table-name "$TABLE_NAME" \
  --attribute-definitions \
    AttributeName=PK,AttributeType=S \
    AttributeName=SK,AttributeType=S \
    AttributeName=StatusGSI_PK,AttributeType=S \
  --key-schema \
    AttributeName=PK,KeyType=HASH \
    AttributeName=SK,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --global-secondary-indexes '[
    {
      "IndexName": "StatusIndex",
      "KeySchema": [
        {"AttributeName": "StatusGSI_PK", "KeyType": "HASH"},
        {"AttributeName": "SK", "KeyType": "RANGE"}
      ],
      "Projection": {"ProjectionType": "ALL"}
    }
  ]'

# Attendre que la table soit active
echo "   Waiting for table to be active..."
aws dynamodb wait table-exists --table-name "$TABLE_NAME" --region "$REGION"
echo "✅ DynamoDB table created: $TABLE_NAME"

# ── 3. Cognito User Pool ──────────────────────────────────────────────────────
echo ""
echo "[3/5] Creating Cognito User Pool: $POOL_NAME"

POOL_ID=$(aws cognito-idp create-user-pool \
  --region "$REGION" \
  --pool-name "$POOL_NAME" \
  --policies '{"PasswordPolicy":{"MinimumLength":8,"RequireUppercase":true,"RequireLowercase":true,"RequireNumbers":true,"RequireSymbols":false}}' \
  --auto-verified-attributes email \
  --username-attributes email \
  --query 'UserPool.Id' \
  --output text)

echo "   Pool ID: $POOL_ID"

# App client (pas de secret pour une app mobile)
CLIENT_ID=$(aws cognito-idp create-user-pool-client \
  --region "$REGION" \
  --user-pool-id "$POOL_ID" \
  --client-name "ExpenseTrackerMobile" \
  --explicit-auth-flows USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH \
  --no-generate-secret \
  --query 'UserPoolClient.ClientId' \
  --output text)

echo "   Client ID: $CLIENT_ID"

# Groupes RBAC
aws cognito-idp create-group --region "$REGION" \
  --group-name employees --user-pool-id "$POOL_ID" \
  --description "Regular employees who submit expenses"

aws cognito-idp create-group --region "$REGION" \
  --group-name finance --user-pool-id "$POOL_ID" \
  --description "Finance managers who approve/reject expenses"

# Utilisateurs de test
echo "   Creating test users..."

# Employé : alice
aws cognito-idp admin-create-user --region "$REGION" \
  --user-pool-id "$POOL_ID" --username alice@test.com \
  --user-attributes Name=email,Value=alice@test.com Name=email_verified,Value=true \
  --temporary-password "Temp1234!" --message-action SUPPRESS

aws cognito-idp admin-set-user-password --region "$REGION" \
  --user-pool-id "$POOL_ID" --username alice@test.com \
  --password "Employee1234!" --permanent

aws cognito-idp admin-add-user-to-group --region "$REGION" \
  --user-pool-id "$POOL_ID" --username alice@test.com --group-name employees

# Finance Manager : bob
aws cognito-idp admin-create-user --region "$REGION" \
  --user-pool-id "$POOL_ID" --username bob@test.com \
  --user-attributes Name=email,Value=bob@test.com Name=email_verified,Value=true \
  --temporary-password "Temp1234!" --message-action SUPPRESS

aws cognito-idp admin-set-user-password --region "$REGION" \
  --user-pool-id "$POOL_ID" --username bob@test.com \
  --password "Manager1234!" --permanent

aws cognito-idp admin-add-user-to-group --region "$REGION" \
  --user-pool-id "$POOL_ID" --username bob@test.com --group-name finance

echo "✅ Cognito User Pool created"
echo "   alice@test.com (employee) / password: Employee1234!"
echo "   bob@test.com   (finance)  / password: Manager1234!"

# ── 4. IAM Role pour Lambda ───────────────────────────────────────────────────
echo ""
echo "[4/5] Creating IAM Role for Lambda"

cat > /tmp/trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Service": "lambda.amazonaws.com" },
    "Action": "sts:AssumeRole"
  }]
}
EOF

ROLE_ARN=$(aws iam create-role \
  --role-name lambda-expense-tracker-role \
  --assume-role-policy-document file:///tmp/trust-policy.json \
  --query 'Role.Arn' --output text)

# CloudWatch Logs
aws iam attach-role-policy \
  --role-name lambda-expense-tracker-role \
  --policy-arn arn:aws:iam::aws:policy/AWSLambdaBasicExecutionRole

# DynamoDB + S3 (least privilege)
cat > /tmp/expense-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query"
      ],
      "Resource": [
        "arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/${TABLE_NAME}",
        "arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/${TABLE_NAME}/index/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject"],
      "Resource": "arn:aws:s3:::${BUCKET_NAME}/*"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name lambda-expense-tracker-role \
  --policy-name ExpenseTrackerPolicy \
  --policy-document file:///tmp/expense-policy.json

echo "✅ IAM Role created: $ROLE_ARN"

# ── 5. Résumé ─────────────────────────────────────────────────────────────────
echo ""
echo "========================================"
echo " ✅ Infrastructure deployed successfully!"
echo "========================================"
echo ""
echo "Save these values in your .env or aws-lambda-tools-defaults.json:"
echo ""
echo "  REGION=$REGION"
echo "  TABLE_NAME=$TABLE_NAME"
echo "  RECEIPTS_BUCKET=$BUCKET_NAME"
echo "  COGNITO_POOL_ID=$POOL_ID"
echo "  COGNITO_CLIENT_ID=$CLIENT_ID"
echo "  LAMBDA_ROLE_ARN=$ROLE_ARN"
echo ""
echo "Next step: deploy Lambda functions with:"
echo "  cd backend/lambdas/createExpense && dotnet lambda deploy-function"
