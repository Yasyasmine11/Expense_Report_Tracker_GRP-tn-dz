namespace ExpenseTrackerApp;

/// <summary>
/// Configuration AWS — remplacer par vos vraies valeurs après déploiement
/// </summary>
public static class AppConfig
{
    // Cognito
    public const string CognitoRegion   = "eu-west-3";
    public const string UserPoolId      = "eu-west-3_XXXXXXXXX";   // ← à remplacer
    public const string AppClientId     = "XXXXXXXXXXXXXXXXXXXXXXXXXX"; // ← à remplacer

    // API Gateway
    public const string ApiBaseUrl      = "https://XXXXXXXXXX.execute-api.eu-west-3.amazonaws.com/prod";
    // ← à remplacer après déploiement API Gateway
}
