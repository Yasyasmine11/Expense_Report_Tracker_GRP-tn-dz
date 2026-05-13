using ExpenseTrackerApp.Models;
using ExpenseTrackerApp.Services;

namespace ExpenseTrackerApp.Pages;

public partial class EmployeePage : ContentPage
{
    private readonly ExpenseService _service = new();
    private List<ExpenseReport> _expenses    = new();

    public EmployeePage() => InitializeComponent();

    protected override async void OnAppearing()
    {
        base.OnAppearing();
        var email = AuthService.GetUserEmail() ?? "";
        if (!string.IsNullOrEmpty(email))
            WelcomeLabel.Text = $"Bonjour, {email.Split('@')[0]} 👋";

        await LoadExpensesAsync();
    }

    private async Task LoadExpensesAsync()
    {
        try
        {
            _expenses = await _service.GetMyExpensesAsync();
            ExpensesList.ItemsSource = _expenses;
            UpdateStats();
        }
        catch (Exception ex)
        {
            await DisplayAlert("Erreur", $"Impossible de charger les notes : {ex.Message}", "OK");
        }
        finally
        {
            RefreshView.IsRefreshing = false;
        }
    }

    private void UpdateStats()
    {
        DraftCount.Text     = _expenses.Count(e => e.Status == "DRAFT").ToString();
        SubmittedCount.Text = _expenses.Count(e => e.Status == "SUBMITTED").ToString();
        ApprovedCount.Text  = _expenses.Count(e => e.Status == "APPROVED").ToString();

        var total = _expenses.Where(e => e.Status == "APPROVED").Sum(e => e.Amount);
        TotalLabel.Text = $"€{total:F2}";
    }

    private async void OnCreateClicked(object sender, EventArgs e)
        => await Shell.Current.GoToAsync(nameof(CreateExpensePage));

    private async void OnSubmitClicked(object sender, EventArgs e)
    {
        if (sender is not Button btn || btn.CommandParameter is not string expenseId) return;

        bool confirm = await DisplayAlert(
            "Soumettre",
            "Soumettre cette note pour approbation ?",
            "Soumettre", "Annuler");

        if (!confirm) return;

        var ok = await _service.SubmitExpenseAsync(expenseId);

        await DisplayAlert(
            ok ? "Soumise ✅" : "Erreur",
            ok ? "Note soumise avec succès." : "Impossible de soumettre.",
            "OK");

        if (ok) await LoadExpensesAsync();
    }

    private async void OnRefresh(object sender, EventArgs e) => await LoadExpensesAsync();

    private async void OnLogoutClicked(object sender, EventArgs e)
    {
        await new AuthService().LogoutAsync();
        await Shell.Current.GoToAsync("//LoginPage");
    }
}
