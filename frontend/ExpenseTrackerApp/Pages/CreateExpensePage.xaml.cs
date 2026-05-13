using ExpenseTrackerApp.Services;

namespace ExpenseTrackerApp.Pages;

public partial class CreateExpensePage : ContentPage
{
    private readonly ExpenseService _service = new();

    public CreateExpensePage() => InitializeComponent();

    private async void OnSaveDraftClicked(object sender, EventArgs e)
    {
        // Validation
        if (!decimal.TryParse(AmountEntry.Text, out var amount) || amount <= 0)
        {
            ShowError("Please enter a valid amount.");
            return;
        }
        if (CategoryPicker.SelectedItem == null)
        {
            ShowError("Please select a category.");
            return;
        }
        if (string.IsNullOrWhiteSpace(DescriptionEditor.Text))
        {
            ShowError("Please enter a description.");
            return;
        }

        SetLoading(true);

        var expenseId = await _service.CreateExpenseAsync(
            amount,
            CategoryPicker.SelectedItem.ToString()!,
            DescriptionEditor.Text.Trim());

        SetLoading(false);

        if (expenseId != null)
        {
            await DisplayAlert("Saved!", "Expense saved as draft.", "OK");
            await Shell.Current.GoToAsync("..");  // retour à EmployeePage
        }
        else
        {
            ShowError("Failed to create expense. Please try again.");
        }
    }

    private async void OnCancelClicked(object sender, EventArgs e)
    {
        await Shell.Current.GoToAsync("..");
    }

    private void ShowError(string msg)
    {
        ErrorLabel.Text      = msg;
        ErrorLabel.IsVisible = true;
    }

    private void SetLoading(bool loading)
    {
        Loader.IsVisible  = loading;
        Loader.IsRunning  = loading;
        ErrorLabel.IsVisible = false;
    }
}
