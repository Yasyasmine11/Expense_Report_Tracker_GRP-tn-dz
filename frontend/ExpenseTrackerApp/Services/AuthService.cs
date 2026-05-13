using Amazon;
using Amazon.CognitoIdentityProvider;
using Amazon.CognitoIdentityProvider.Model;
using ExpenseTrackerApp.Models;
using Microsoft.IdentityModel.Tokens;
using System.IdentityModel.Tokens.Jwt;

namespace ExpenseTrackerApp.Services;

public class AuthService
{
    private readonly AmazonCognitoIdentityProviderClient _cognito;
    private static string? _accessToken;
    private static string? _userId;
    private static bool _isFinanceManager;

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
            _accessToken = tokens.AccessToken;

            // Décoder le JWT pour extraire les claims (sub, email, groups)
            var handler   = new JwtSecurityTokenHandler();
            var jwt       = handler.ReadJwtToken(tokens.IdToken);
            var sub       = jwt.Claims.FirstOrDefault(c => c.Type == "sub")?.Value ?? "";
            var groups    = jwt.Claims
                               .Where(c => c.Type == "cognito:groups")
                               .Select(c => c.Value)
                               .ToList();

            _userId          = sub;
            _isFinanceManager = groups.Contains("finance");

            // Stocker le token de façon sécurisée
            await SecureStorage.SetAsync("access_token", tokens.AccessToken);
            await SecureStorage.SetAsync("user_id",      sub);
            await SecureStorage.SetAsync("is_finance",   _isFinanceManager.ToString());

            return new LoginResult
            {
                Success          = true,
                AccessToken      = tokens.AccessToken,
                IdToken          = tokens.IdToken,
                IsFinanceManager = _isFinanceManager,
                Email            = email,
                UserId           = sub
            };
        }
        catch (NotAuthorizedException)
        {
            return new LoginResult { Success = false, ErrorMessage = "Incorrect username or password." };
        }
        catch (UserNotFoundException)
        {
            return new LoginResult { Success = false, ErrorMessage = "User not found." };
        }
        catch (Exception ex)
        {
            return new LoginResult { Success = false, ErrorMessage = $"Login error: {ex.Message}" };
        }
    }

    public async Task LogoutAsync()
    {
        SecureStorage.Remove("access_token");
        SecureStorage.Remove("user_id");
        SecureStorage.Remove("is_finance");
        _accessToken      = null;
        _userId           = null;
        _isFinanceManager = false;
    }

    public static string? GetAccessToken() => _accessToken;
    public static string? GetUserId()      => _userId;
    public static bool IsFinance()         => _isFinanceManager;
}
