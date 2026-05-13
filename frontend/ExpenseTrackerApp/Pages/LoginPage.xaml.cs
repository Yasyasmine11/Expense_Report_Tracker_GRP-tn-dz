using ExpenseTrackerApp.Services;

namespace ExpenseTrackerApp.Pages;

public partial class LoginPage : ContentPage
{
    private readonly AuthService _auth = new();

    public LoginPage() => InitializeComponent();

    private async void OnLoginClicked(object sender, EventArgs e)
    {
        if (string.IsNullOrWhiteSpace(EmailEntry.Text) ||
            string.IsNullOrWhiteSpace(PasswordEntry.Text))
        {
            ShowError("Please enter your email and password.");
            return;
        }

        SetLoading(true);

        var result = await _auth.LoginAsync(
            EmailEntry.Text.Trim(),
            PasswordEntry.Text);

        SetLoading(false);

        if (!result.Success)
        {
            ShowError(result.ErrorMessage);
            return;
        }

        // Rediriger selon le rôle
        if (result.IsFinanceManager)
            await Shell.Current.GoToAsync("//ManagerPage");
        else
            await Shell.Current.GoToAsync("//EmployeePage");
    }

    private void ShowError(string msg)
    {
        ErrorLabel.Text      = msg;
        ErrorLabel.IsVisible = true;
    }

    private void SetLoading(bool loading)
    {
        Loader.IsVisible     = loading;
        Loader.IsRunning     = loading;
        LoginButton.IsEnabled = !loading;
        ErrorLabel.IsVisible  = false;
    }
}
