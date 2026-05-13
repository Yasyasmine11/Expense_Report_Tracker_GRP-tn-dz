namespace ExpenseTrackerApp.Models;

public class ExpenseReport
{
    public string ExpenseId   { get; set; } = "";
    public string UserId      { get; set; } = "";
    public string UserEmail   { get; set; } = "";
    public decimal Amount     { get; set; }
    public string Category    { get; set; } = "";
    public string Description { get; set; } = "";
    public string Status      { get; set; } = "";
    public string ReceiptKey  { get; set; } = "";
    public string Justification { get; set; } = "";
    public string CreatedAt   { get; set; } = "";
    public string UpdatedAt   { get; set; } = "";

    // Propriétés calculées pour l'UI
    public string StatusBadge => Status switch
    {
        "DRAFT"     => "📝 Draft",
        "SUBMITTED" => "📤 Submitted",
        "APPROVED"  => "✅ Approved",
        "REJECTED"  => "❌ Rejected",
        _           => Status
    };

    public Color StatusColor => Status switch
    {
        "DRAFT"     => Colors.Gray,
        "SUBMITTED" => Colors.Orange,
        "APPROVED"  => Colors.Green,
        "REJECTED"  => Colors.Red,
        _           => Colors.Gray
    };

    public bool CanSubmit     => Status == "DRAFT" || Status == "REJECTED";
    public bool CanUploadReceipt => Status == "DRAFT";
    public string AmountFormatted => $"€{Amount:F2}";
}

public class LoginResult
{
    public bool   Success         { get; set; }
    public string AccessToken     { get; set; } = "";
    public string IdToken         { get; set; } = "";
    public bool   IsFinanceManager { get; set; }
    public string Email           { get; set; } = "";
    public string UserId          { get; set; } = "";
    public string ErrorMessage    { get; set; } = "";
}
