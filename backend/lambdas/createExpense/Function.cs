using Amazon.DynamoDBv2;
using Amazon.DynamoDBv2.Model;
using Amazon.Lambda.APIGatewayEvents;
using Amazon.Lambda.Core;
using Newtonsoft.Json;

[assembly: LambdaSerializer(typeof(Amazon.Lambda.Serialization.SystemTextJson.DefaultLambdaJsonSerializer))]

namespace CreateExpense;

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
            // Récupérer l'identité depuis les claims Cognito
            var claims   = request.RequestContext.Authorizer.Claims;
            var userId   = claims["sub"];
            var email    = claims.ContainsKey("email") ? claims["email"] : "";

            // Désérialiser le body
            var dto = JsonConvert.DeserializeObject<CreateExpenseDto>(request.Body);
            if (dto == null || dto.Amount <= 0 || string.IsNullOrEmpty(dto.Category))
            {
                return BadRequest("Amount and Category are required.");
            }

            var expenseId = Guid.NewGuid().ToString();
            var now       = DateTime.UtcNow.ToString("o");

            // Construire l'item DynamoDB
            var item = new Dictionary<string, AttributeValue>
            {
                ["PK"]           = new() { S = $"USER#{userId}" },
                ["SK"]           = new() { S = $"EXPENSE#{expenseId}" },
                ["expenseId"]    = new() { S = expenseId },
                ["userId"]       = new() { S = userId },
                ["userEmail"]    = new() { S = email },
                ["amount"]       = new() { N = dto.Amount.ToString("F2") },
                ["category"]     = new() { S = dto.Category },
                ["description"]  = new() { S = dto.Description ?? "" },
                ["status"]       = new() { S = "DRAFT" },
                ["StatusGSI_PK"] = new() { S = "STATUS#DRAFT" },
                ["createdAt"]    = new() { S = now },
                ["updatedAt"]    = new() { S = now }
            };

            await _dynamo.PutItemAsync(new PutItemRequest
            {
                TableName = _tableName,
                Item      = item
            });

            context.Logger.LogInformation($"Expense {expenseId} created for user {userId}");

            return Ok(JsonConvert.SerializeObject(new
            {
                expenseId,
                status = "DRAFT",
                message = "Expense created successfully"
            }), 201);
        }
        catch (Exception ex)
        {
            context.Logger.LogError($"Error creating expense: {ex.Message}");
            return ServerError(ex.Message);
        }
    }

    // ── Helpers ──────────────────────────────────────────────────────────
    private static APIGatewayProxyResponse Ok(string body, int statusCode = 200) =>
        new() { StatusCode = statusCode, Body = body, Headers = CorsHeaders() };

    private static APIGatewayProxyResponse BadRequest(string msg) =>
        new() { StatusCode = 400, Body = $"{{\"error\":\"{msg}\"}}", Headers = CorsHeaders() };

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

public class CreateExpenseDto
{
    public decimal Amount { get; set; }
    public string Category { get; set; } = "";
    public string Description { get; set; } = "";
}
