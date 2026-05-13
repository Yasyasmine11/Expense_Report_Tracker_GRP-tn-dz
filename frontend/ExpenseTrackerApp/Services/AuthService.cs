using Amazon;
using Amazon.CognitoIdentityProvider;
using Amazon.CognitoIdentityProvider.Model;
using ExpenseTrackerApp.Models;
using System.IdentityModel.Tokens.Jwt;

namespace ExpenseTrackerApp.Services;

public class AuthService
{
    private readonly AmazonCognitoIdentityProviderClient _cognito;

    // IdToken is used for API calls — it contains cognito:groups + sub + email claims
    private static string? _idToken;
    private static string? _userId;
    private static string? _userEmail;
    private static bool    _isFinanceManager;

    public AuthService()
    {
        _cognito = new AmazonCognitoIdentityProviderClient(
            RegionEndpoint.GetBySystemName(AppConfig.CognitoRegion));
    }

    public async Task<LoginResult> LoginAsync(string email, string password)
    {
        try
        {
            var response = await _cognito.InitiateAuthAsync(new InitiateAuthRequest
            {
                AuthFlow  = AuthFlowType.USER_PASSWORD_AUTH,
                ClientId  = AppConfig.AppClientId,
                AuthParameters = new Dictionary<string, string>
                {
                    { "USERNAME", email },
                    { "PASSWORD", password }
                }
            });

            var tokens = response.AuthenticationResult;

            // Decode IdToken — it contains sub, email, cognito:groups
            var handler = new JwtSecurityTokenHandler();
            var jwt     = handler.ReadJwtToken(tokens.IdToken);

            var sub    = jwt.Claims.FirstOrDefault(c => c.Type == "sub")?.Value    ?? "";
            var mail   = jwt.Claims.FirstOrDefault(c => c.Type == "email")?.Value  ?? email;
            var groups = jwt.Claims.Where(c => c.Type == "cognito:groups")
                                   .Select(c => c.Value)
                                   .ToList();

            _idToken          = tokens.IdToken;   // ← use IdToken for API calls
            _userId           = sub;
            _userEmail        = mail;
            _isFinanceManager = groups.Contains("finance");

            await SecureStorage.SetAsync("id_token",   tokens.IdToken);
            await SecureStorage.SetAsync("user_id",    sub);
            await SecureStorage.SetAsync("user_email", mail);
            await SecureStorage.SetAsync("is_finance", _isFinanceManager.ToString());

            return new LoginResult
            {
                Success          = true,
                IdToken          = tokens.IdToken,
                IsFinanceManager = _isFinanceManager,
                Email            = mail,
                UserId           = sub
            };
        }
        catch (NotAuthorizedException)
        {
            return new LoginResult { Success = false, ErrorMessage = "Email ou mot de passe incorrect." };
        }
        catch (UserNotFoundException)
        {
            return new LoginResult { Success = false, ErrorMessage = "Utilisateur introuvable." };
        }
        catch (Exception ex)
        {
            return new LoginResult { Success = false, ErrorMessage = $"Erreur de connexion : {ex.Message}" };
        }
    }

    public async Task LogoutAsync()
    {
        SecureStorage.Remove("id_token");
        SecureStorage.Remove("user_id");
        SecureStorage.Remove("user_email");
        SecureStorage.Remove("is_finance");
        _idToken          = null;
        _userId           = null;
        _userEmail        = null;
        _isFinanceManager = false;
    }

    public static string? GetIdToken()    => _idToken;
    public static string? GetUserId()     => _userId;
    public static string? GetUserEmail()  => _userEmail;
    public static bool    IsFinance()     => _isFinanceManager;
}
