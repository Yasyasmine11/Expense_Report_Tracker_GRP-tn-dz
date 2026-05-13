namespace ExpenseTrackerApp;

/// <summary>
/// Configuration AWS — remplacer par vos vraies valeurs après déploiement
/// </summary>
public static class AppConfig
{
    // Cognito
    public const string CognitoRegion   = "eu-west-3";
    public const string UserPoolId      = "eu-west-3_IFDSxyrQK";
    public const string AppClientId     = "42l7n46ng7hciqqb5degcdoiq9";

    // API Gateway — trailing slash required for relative URI resolution with HttpClient
    public const string ApiBaseUrl      = "https://rwfqaety92.execute-api.eu-west-3.amazonaws.com/prod/";
}
