namespace ExpenseTracker.Shared.Models
{
    public class ExpenseReport
    {
        public string ExpenseId { get; set; }
        public string UserId { get; set; }
        public string UserEmail { get; set; }
        public decimal Amount { get; set; }
        public string Category { get; set; }
        public string Description { get; set; }
        public string Status { get; set; }
        public string ReceiptKey { get; set; }
        public string Justification { get; set; }
        public string CreatedAt { get; set; }
        public string UpdatedAt { get; set; }
    }

    // Statuts possibles (state machine)
    public static class ExpenseStatus
    {
        public const string Draft      = "DRAFT";
        public const string Submitted  = "SUBMITTED";
        public const string Approved   = "APPROVED";
        public const string Rejected   = "REJECTED";
    }

    // Catégories
    public static class ExpenseCategory
    {
        public const string Travel    = "TRAVEL";
        public const string Meal      = "MEAL";
        public const string Equipment = "EQUIPMENT";
        public const string Other     = "OTHER";
    }
}

namespace ExpenseTracker.Shared.DTOs
{
    public class CreateExpenseDto
    {
        public decimal Amount { get; set; }
        public string Category { get; set; }
        public string Description { get; set; }
    }

    public class ReviewDto
    {
        public string UserId { get; set; }
        public string ExpenseId { get; set; }
        public string Decision { get; set; }   // "APPROVED" ou "REJECTED"
        public string Justification { get; set; }
    }

    public class ApiResponse<T>
    {
        public bool Success { get; set; }
        public string Message { get; set; }
        public T Data { get; set; }

        public static ApiResponse<T> Ok(T data, string message = "Success") =>
            new() { Success = true, Message = message, Data = data };

        public static ApiResponse<T> Fail(string message) =>
            new() { Success = false, Message = message, Data = default };
    }
}
