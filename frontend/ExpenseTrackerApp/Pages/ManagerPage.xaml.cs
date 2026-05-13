using ExpenseTrackerApp.Models;
using ExpenseTrackerApp.Services;

namespace ExpenseTrackerApp.Pages;

public partial class ManagerPage : ContentPage
{
    private readonly ExpenseService _service = new();
    private List<ExpenseReport> _all = new();

    public ManagerPage() => InitializeComponent();

    protected override async void OnAppearing()
    {
        base.OnAppearing();
        await LoadExpensesAsync();
    }

    private async Task LoadExpensesAsync()
    {
        try
        {
            _all = await _service.GetPendingExpensesAsync();
            ExpenseList.ItemsSource = _all;

            SubmittedCountLabel.Text = _all.Count(e => e.Status == "SUBMITTED").ToString();
            ApprovedCountLabel.Text  = _all.Count(e => e.Status == "APPROVED").ToString();
            RejectedCountLabel.Text  = _all.Count(e => e.Status == "REJECTED").ToString();
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

    private async void OnApproveClicked(object sender, EventArgs e)
    {
        if (sender is not Button btn || btn.CommandParameter is not ExpenseReport expense) return;

        bool confirm = await DisplayAlert(
            "Approuver",
            $"Approuver {expense.AmountFormatted} — \"{expense.Description}\" ?",
            "Approuver", "Annuler");

        if (!confirm) return;

        var ok = await _service.ApproveExpenseAsync(expense.ExpenseId, expense.UserId);

        await DisplayAlert(
            ok ? "Approuvée ✅" : "Erreur",
            ok ? "Note de frais approuvée." : "Impossible d'approuver.",
            "OK");

        if (ok) await LoadExpensesAsync();
    }

    private async void OnRejectClicked(object sender, EventArgs e)
    {
        if (sender is not Button btn || btn.CommandParameter is not ExpenseReport expense) return;

        var justification = await DisplayPromptAsync(
            "Motif du rejet",
            "Veuillez indiquer la raison du rejet :",
            placeholder: "Ex : Reçu manquant, non conforme à la politique...",
            maxLength: 300);

        if (string.IsNullOrWhiteSpace(justification))
        {
            await DisplayAlert("Requis", "Un motif est obligatoire pour rejeter.", "OK");
            return;
        }

        var ok = await _service.RejectExpenseAsync(expense.ExpenseId, expense.UserId, justification);

        await DisplayAlert(
            ok ? "Rejetée ❌" : "Erreur",
            ok ? "Note de frais rejetée." : "Impossible de rejeter.",
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
