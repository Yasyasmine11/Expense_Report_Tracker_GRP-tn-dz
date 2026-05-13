namespace ExpenseTrackerApp.Models;

public class ExpenseReport
{
    public string  ExpenseId     { get; set; } = "";
    public string  UserId        { get; set; } = "";
    public string  UserEmail     { get; set; } = "";
    public decimal Amount        { get; set; }
    public string  Category      { get; set; } = "";
    public string  Description   { get; set; } = "";
    public string  Status        { get; set; } = "";
    public string  ReceiptKey    { get; set; } = "";
    public string  Justification { get; set; } = "";
    public string  ReviewedBy    { get; set; } = "";
    public string  CreatedAt     { get; set; } = "";
    public string  UpdatedAt     { get; set; } = "";

    // ── Propriétés calculées pour l'UI ───────────────────────────────────────

    public string AmountFormatted => $"€{Amount:F2}";

    public string StatusLabel => Status switch
    {
        "DRAFT"     => "Brouillon",
        "SUBMITTED" => "En attente",
        "APPROVED"  => "Approuvée",
        "REJECTED"  => "Rejetée",
        _           => Status
    };

    // Texte de la couleur en string (MAUI binding depuis DataTemplate)
    public Color StatusColor => Status switch
    {
        "DRAFT"     => Color.FromArgb("#718096"),
        "SUBMITTED" => Color.FromArgb("#DD6B20"),
        "APPROVED"  => Color.FromArgb("#276749"),
        "REJECTED"  => Color.FromArgb("#9B2C2C"),
        _           => Color.FromArgb("#718096")
    };

    public Color StatusBgColor => Status switch
    {
        "DRAFT"     => Color.FromArgb("#EDF2F7"),
        "SUBMITTED" => Color.FromArgb("#FEEBC8"),
        "APPROVED"  => Color.FromArgb("#C6F6D5"),
        "REJECTED"  => Color.FromArgb("#FED7D7"),
        _           => Color.FromArgb("#EDF2F7")
    };

    // Actions disponibles
    public bool CanSubmit        => Status == "DRAFT" || Status == "REJECTED";
    public bool CanUploadReceipt => Status == "DRAFT";
    public bool CanReview        => Status == "SUBMITTED";

    // Visibilité
    public bool HasJustification => !string.IsNullOrWhiteSpace(Justification);
}

public class LoginResult
{
    public bool   Success          { get; set; }
    public string IdToken          { get; set; } = "";
    public bool   IsFinanceManager { get; set; }
    public string Email            { get; set; } = "";
    public string UserId           { get; set; } = "";
    public string ErrorMessage     { get; set; } = "";
}
