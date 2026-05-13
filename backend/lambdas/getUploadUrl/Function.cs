using Amazon.DynamoDBv2;
using Amazon.DynamoDBv2.Model;
using Amazon.Lambda.APIGatewayEvents;
using Amazon.Lambda.Core;
using Amazon.S3;
using Amazon.S3.Model;
using Newtonsoft.Json;

[assembly: LambdaSerializer(typeof(Amazon.Lambda.Serialization.SystemTextJson.DefaultLambdaJsonSerializer))]

namespace GetUploadUrl;

public class Function
{
    private readonly IAmazonS3 _s3;
    private readonly IAmazonDynamoDB _dynamo;
    private readonly string _tableName;
    private readonly string _bucketName;

    public Function()
    {
        _s3         = new AmazonS3Client();
        _dynamo     = new AmazonDynamoDBClient();
        _tableName  = Environment.GetEnvironmentVariable("TABLE_NAME")  ?? "ExpenseReports";
        _bucketName = Environment.GetEnvironmentVariable("RECEIPTS_BUCKET") ?? "";
    }

    public async Task<APIGatewayProxyResponse> FunctionHandler(
        APIGatewayProxyRequest request, ILambdaContext context)
    {
        try
        {
            var claims    = request.RequestContext.Authorizer.Claims;
            var userId    = claims["sub"];
            var expenseId = request.PathParameters["expenseId"];

            // Vérifier que l'expense appartient bien à cet utilisateur
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

            // Clé S3 : receipts/{userId}/{expenseId}.jpg
            var s3Key = $"receipts/{userId}/{expenseId}.jpg";

            // Générer la pre-signed URL (valide 10 minutes)
            var presignRequest = new GetPreSignedUrlRequest
            {
                BucketName = _bucketName,
                Key        = s3Key,
                Verb       = HttpVerb.PUT,
                Expires    = DateTime.UtcNow.AddMinutes(10),
                ContentType = "image/jpeg"
            };

            var uploadUrl = _s3.GetPreSignedURL(presignRequest);

            // Sauvegarder la clé S3 dans DynamoDB pour pouvoir récupérer le reçu plus tard
            await _dynamo.UpdateItemAsync(new UpdateItemRequest
            {
                TableName        = _tableName,
                Key = new()
                {
                    ["PK"] = new() { S = $"USER#{userId}" },
                    ["SK"] = new() { S = $"EXPENSE#{expenseId}" }
                },
                UpdateExpression          = "SET receiptKey = :k, updatedAt = :ts",
                ExpressionAttributeValues = new()
                {
                    [":k"]  = new() { S = s3Key },
                    [":ts"] = new() { S = DateTime.UtcNow.ToString("o") }
                }
            });

            context.Logger.LogInformation(
                $"Pre-signed URL generated for expense {expenseId}, key: {s3Key}");

            return Ok(JsonConvert.SerializeObject(new
            {
                uploadUrl,
                key       = s3Key,
                expiresIn = "10 minutes"
            }));
        }
        catch (Exception ex)
        {
            context.Logger.LogError($"Error generating upload URL: {ex.Message}");
            return ServerError(ex.Message);
        }
    }

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
