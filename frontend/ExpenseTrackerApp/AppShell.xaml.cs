namespace ExpenseTrackerApp;

public partial class AppShell : Shell
{
    public AppShell()
    {
        InitializeComponent();

        Routing.RegisterRoute(nameof(Pages.CreateExpensePage),
            typeof(Pages.CreateExpensePage));
    }
}
