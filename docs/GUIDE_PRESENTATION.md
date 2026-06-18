# 📚 GUIDE COMPLET — Expense Report Tracker
> Elyes Boudabous · Yasmine Aoudjit · Mohamed Amine Dhaoui  
> Module 5ENTAPP / E5WMD · Dr. Abdelhak TOUITI · ESTIAM Paris

---

# PARTIE 1 — CE QU'ON A CONSTRUIT

## L'idée en une phrase
Une app Windows/Android qui remplace les emails/Excel pour gérer les notes de frais, avec un système d'approbation automatisé sur AWS.

## Les 2 utilisateurs
| Utilisateur | Email | Mot de passe | Ce qu'il peut faire |
|---|---|---|---|
| Alice | alice@test.com | Employee1234! | Créer, uploader reçu, soumettre |
| Bob | bob@test.com | Manager1234! | Voir les notes, approuver, rejeter |

---

# PARTIE 2 — CE QU'ON A MIS SUR AWS

## Région : eu-west-3 (Paris) 🇫🇷
## Account ID : 706922781773

---

## 🔐 1. Amazon Cognito
**C'est quoi simplement ?** → Le système de login de l'app

**Ce qu'on a créé :**
- Un User Pool nommé `ExpenseTrackerPool`
- 2 groupes : `employees` (Alice) et `finance` (Bob)
- Quand Alice se connecte → Cognito lui donne un token JWT (badge numérique)
- Ce token contient : son ID, son email, son groupe

---

## 🚪 2. Amazon API Gateway
**C'est quoi simplement ?** → La porte d'entrée, le réceptionniste

**Ce qu'on a créé :**
- URL : `https://rwfqaety92.execute-api.eu-west-3.amazonaws.com/prod/`
- Vérifie automatiquement le token JWT avant chaque requête
- Route vers la bonne Lambda selon l'URL

| URL appelée | Lambda déclenchée |
|---|---|
| `POST /expenses` | createExpense |
| `GET /expenses` | getExpenses |
| `POST /expenses/{id}/submit` | submitExpense |
| `POST /expenses/{id}/approve` | approveExpense |
| `POST /expenses/{id}/reject` | rejectExpense |
| `GET /expenses/{id}/upload-url` | getUploadUrl |

---

## ⚡ 3. AWS Lambda (7 fonctions en C# .NET 8)
**C'est quoi simplement ?** → Des petits programmes qui s'exécutent seulement quand on les appelle

| Fonction | Ce qu'elle fait |
|---|---|
| `createExpense` | Crée une note en statut DRAFT dans DynamoDB |
| `getExpenses` | Retourne les notes (les siennes si Alice, toutes SUBMITTED si Bob) |
| `submitExpense` | Vérifie que c'est DRAFT → change en SUBMITTED |
| `approveExpense` | Vérifie que Bob est finance + que c'est SUBMITTED → APPROVED |
| `rejectExpense` | Même vérification → REJECTED + justification obligatoire |
| `getUploadUrl` | Génère un lien secret S3 valide 10 min pour uploader le reçu |
| `getExpenseById` | Récupère les détails d'une note précise |

---

## 🗄️ 4. Amazon DynamoDB
**C'est quoi simplement ?** → La base de données, le grand tableau où tout est sauvegardé

### Table : `ExpenseReports`

**Chaque ligne (item) ressemble à ça :**
```
PK             : USER#abc-123          ← identifiant d'Alice
SK             : EXPENSE#xyz-456       ← identifiant de la note
expenseId      : xyz-456
userId         : abc-123
userEmail      : alice@test.com
amount         : 340.00
category       : REPAS
description    : Déjeuner client
status         : SUBMITTED
StatusGSI_PK   : STATUS#SUBMITTED      ← utilisé par le GSI
receiptKey     : receipts/abc/xyz.jpg
createdAt      : 2026-05-21T10:00:00Z
updatedAt      : 2026-05-21T10:05:00Z
```

### C'est quoi le GSI ? (Global Secondary Index)

**Le problème :**
Bob veut voir TOUTES les notes SUBMITTED de tous les employés.
Mais les données sont triées par utilisateur (PK = USER#...).
Sans GSI → il faudrait scanner toute la table = lent et cher.

**La solution — le GSI `StatusIndex` :**
C'est un 2ème tableau trié par statut, mis à jour automatiquement.

```
StatusGSI_PK        SK
STATUS#DRAFT        EXPENSE#aaa
STATUS#SUBMITTED    EXPENSE#bbb   ← Bob query ici
STATUS#SUBMITTED    EXPENSE#ccc   ← et ici
STATUS#APPROVED     EXPENSE#ddd
```

Bob fait une seule requête : "donne moi tout ce qui a StatusGSI_PK = STATUS#SUBMITTED"
→ Il obtient instantanément toutes les notes en attente, peu importe l'employé.

**Analogie :** La table = livre trié par nom. Le GSI = index à la fin du livre trié par statut.

---

## 📦 5. Amazon S3
**C'est quoi simplement ?** → Le stockage des photos de reçus

- Bucket : `expense-tracker-receipts-706922781773`
- 100% privé — personne ne peut accéder directement
- Fichiers stockés : `receipts/{userId}/{expenseId}.jpg`
- Accès uniquement via URL temporaire de 10 min générée par Lambda

---

## 🔑 6. AWS IAM
**C'est quoi simplement ?** → Le gestionnaire des permissions entre services AWS

- Rôle : `lambda-expense-tracker-role`
- Lambda peut : lire/écrire DynamoDB + lire/écrire S3
- Lambda ne peut PAS : toucher Cognito, créer d'autres ressources
- Principe : donner le minimum nécessaire (least privilege)

---

# PARTIE 3 — LE FRONTEND (L'APPLICATION)

## Où est le code ?
```
frontend/
└── ExpenseTrackerApp/
    ├── Pages/
    │   ├── LoginPage.xaml         → écran de connexion
    │   ├── EmployeePage.xaml      → liste des notes d'Alice
    │   ├── ManagerPage.xaml       → file d'approbation de Bob
    │   └── CreateExpensePage.xaml → formulaire + upload photo
    ├── Services/
    │   ├── AuthService.cs         → connexion via Cognito
    │   └── ExpenseService.cs      → appels vers API Gateway
    ├── Models/
    │   └── ExpenseReport.cs       → structure d'une note
    └── AppConfig.cs               → URLs et IDs AWS
```

## Ce que voit Alice
1. LoginPage → entre email/mot de passe
2. EmployeePage → voit ses notes avec compteurs (Brouillons / En attente / Approuvées)
3. CreateExpensePage → remplit montant, catégorie, description, choisit photo → enregistre

## Ce que voit Bob
1. LoginPage → entre email/mot de passe
2. ManagerPage → voit toutes les notes SUBMITTED → approuve ou rejette avec justification

---

# PARTIE 4 — LE WORKFLOW ENFORCED

## La règle
```
DRAFT → SUBMITTED → APPROVED
                 ↘ REJECTED → SUBMITTED (resoumission)
```

## Comment c'est bloqué dans le code ?

**submitExpense :** seul DRAFT ou REJECTED peut être soumis
```csharp
if (currentStatus != "DRAFT" && currentStatus != "REJECTED")
    return BadRequest("Impossible de soumettre");
```

**approveExpense :** seul SUBMITTED peut être approuvé + seul finance peut approuver
```csharp
if (!IsFinanceManager(claims))
    return Forbidden("Accès refusé");

if (currentStatus != "SUBMITTED")
    return BadRequest("Impossible d'approuver");
```

**Concrètement :**
- Alice ne peut pas approuver sa propre note → 403 Forbidden
- Alice ne peut pas soumettre une note déjà approuvée → 400 Bad Request
- Bob ne peut pas approuver une note en DRAFT → 400 Bad Request

---

# PARTIE 5 — ARGUMENTS POUR L'ARCHITECTURE

| Question | Réponse |
|---|---|
| Pourquoi Serverless ? | On ne paie que ce qu'on utilise. Pas de serveur qui tourne 24h/24 pour rien |
| Pourquoi Lambda ? | Scale automatiquement. 1000 employés en même temps = 1000 instances auto |
| Pourquoi DynamoDB ? | Pas d'administration, pas de schema fixe, scale automatique |
| Pourquoi le GSI ? | Sans GSI = scan complet de la table. Avec GSI = requête directe, instantané |
| Pourquoi S3 + pre-signed URLs ? | Lambda a une limite 6MB. Upload direct S3 = pas de limite + plus rapide |
| Pourquoi .NET MAUI ? | Un seul code pour Windows ET Android. Même langage C# que les Lambdas |
| Pourquoi state machine server-side ? | Impossible à bypasser depuis le client. Même un hacker ne peut pas tricher |

---

# PARTIE 6 — SPEECH COMPLET

## Introduction — Yasmine
"Bonjour Dr. TOUITI. Notre équipe : Elyes Boudabous, Yasmine Aoudjit et Mohamed Amine Dhaoui.

Dans beaucoup d'entreprises aujourd'hui, les notes de frais se gèrent encore par email ou Excel.
Résultat : remboursements perdus, doubles paiements, audits impossibles.
Notre projet digitalise ce processus avec une architecture 100% serverless sur AWS
et une interface mobile et desktop."

## Architecture — Mohamed Amine
"Notre architecture suit un flux simple. L'employé utilise l'app MAUI sur Windows ou Android.
Chaque requête porte un token JWT. Ce token arrive sur API Gateway qui le valide via Cognito.
Si le token est invalide, la requête est rejetée avant même d'atteindre notre code.
API Gateway route ensuite vers la bonne Lambda parmi nos 7 fonctions C# .NET 8.
Les données sont dans DynamoDB, les reçus dans S3 en accès privé,
et les permissions sont gérées par IAM avec le principe de least privilege."

## Démo — Elyes
"Je vous montre le flux complet.
Je me connecte en tant qu'Alice — Cognito valide et retourne un token JWT.
Je crée une note, je choisis une photo de reçu —
Lambda génère une URL temporaire S3 de 10 minutes et l'app uploade directement.
Je soumets — statut passe à SUBMITTED.
Je me connecte maintenant en tant que Bob, Finance Manager.
Il voit la queue des notes récupérées via notre GSI StatusIndex.
Il approuve — statut APPROVED.
Voici dans la console DynamoDB la preuve que tout est bien persisté."

## Points techniques — Partagé

**RBAC — Yasmine :**
"Dans chaque Lambda sensible, on lit le claim cognito:groups du token JWT.
Si l'utilisateur n'est pas dans le groupe finance, on retourne 403 immédiatement.
C'est impossible à contourner depuis le client."

**State Machine — Mohamed Amine :**
"Avant chaque modification, Lambda vérifie le statut actuel dans DynamoDB.
On ne peut soumettre que depuis DRAFT ou REJECTED.
On ne peut approuver que depuis SUBMITTED.
Si quelqu'un appelle l'API directement avec un mauvais statut — c'est bloqué."

**Pre-signed URLs — Yasmine :**
"Le bucket S3 est totalement privé.
Lambda génère une URL signée valide 10 minutes.
L'app uploade directement sur S3 sans passer par notre backend —
ça évite la limite de 6MB de Lambda et c'est plus performant."

## Conclusion — Mohamed Amine
"L'infrastructure est déployée en eu-west-3 Paris.
Nous avons testé le flux complet end-to-end.
Les améliorations envisagées : CI/CD GitHub Actions, pagination DynamoDB,
et AWS Step Functions pour enrichir le workflow.
Merci, nous sommes disponibles pour vos questions."

---

# PARTIE 7 — RÉPONSES AUX QUESTIONS DU PROF

**"Pourquoi ce GSI ?"**
Sans GSI, récupérer les notes SUBMITTED = scan de toute la table.
Le GSI crée un index secondaire trié par statut.
Bob fait une requête directe sur STATUS#SUBMITTED — instantané.

**"Pourquoi PK=USER# et SK=EXPENSE# ?"**
Single-table design. Un seul Query suffit pour récupérer toutes les notes d'un employé.
On évite les jointures qui n'existent pas en DynamoDB.

**"Comment le workflow est enforced ?"**
Lambda lit le statut actuel dans DynamoDB avant chaque UpdateItem.
Si la transition n'est pas autorisée, on retourne 400.
Le client ne peut jamais bypasser ça.

**"Pourquoi pas upload via Lambda directement ?"**
Limite de 6MB sur le payload Lambda.
Pre-signed URL = upload direct S3 sans limite + moins de latence.

**"Pourquoi .NET MAUI ?"**
Un seul code pour Windows et Android. Cohérent avec le backend en C#.
Pas besoin d'apprendre 2 langages différents.

**"Qu'est-ce que vous amélioreriez ?"**
CI/CD GitHub Actions pour déployer automatiquement les Lambdas,
pagination DynamoDB pour scaler sur de grands volumes,
SNS pour notifier Alice par email quand sa note est traitée,
Step Functions pour un workflow plus complexe.
