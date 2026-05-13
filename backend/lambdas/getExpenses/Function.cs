using Amazon.DynamoDBv2;
using Amazon.DynamoDBv2.Model;
using Amazon.Lambda.APIGatewayEvents;
using Amazon.Lambda.Core;
using Newtonsoft.Json;

[assembly: LambdaSerializer(typeof(Amazon.Lambda.Serialization.SystemTextJson.DefaultLambdaJsonSerializer))]

namespace GetExpenses;

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
            var userId = claims["sub"];

            List<Dictionary<string, object>> results;

            if (IsFinanceManager(claims))
            {
                // Finance Manager → toutes les expenses SUBMITTED (via GSI StatusIndex)
                results = await QueryByStatus("SUBMITTED");
            }
            else
            {
                // Employé → ses propres expenses (query sur PK)
                results = await QueryByUser(userId);
            }

            return Ok(JsonConvert.SerializeObject(new { expenses = results }));
        }
        catch (Exception ex)
        {
            context.Logger.LogError($"Error fetching expenses: {ex.Message}");
            return ServerError(ex.Message);
        }
    }

    // Query toutes les expenses d'un user via la table principale
    private async Task<List<Dictionary<string, object>>> QueryByUser(string userId)
    {
        var response = await _dynamo.QueryAsync(new QueryRequest
        {
            TableName              = _tableName,
            KeyConditionExpression = "PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues = new()
            {
                [":pk"]        = new() { S = $"USER#{userId}" },
                [":sk_prefix"] = new() { S = "EXPENSE#" }
            },
            ScanIndexForward = false  // tri décroissant (plus récent en premier)
        });

        return response.Items.Select(MapItem).ToList();
    }

    // Query toutes les expenses par statut via le GSI StatusIndex
    private async Task<List<Dictionary<string, object>>> QueryByStatus(string status)
    {
        var response = await _dynamo.QueryAsync(new QueryRequest
        {
            TableName              = _tableName,
            IndexName              = "StatusIndex",
            KeyConditionExpression = "StatusGSI_PK = :gsi",
            ExpressionAttributeValues = new()
            {
                [":gsi"] = new() { S = $"STATUS#{status}" }
            }
        });

        return response.Items.Select(MapItem).ToList();
    }

    // Convertit un item DynamoDB en dict simple pour la sérialisation JSON
    private static Dictionary<string, object> MapItem(Dictionary<string, AttributeValue> item)
    {
        var result = new Dictionary<string, object>();

        foreach (var (key, val) in item)
        {
            if (val.S  != null) result[key] = val.S;
            else if (val.N != null) result[key] = decimal.Parse(val.N);
            else if (val.BOOL) result[key] = val.BOOL;
        }

        return result;
    }

    private static bool IsFinanceManager(IDictionary<string, string> claims)
    {
        if (claims.TryGetValue("cognito:groups", out var groups))
            return groups.Contains("finance");
        return false;
    }

    private static APIGatewayProxyResponse Ok(string body) =>
        new() { StatusCode = 200, Body = body, Headers = CorsHeaders() };

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
