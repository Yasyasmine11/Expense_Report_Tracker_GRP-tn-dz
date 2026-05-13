using Amazon.DynamoDBv2;
using Amazon.DynamoDBv2.Model;
using Amazon.Lambda.APIGatewayEvents;
using Amazon.Lambda.Core;
using Newtonsoft.Json;

[assembly: LambdaSerializer(typeof(Amazon.Lambda.Serialization.SystemTextJson.DefaultLambdaJsonSerializer))]

namespace ApproveExpense;

public class Function
{
    private readonly IAmazonDynamoDB _dynamo;
    private readonly string _tableName;

    public Function()
    {
        _dynamo    = new AmazonDynamoDBClient();
        _tableName = Environment.GetEnvironmentVariable("TABLE_NAME") ?? "ExpenseReports";
    }

    public async Task<APIGatewayProxyResponse> FunctionHandler(
        APIGatewayProxyRequest request, ILambdaContext context)
    {
        try
        {
            var claims = request.RequestContext.Authorizer.Claims;

            // ── RBAC : seul le groupe "finance" peut approuver ────────────
            if (!IsFinanceManager(claims))
            {
                return Forbidden("Only Finance Managers can approve expense reports.");
            }
            // ──────────────────────────────────────────────────────────────

            var body      = JsonConvert.DeserializeObject<ApproveDto>(request.Body);
            var expenseId = request.PathParameters["expenseId"];

            if (body == null || string.IsNullOrEmpty(body.UserId))
                return BadRequest("UserId is required in the request body.");

            // Récupérer l'expense
            var getResult = await _dynamo.GetItemAsync(new GetItemRequest
            {
                TableName = _tableName,
                Key = new()
                {
                    ["PK"] = new() { S = $"USER#{body.UserId}" },
                    ["SK"] = new() { S = $"EXPENSE#{expenseId}" }
                }
            });

            if (!getResult.IsItemSet || getResult.Item.Count == 0)
                return NotFound("Expense not found.");

            var currentStatus = getResult.Item["status"].S;

            // ── STATE MACHINE : seul SUBMITTED peut être approuvé ─────────
            if (currentStatus != "SUBMITTED")
            {
                return BadRequest(
                    $"Cannot approve an expense with status '{currentStatus}'. " +
                    "Only SUBMITTED expenses can be approved.");
            }
            // ──────────────────────────────────────────────────────────────

            var managerId = claims["sub"];

            await _dynamo.UpdateItemAsync(new UpdateItemRequest
            {
                TableName        = _tableName,
                Key = new()
                {
                    ["PK"] = new() { S = $"USER#{body.UserId}" },
                    ["SK"] = new() { S = $"EXPENSE#{expenseId}" }
                },
                UpdateExpression =
                    "SET #s = :s, StatusGSI_PK = :gsi, reviewedBy = :mgr, updatedAt = :ts",
                ExpressionAttributeNames  = new() { ["#s"] = "status" },
                ExpressionAttributeValues = new()
                {
                    [":s"]   = new() { S = "APPROVED" },
                    [":gsi"] = new() { S = "STATUS#APPROVED" },
                    [":mgr"] = new() { S = managerId },
                    [":ts"]  = new() { S = DateTime.UtcNow.ToString("o") }
                }
            });

            context.Logger.LogInformation(
                $"Expense {expenseId} APPROVED by manager {managerId}");

            return Ok("{\"message\":\"Expense approved successfully\",\"status\":\"APPROVED\"}");
        }
        catch (Exception ex)
        {
            context.Logger.LogError($"Error approving expense: {ex.Message}");
            return ServerError(ex.Message);
        }
    }

    // Vérifie si l'utilisateur appartient au groupe "finance" via les claims JWT
    private static bool IsFinanceManager(IDictionary<string, string> claims)
    {
        if (claims.TryGetValue("cognito:groups", out var groups))
            return groups.Contains("finance");
        return false;
    }

    private static APIGatewayProxyResponse Ok(string body) =>
        new() { StatusCode = 200, Body = body, Headers = CorsHeaders() };

    private static APIGatewayProxyResponse BadRequest(string msg) =>
        new() { StatusCode = 400, Body = $"{{\"error\":\"{msg}\"}}", Headers = CorsHeaders() };

    private static APIGatewayProxyResponse Forbidden(string msg) =>
        new() { StatusCode = 403, Body = $"{{\"error\":\"{msg}\"}}", Headers = CorsHeaders() };

    private static APIGatewayProxyResponse NotFound(string msg) =>
        new() { StatusCode = 404, Body = $"{{\"error\":\"{msg}\"}}", Headers = CorsHeaders() };

    private static APIGatewayProxyResponse ServerError(string msg) =>
        new() { StatusCode = 500, Body = $"{{\"error\":\"{msg}\"}}", Headers = CorsHeaders() };

    private static Dictionary<string, string> CorsHeaders() => new()
    {
        ["Content-Type"]                 = "application/json",
        ["Access-Control-Allow-Origin"]  = "*",
        ["Access-Control-Allow-Headers"] = "Content-Type,Authorization",
        ["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    };
}

public class ApproveDto
{
    public string UserId { get; set; } = "";
}
