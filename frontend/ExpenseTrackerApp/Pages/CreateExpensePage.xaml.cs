using ExpenseTrackerApp.Services;

namespace ExpenseTrackerApp.Pages;

public partial class CreateExpensePage : ContentPage
{
    private readonly ExpenseService _service = new();
    private FileResult? _selectedFile;

    public CreateExpensePage() => InitializeComponent();

    // ── Choisir une photo ────────────────────────────────────────────────────

    private async void OnPickFileClicked(object sender, EventArgs e)
    {
        try
        {
            var options = new PickOptions
            {
                PickerTitle = "Choisir un reçu",
                FileTypes    = FilePickerFileType.Images
            };

            var result = await FilePicker.PickAsync(options);
            if (result != null)
            {
                _selectedFile       = result;
                FileNameLabel.Text      = $"✅ {result.FileName}";
                FileNameLabel.TextColor = Color.FromArgb("#276749");
            }
        }
        catch (Exception ex)
        {
            await DisplayAlert("Erreur", $"Impossible de choisir le fichier : {ex.Message}", "OK");
        }
    }

    // ── Enregistrer ─────────────────────────────────────────────────────────

    private async void OnSaveDraftClicked(object sender, EventArgs e)
    {
        // Validation
        if (!decimal.TryParse(AmountEntry.Text, out var amount) || amount <= 0)
        {
            ShowError("Veuillez entrer un montant valide.");
            return;
        }
        if (CategoryPicker.SelectedItem == null)
        {
            ShowError("Veuillez sélectionner une catégorie.");
            return;
        }
        if (string.IsNullOrWhiteSpace(DescriptionEditor.Text))
        {
            ShowError("Veuillez entrer une description.");
            return;
        }

        SetLoading(true);

        try
        {
            // Étape 1 — Créer la note (DRAFT)
            var expenseId = await _service.CreateExpenseAsync(
                amount,
                CategoryPicker.SelectedItem.ToString()!,
                DescriptionEditor.Text.Trim());

            if (expenseId == null)
            {
                ShowError("Impossible de créer la note. Réessayez.");
                return;
            }

            // Étape 2 — Upload du reçu si un fichier a été sélectionné
            if (_selectedFile != null)
            {
                FileNameLabel.Text      = "⏳ Upload en cours...";
                FileNameLabel.TextColor = Color.FromArgb("#DD6B20");

                var uploadUrl = await _service.GetUploadUrlAsync(expenseId);

                if (uploadUrl != null)
                {
                    using var stream = await _selectedFile.OpenReadAsync();
                    var uploaded = await _service.UploadReceiptAsync(uploadUrl, stream);

                    FileNameLabel.Text      = uploaded ? "✅ Reçu uploadé !" : "⚠️ Upload échoué";
                    FileNameLabel.TextColor = uploaded
                        ? Color.FromArgb("#276749")
                        : Color.FromArgb("#C53030");
                }
                else
                {
                    FileNameLabel.Text      = "⚠️ URL upload indisponible";
                    FileNameLabel.TextColor = Color.FromArgb("#C53030");
                }
            }

            await DisplayAlert("Enregistré ✅", "Note créée avec succès.", "OK");
            await Shell.Current.GoToAsync("..");
        }
        catch (Exception ex)
        {
            ShowError($"Erreur : {ex.Message}");
        }
        finally
        {
            SetLoading(false);
        }
    }

    private async void OnCancelClicked(object sender, EventArgs e)
        => await Shell.Current.GoToAsync("..");

    private void ShowError(string msg)
    {
        ErrorLabel.Text      = msg;
        ErrorLabel.IsVisible = true;
    }

    private void SetLoading(bool loading)
    {
        Loader.IsVisible     = loading;
        Loader.IsRunning     = loading;
        ErrorLabel.IsVisible = false;
    }
}
