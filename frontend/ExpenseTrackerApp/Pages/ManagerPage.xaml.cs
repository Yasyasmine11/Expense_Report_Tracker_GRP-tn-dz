using ExpenseTrackerApp.Models;
using ExpenseTrackerApp.Services;

namespace ExpenseTrackerApp.Pages;

public partial class ManagerPage : ContentPage
{
    private readonly ExpenseService _service = new();
    private List<ExpenseReport> _pending     = new();

    public ManagerPage() => InitializeComponent();

    protected override async void OnAppearing()
    {
        base.OnAppearing();
        await LoadPendingAsync();
    }

    private async Task LoadPendingAsync()
    {
        try
        {
            _pending = await _service.GetPendingExpensesAsync();
            PendingList.ItemsSource = _pending;
            PendingCountLabel.Text  =
                $"{_pending.Count} expense{(_pending.Count != 1 ? "s" : "")} waiting for review";
        }
        catch (Exception ex)
        {
            await DisplayAlert("Error", $"Could not load pending expenses: {ex.Message}", "OK");
        }
        finally
        {
            RefreshView.IsRefreshing = false;
        }
    }

    private async void OnApproveClicked(object sender, EventArgs e)
    {
        if (sender is not Button btn || btn.CommandParameter is not ExpenseReport expense)
            return;

        bool confirm = await DisplayAlert(
            "Approve Expense",
            $"Approve €{expense.Amount:F2} — \"{expense.Description}\"?",
            "Approve", "Cancel");

        if (!confirm) return;

        var ok = await _service.ApproveExpenseAsync(expense.ExpenseId, expense.UserId);

        await DisplayAlert(
            ok ? "Approved" : "Error",
            ok ? "Expense approved successfully." : "Failed to approve expense.",
            "OK");

        if (ok) await LoadPendingAsync();
    }

    private async void OnRejectClicked(object sender, EventArgs e)
    {
        if (sender is not Button btn || btn.CommandParameter is not ExpenseReport expense)
            return;

        // Demander la justification via une popup
        var justification = await DisplayPromptAsync(
            "Reject Expense",
            "Please provide a justification for the rejection:",
            placeholder: "e.g. Receipt missing, policy violation...",
            maxLength: 300);

        if (string.IsNullOrWhiteSpace(justification))
        {
            await DisplayAlert("Required", "A justification is required to reject an expense.", "OK");
            return;
        }

        var ok = await _service.RejectExpenseAsync(
            expense.ExpenseId, expense.UserId, justification);

        await DisplayAlert(
            ok ? "Rejected" : "Error",
            ok ? "Expense rejected." : "Failed to reject expense.",
            "OK");

        if (ok) await LoadPendingAsync();
    }

    private async void OnRefresh(object sender, EventArgs e)
    {
        await LoadPendingAsync();
    }

    private async void OnLogoutClicked(object sender, EventArgs e)
    {
        await new AuthService().LogoutAsync();
        await Shell.Current.GoToAsync("//LoginPage");
    }
}
