using Amazon.DynamoDBv2;
using Amazon.DynamoDBv2.Model;
using Amazon.Lambda.APIGatewayEvents;
using Amazon.Lambda.Core;

[assembly: LambdaSerializer(typeof(Amazon.Lambda.Serialization.SystemTextJson.DefaultLambdaJsonSerializer))]

namespace SubmitExpense;

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
            var claims    = request.RequestContext.Authorizer.Claims;
            var userId    = claims["sub"];
            var expenseId = request.PathParameters["expenseId"];

            // Récupérer l'expense existante
            var getResult = await _dynamo.GetItemAsync(new GetItemRequest
            {
                TableName = _tableName,
                Key = new()
                {
                    ["PK"] = new() { S = $"USER#{userId}" },
                    ["SK"] = new() { S = $"EXPENSE#{expenseId}" }
                }
            });

            if (!getResult.IsItemSet || getResult.Item.Count == 0)
                return NotFound("Expense not found.");

            var currentStatus = getResult.Item["status"].S;

            // ── STATE MACHINE ─────────────────────────────────────────────
            // Seul DRAFT ou REJECTED peut être soumis
            if (currentStatus != "DRAFT" && currentStatus != "REJECTED")
            {
                return BadRequest(
                    $"Cannot submit an expense with status '{currentStatus}'. " +
                    "Only DRAFT or REJECTED expenses can be submitted.");
            }
            // ──────────────────────────────────────────────────────────────

            await _dynamo.UpdateItemAsync(new UpdateItemRequest
            {
                TableName        = _tableName,
                Key = new()
                {
                    ["PK"] = new() { S = $"USER#{userId}" },
                    ["SK"] = new() { S = $"EXPENSE#{expenseId}" }
                },
                UpdateExpression = "SET #s = :s, StatusGSI_PK = :gsi, updatedAt = :ts",
                ExpressionAttributeNames  = new() { ["#s"] = "status" },
                ExpressionAttributeValues = new()
                {
                    [":s"]   = new() { S = "SUBMITTED" },
                    [":gsi"] = new() { S = "STATUS#SUBMITTED" },
                    [":ts"]  = new() { S = DateTime.UtcNow.ToString("o") }
                }
            });

            context.Logger.LogInformation($"Expense {expenseId} submitted by {userId}");

            return Ok("{\"message\":\"Expense submitted successfully\",\"status\":\"SUBMITTED\"}");
        }
        catch (Exception ex)
        {
            context.Logger.LogError($"Error submitting expense: {ex.Message}");
            return ServerError(ex.Message);
        }
    }

    private static APIGatewayProxyResponse Ok(string body) =>
        new() { StatusCode = 200, Body = body, Headers = CorsHeaders() };

    private static APIGatewayProxyResponse BadRequest(string msg) =>
        new() { StatusCode = 400, Body = $"{{\"error\":\"{msg}\"}}", Headers = CorsHeaders() };

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
