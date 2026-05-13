using ExpenseTrackerApp.Models;
using ExpenseTrackerApp.Services;

namespace ExpenseTrackerApp.Pages;

public partial class EmployeePage : ContentPage
{
    private readonly ExpenseService _service = new();
    private List<ExpenseReport> _expenses    = new();

    public EmployeePage()
    {
        InitializeComponent();
    }

    protected override async void OnAppearing()
    {
        base.OnAppearing();
        await LoadExpensesAsync();
    }

    private async Task LoadExpensesAsync()
    {
        try
        {
            _expenses            = await _service.GetMyExpensesAsync();
            ExpensesList.ItemsSource = _expenses;
            UpdateStats();
        }
        catch (Exception ex)
        {
            await DisplayAlert("Error", $"Could not load expenses: {ex.Message}", "OK");
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
    }

    private async void OnCreateClicked(object sender, EventArgs e)
    {
        await Shell.Current.GoToAsync(nameof(CreateExpensePage));
    }

    private async void OnSubmitClicked(object sender, EventArgs e)
    {
        if (sender is Button btn && btn.CommandParameter is string expenseId)
        {
            bool confirm = await DisplayAlert(
                "Submit Expense",
                "Are you sure you want to submit this expense for approval?",
                "Submit", "Cancel");

            if (!confirm) return;

            var success = await _service.SubmitExpenseAsync(expenseId);

            if (success)
            {
                await DisplayAlert("Success", "Expense submitted successfully!", "OK");
                await LoadExpensesAsync();
            }
            else
            {
                await DisplayAlert("Error", "Could not submit expense.", "OK");
            }
        }
    }

    private async void OnUploadReceiptClicked(object sender, EventArgs e)
    {
        if (sender is Button btn && btn.CommandParameter is string expenseId)
        {
            try
            {
                // Prendre une photo ou choisir depuis la galerie
                var photo = await MediaPicker.PickPhotoAsync();
                if (photo == null) return;

                // Obtenir la pre-signed URL depuis Lambda
                var uploadUrl = await _service.GetUploadUrlAsync(expenseId);
                if (uploadUrl == null)
                {
                    await DisplayAlert("Error", "Could not get upload URL.", "OK");
                    return;
                }

                // Upload direct sur S3
                using var stream = await photo.OpenReadAsync();
                var ok = await _service.UploadReceiptAsync(uploadUrl, stream);

                await DisplayAlert(
                    ok ? "Success" : "Error",
                    ok ? "Receipt uploaded successfully!" : "Upload failed.",
                    "OK");
            }
            catch (Exception ex)
            {
                await DisplayAlert("Error", ex.Message, "OK");
            }
        }
    }

    private async void OnRefresh(object sender, EventArgs e)
    {
        await LoadExpensesAsync();
    }

    private async void OnLogoutClicked(object sender, EventArgs e)
    {
        await new AuthService().LogoutAsync();
        await Shell.Current.GoToAsync("//LoginPage");
    }
}
