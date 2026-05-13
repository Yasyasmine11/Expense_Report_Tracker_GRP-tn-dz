using ExpenseTrackerApp.Models;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace ExpenseTrackerApp.Services;

public class ExpenseService
{
    private readonly HttpClient _http;

    public ExpenseService()
    {
        // BaseAddress MUST end with '/' so relative paths resolve under /prod/
        _http = new HttpClient { BaseAddress = new Uri(AppConfig.ApiBaseUrl) };
    }

    // Attach IdToken — Cognito authorizer passes sub + cognito:groups to Lambda
    private void Auth()
    {
        var token = AuthService.GetIdToken();
        if (!string.IsNullOrEmpty(token))
            _http.DefaultRequestHeaders.Authorization =
                new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", token);
    }

    // ── Employee ─────────────────────────────────────────────────────────────

    public async Task<List<ExpenseReport>> GetMyExpensesAsync()
    {
        Auth();
        var response = await _http.GetStringAsync("expenses");   // no leading /
        var json     = JObject.Parse(response);
        return json["expenses"]?.ToObject<List<ExpenseReport>>() ?? new();
    }

    public async Task<string?> CreateExpenseAsync(decimal amount, string category, string description)
    {
        Auth();
        var body    = JsonConvert.SerializeObject(new { amount, category, description });
        var content = new StringContent(body, System.Text.Encoding.UTF8, "application/json");
        var resp    = await _http.PostAsync("expenses", content);   // no leading /

        if (!resp.IsSuccessStatusCode)
        {
            var err = await resp.Content.ReadAsStringAsync();
            throw new Exception($"{(int)resp.StatusCode}: {err}");
        }

        var json = JObject.Parse(await resp.Content.ReadAsStringAsync());
        return json["expenseId"]?.ToString();
    }

    public async Task<bool> SubmitExpenseAsync(string expenseId)
    {
        Auth();
        var resp = await _http.PostAsync($"expenses/{expenseId}/submit", null);
        return resp.IsSuccessStatusCode;
    }

    public async Task<string?> GetUploadUrlAsync(string expenseId)
    {
        Auth();
        var response = await _http.GetStringAsync($"expenses/{expenseId}/upload-url");
        var json     = JObject.Parse(response);
        return json["uploadUrl"]?.ToString();
    }

    public async Task<bool> UploadReceiptAsync(string presignedUrl, Stream imageStream)
    {
        using var uploadClient = new HttpClient();
        var content = new StreamContent(imageStream);
        content.Headers.ContentType =
            new System.Net.Http.Headers.MediaTypeHeaderValue("image/jpeg");
        var response = await uploadClient.PutAsync(presignedUrl, content);
        return response.IsSuccessStatusCode;
    }

    // ── Finance Manager ───────────────────────────────────────────────────────

    public async Task<List<ExpenseReport>> GetPendingExpensesAsync()
    {
        Auth();
        var response = await _http.GetStringAsync("expenses");   // no leading /
        var json     = JObject.Parse(response);
        return json["expenses"]?.ToObject<List<ExpenseReport>>() ?? new();
    }

    public async Task<bool> ApproveExpenseAsync(string expenseId, string userId)
    {
        Auth();
        var body    = JsonConvert.SerializeObject(new { userId });
        var content = new StringContent(body, System.Text.Encoding.UTF8, "application/json");
        var resp    = await _http.PostAsync($"expenses/{expenseId}/approve", content);
        return resp.IsSuccessStatusCode;
    }

    public async Task<bool> RejectExpenseAsync(string expenseId, string userId, string justification)
    {
        Auth();
        var body    = JsonConvert.SerializeObject(new { userId, justification });
        var content = new StringContent(body, System.Text.Encoding.UTF8, "application/json");
        var resp    = await _http.PostAsync($"expenses/{expenseId}/reject", content);
        return resp.IsSuccessStatusCode;
    }
}
