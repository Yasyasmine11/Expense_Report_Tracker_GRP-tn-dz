using Amazon.DynamoDBv2;
using Amazon.DynamoDBv2.Model;
using Amazon.Lambda.APIGatewayEvents;
using Amazon.Lambda.Core;
using Newtonsoft.Json;

[assembly: LambdaSerializer(typeof(Amazon.Lambda.Serialization.SystemTextJson.DefaultLambdaJsonSerializer))]

namespace GetExpenseById;

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
            var callerId  = claims["sub"];
            var expenseId = request.PathParameters["expenseId"];

            // Finance manager peut voir n'importe quelle expense
            // Employee ne peut voir que les siennes (userId en query param ou claim)
            string userId;
            if (IsFinanceManager(claims))
            {
                // Le manager fournit le userId en query string ou on cherche par expenseId via scan
                // Pour simplifier: le manager passe ?userId=xxx OU on retourne l'item via GSI
                userId = request.QueryStringParameters != null &&
                         request.QueryStringParameters.TryGetValue("userId", out var qUid)
                    ? qUid
                    : callerId;
            }
            else
            {
                userId = callerId;
            }

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

            var item = MapItem(getResult.Item);
            return Ok(JsonConvert.SerializeObject(item));
        }
        catch (Exception ex)
        {
            context.Logger.LogError($"Error fetching expense: {ex.Message}");
            return ServerError(ex.Message);
        }
    }

    private static Dictionary<string, object> MapItem(Dictionary<string, AttributeValue> item)
    {
        var result = new Dictionary<string, object>();
        foreach (var (key, val) in item)
        {
            if      (val.S    != null) result[key] = val.S;
            else if (val.N    != null) result[key] = decimal.Parse(val.N);
            else if (val.IsBOOLSet)    result[key] = val.BOOL;
        }
        return result;
    }

    private static bool IsFinanceManager(IDictionary<string, string> claims) =>
        claims.TryGetValue("cognito:groups", out var groups) && groups.Contains("finance");

    private static APIGatewayProxyResponse Ok(string body) =>
        new() { StatusCode = 200, Body = body, Headers = CorsHeaders() };

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
