# 💼 Expense Report Tracker — AWS Serverless

> Module 5ENTAPP / E5WMD · Enterprise Software Engineering on AWS  
> Dr. Abdelhak TOUITI · Master 2 · ESTIAM Paris

## Équipe

| Nom | GitHub |
|---|---|
| Elyes Boudabous | [@Boudabous2001](https://github.com/Boudabous2001) |
| Yasmine Aoudjit | [@Yasyasmine11](https://github.com/Yasyasmine11) |
| Mohamed Amine Dhaoui | [@medaminedh](https://github.com/medaminedha) |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        .NET MAUI App                        │
│              (Employee view / Finance Manager view)          │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS + Bearer Token (JWT)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Amazon API Gateway                        │
│              (REST API + Cognito Authorizer)                 │
└──────┬──────────┬──────────┬──────────┬──────────┬──────────┘
       │          │          │          │          │
       ▼          ▼          ▼          ▼          ▼
  createExpense  getExpenses submitExpense approveExpense rejectExpense
  getUploadUrl
       │
       ▼
┌─────────────────┐     ┌─────────────────────────────────────┐
│   DynamoDB      │     │              Amazon S3               │
│  ExpenseReports │     │      expense-tracker-receipts        │
│  + StatusIndex  │     │    (receipts via pre-signed URLs)    │
└─────────────────┘     └─────────────────────────────────────┘
       ▲
┌─────────────────┐
│ Amazon Cognito  │
│  User Pool      │
│  Groups:        │
│  - employees    │
│  - finance      │
└─────────────────┘
```

## Services AWS utilisés

| Service | Rôle |
|---|---|
| **Amazon Cognito** | Auth, JWT, RBAC via groupes (`employees` / `finance`) |
| **Amazon API Gateway** | Point d'entrée REST, valide le JWT via Cognito Authorizer |
| **AWS Lambda** | Logique métier serverless (C# .NET 8) |
| **Amazon DynamoDB** | Stockage NoSQL avec GSI pour les access patterns |
| **Amazon S3** | Stockage des reçus (accès via pre-signed URLs uniquement) |
| **AWS IAM** | Rôle Lambda avec least privilege (DynamoDB + S3 uniquement) |

## Modèle DynamoDB

**Table : `ExpenseReports`**

| PK | SK | Attributs |
|---|---|---|
| `USER#<userId>` | `EXPENSE#<expenseId>` | amount, category, description, status, receiptKey, justification, createdAt, updatedAt |

**GSI : `StatusIndex`**
- Hash key : `StatusGSI_PK` (ex: `STATUS#SUBMITTED`)
- Range key : `SK`
- Permet au Finance Manager de récupérer toutes les notes en attente sans scan

## State Machine

```
DRAFT ──→ SUBMITTED ──→ APPROVED
  ↑              └──→ REJECTED ──┘
  └────────────────────────────────
```

Les transitions sont validées **server-side** dans les Lambda functions.  
Le client ne peut pas bypasser les règles métier.

## RBAC via Cognito

Les claims JWT contiennent `cognito:groups`. Lambda lit ce claim :

```csharp
private static bool IsFinanceManager(IDictionary<string, string> claims)
{
    if (claims.TryGetValue("cognito:groups", out var groups))
        return groups.Contains("finance");
    return false;
}
```

- `employees` → peut créer, soumettre, uploader un reçu
- `finance` → peut approuver ou rejeter les notes soumises

## Pré-requis

- .NET 8 SDK
- AWS CLI configuré (`aws configure`)
- Visual Studio 2022 + AWS Toolkit

## Déploiement

### 1. Infrastructure AWS

```bash
cd backend/infrastructure
bash setup-infrastructure.sh
```

Le script crée : S3 bucket, DynamoDB table, Cognito User Pool, IAM Role.  
**Notez les valeurs retournées** (POOL_ID, CLIENT_ID, ROLE_ARN, BUCKET_NAME).

### 2. Configurer les Lambda functions

Dans chaque dossier `backend/lambdas/<name>/`, créer `aws-lambda-tools-defaults.json` :

```json
{
  "region": "eu-west-3",
  "configuration": "Release",
  "framework": "net8.0",
  "function-runtime": "dotnet8",
  "function-memory-size": 256,
  "function-timeout": 30,
  "function-role": "<ROLE_ARN>",
  "environment-variables": "TABLE_NAME=ExpenseReports;RECEIPTS_BUCKET=<BUCKET_NAME>"
}
```

### 3. Déployer les Lambda functions

```bash
cd backend/lambdas/createExpense  && dotnet lambda deploy-function CreateExpense
cd backend/lambdas/getExpenses    && dotnet lambda deploy-function GetExpenses
cd backend/lambdas/submitExpense  && dotnet lambda deploy-function SubmitExpense
cd backend/lambdas/approveExpense && dotnet lambda deploy-function ApproveExpense
cd backend/lambdas/rejectExpense  && dotnet lambda deploy-function RejectExpense
cd backend/lambdas/getUploadUrl   && dotnet lambda deploy-function GetUploadUrl
```

### 4. Configurer le frontend MAUI

Mettre à jour `frontend/ExpenseTrackerApp/AppConfig.cs` avec :
- `UserPoolId` et `AppClientId` issus du script d'infra
- `ApiBaseUrl` : URL de l'API Gateway après déploiement

## Comptes de test

| Utilisateur | Email | Mot de passe | Rôle |
|---|---|---|---|
| Alice | alice@test.com | Employee1234! | Employee |
| Bob | bob@test.com | Manager1234! | Finance Manager |

## Structure du projet

```
├── backend/
│   ├── infrastructure/
│   │   └── setup-infrastructure.sh
│   └── lambdas/
│       ├── createExpense/
│       ├── getExpenses/
│       ├── submitExpense/
│       ├── approveExpense/
│       ├── rejectExpense/
│       └── getUploadUrl/
├── frontend/
│   └── ExpenseTrackerApp/    (.NET MAUI)
└── docs/                     (rapport PDF)
```
