using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Windows.Forms;

namespace SSeriesExplorer;

public sealed class MainForm : Form
{
    public const string Version = "1.0.0";

    private readonly TextBox _address = new() { Anchor = AnchorStyles.Left | AnchorStyles.Right, Font = new Font("Segoe UI", 10) };
    private readonly TextBox _filter = new() { Width = 260, PlaceholderText = "Filter über alle Spalten" };
    private readonly ComboBox _mode = new() { DropDownStyle = ComboBoxStyle.DropDownList, Width = 210 };
    private readonly DataGridView _grid = new() { Dock = DockStyle.Fill, AllowUserToAddRows = false, AllowUserToDeleteRows = false, ReadOnly = true, SelectionMode = DataGridViewSelectionMode.FullRowSelect, MultiSelect = true, AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.None };
    private readonly StatusStrip _status = new();
    private readonly ToolStripStatusLabel _statusText = new("Bereit");
    private readonly List<FileRow> _rows = new();
    private readonly Stack<string> _back = new();
    private readonly Stack<string> _forward = new();
    private string _currentFolder = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
    private string? _clipboardPath;
    private bool _clipboardCut;

    public MainForm()
    {
        Text = $"S-Series Explorer {Version} - C#";
        Width = 1500;
        Height = 850;
        MinimumSize = new Size(980, 620);
        StartPosition = FormStartPosition.CenterScreen;
        Font = new Font("Segoe UI", 10);
        BuildUi();
        Navigate(_currentFolder, false);
    }

    private void BuildUi()
    {
        var top = new TableLayoutPanel { Dock = DockStyle.Top, Height = 92, ColumnCount = 1, RowCount = 2, Padding = new Padding(8) };
        var nav = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 8 };
        nav.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));
        nav.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));
        nav.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));
        nav.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        nav.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));
        nav.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));
        nav.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));
        nav.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));
        nav.Controls.Add(Button("Zurück", (_, _) => GoBack()), 0, 0);
        nav.Controls.Add(Button("Vor", (_, _) => GoForward()), 1, 0);
        nav.Controls.Add(Button("Hoch", (_, _) => GoUp()), 2, 0);
        nav.Controls.Add(_address, 3, 0);
        nav.Controls.Add(Button("Los", (_, _) => NavigateFromAddress()), 4, 0);
        nav.Controls.Add(Button("Neu Ordner", (_, _) => CreateFolder()), 5, 0);
        nav.Controls.Add(Button("Export CSV", (_, _) => ExportCsv()), 6, 0);
        _address.KeyDown += (_, e) => { if (e.KeyCode == Keys.Enter) { NavigateFromAddress(); e.SuppressKeyPress = true; } };

        var tools = new FlowLayoutPanel { Dock = DockStyle.Fill, FlowDirection = FlowDirection.LeftToRight };
        _mode.Items.AddRange(new object[] { "Explorer: Ordner anzeigen", "Ordnervergleich" });
        _mode.SelectedIndex = 0;
        _mode.SelectedIndexChanged += (_, _) => { if (_mode.SelectedIndex == 1) CompareFolders(); };
        _filter.TextChanged += (_, _) => ApplyFilter();
        tools.Controls.Add(new Label { Text = "Funktion:", AutoSize = true, Padding = new Padding(0, 7, 4, 0) });
        tools.Controls.Add(_mode);
        tools.Controls.Add(new Label { Text = "Suche:", AutoSize = true, Padding = new Padding(14, 7, 4, 0) });
        tools.Controls.Add(_filter);
        tools.Controls.Add(Button("Aktualisieren", (_, _) => Navigate(_currentFolder, false)));
        tools.Controls.Add(Button("Vergleichen...", (_, _) => CompareFolders()));

        top.Controls.Add(nav, 0, 0);
        top.Controls.Add(tools, 0, 1);
        Controls.Add(_grid);
        Controls.Add(top);
        _status.Items.Add(_statusText);
        Controls.Add(_status);

        _grid.Columns.Add("Kind", "Objekt");
        _grid.Columns.Add("Name", "Name");
        for (int i = 1; i <= 12; i++) _grid.Columns.Add($"Seg{i}", $"Teil {i}");
        _grid.Columns.Add("Issue", "Ausgabe");
        _grid.Columns.Add("Language", "Sprache");
        _grid.Columns.Add("Corel", "Corel-DES-Version");
        _grid.Columns.Add("Size", "Größe");
        _grid.Columns.Add("Modified", "Geändert");
        _grid.Columns.Add("Status", "Vergleich");
        _grid.Columns.Add("Path", "Pfad");
        _grid.Columns[1].Width = 260;
        _grid.Columns[^1].Width = 420;
        _grid.CellDoubleClick += (_, e) => OpenSelected();
        _grid.KeyDown += GridKeyDown;
        _grid.ContextMenuStrip = BuildContextMenu();
    }

    private static Button Button(string text, EventHandler handler)
    {
        var button = new Button { Text = text, AutoSize = true, Margin = new Padding(3) };
        button.Click += handler;
        return button;
    }

    private ContextMenuStrip BuildContextMenu()
    {
        var menu = new ContextMenuStrip();
        menu.Items.Add("Öffnen", null, (_, _) => OpenSelected());
        menu.Items.Add("Kopieren", null, (_, _) => CopySelected(false));
        menu.Items.Add("Ausschneiden", null, (_, _) => CopySelected(true));
        menu.Items.Add("Einfügen", null, (_, _) => PasteClipboard());
        menu.Items.Add("Umbenennen", null, (_, _) => RenameSelected());
        menu.Items.Add("Löschen", null, (_, _) => DeleteSelected());
        menu.Items.Add("Neuer Ordner", null, (_, _) => CreateFolder());
        return menu;
    }

    private void GridKeyDown(object? sender, KeyEventArgs e)
    {
        if (e.KeyCode == Keys.Enter) { OpenSelected(); e.SuppressKeyPress = true; }
        if (e.KeyCode == Keys.Delete) DeleteSelected();
        if (e.KeyCode == Keys.F2) RenameSelected();
        if (e.Control && e.KeyCode == Keys.C) CopySelected(false);
        if (e.Control && e.KeyCode == Keys.X) CopySelected(true);
        if (e.Control && e.KeyCode == Keys.V) PasteClipboard();
    }

    private void NavigateFromAddress() => Navigate(_address.Text.Trim(), true);

    private void Navigate(string folder, bool remember)
    {
        if (!Directory.Exists(folder)) { MessageBox.Show("Ordner nicht gefunden."); return; }
        if (remember && !string.Equals(_currentFolder, folder, StringComparison.OrdinalIgnoreCase)) { _back.Push(_currentFolder); _forward.Clear(); }
        _currentFolder = Path.GetFullPath(folder);
        _address.Text = _currentFolder;
        _rows.Clear();
        foreach (string dir in Directory.EnumerateDirectories(_currentFolder).OrderBy(Path.GetFileName)) _rows.Add(FileRow.FromPath(dir, true, ""));
        foreach (string file in Directory.EnumerateFiles(_currentFolder).OrderBy(Path.GetFileName)) _rows.Add(FileRow.FromPath(file, false, ""));
        ApplyFilter();
        _statusText.Text = $"{_rows.Count} Objekte - {_currentFolder}";
    }

    private void ApplyFilter()
    {
        string term = _filter.Text.Trim();
        _grid.Rows.Clear();
        foreach (var row in _rows.Where(r => string.IsNullOrWhiteSpace(term) || r.SearchText.Contains(term, StringComparison.OrdinalIgnoreCase)))
        {
            int index = _grid.Rows.Add(row.ToCells());
            _grid.Rows[index].Tag = row;
            if (row.Status.Contains("Geändert")) _grid.Rows[index].DefaultCellStyle.BackColor = Color.MistyRose;
            if (row.Status.Contains("Nur")) _grid.Rows[index].DefaultCellStyle.BackColor = Color.LemonChiffon;
        }
    }

    private FileRow? SelectedRow() => _grid.CurrentRow?.Tag as FileRow;
    private void OpenSelected()
    {
        var row = SelectedRow();
        if (row is null) return;
        if (row.IsDirectory) Navigate(row.Path, true); else Process.Start(new ProcessStartInfo(row.Path) { UseShellExecute = true });
    }
    private void GoBack() { if (_back.TryPop(out var p)) { _forward.Push(_currentFolder); Navigate(p, false); } }
    private void GoForward() { if (_forward.TryPop(out var p)) { _back.Push(_currentFolder); Navigate(p, false); } }
    private void GoUp() { var parent = Directory.GetParent(_currentFolder); if (parent != null) Navigate(parent.FullName, true); }
    private void CopySelected(bool cut) { var row = SelectedRow(); if (row is null) return; _clipboardPath = row.Path; _clipboardCut = cut; _statusText.Text = cut ? "Ausgeschnitten" : "Kopiert"; }
    private void PasteClipboard()
    {
        if (_clipboardPath is null) return;
        string target = Path.Combine(_currentFolder, Path.GetFileName(_clipboardPath));
        target = UniquePath(target);
        if (Directory.Exists(_clipboardPath)) CopyDirectory(_clipboardPath, target); else File.Copy(_clipboardPath, target);
        if (_clipboardCut) { if (Directory.Exists(_clipboardPath)) Directory.Delete(_clipboardPath, true); else File.Delete(_clipboardPath); _clipboardPath = null; }
        Navigate(_currentFolder, false);
    }
    private void RenameSelected()
    {
        var row = SelectedRow(); if (row is null) return;
        string? name = Prompt("Neuer Name", Path.GetFileName(row.Path)); if (string.IsNullOrWhiteSpace(name)) return;
        string target = Path.Combine(Path.GetDirectoryName(row.Path)!, name);
        if (row.IsDirectory) Directory.Move(row.Path, target); else File.Move(row.Path, target);
        Navigate(_currentFolder, false);
    }
    private void DeleteSelected()
    {
        var row = SelectedRow(); if (row is null) return;
        if (MessageBox.Show($"'{Path.GetFileName(row.Path)}' löschen?", "Löschen", MessageBoxButtons.YesNo, MessageBoxIcon.Warning) != DialogResult.Yes) return;
        if (row.IsDirectory) Directory.Delete(row.Path, true); else File.Delete(row.Path);
        Navigate(_currentFolder, false);
    }
    private void CreateFolder()
    {
        string? name = Prompt("Ordnername", "Neuer Ordner"); if (string.IsNullOrWhiteSpace(name)) return;
        Directory.CreateDirectory(UniquePath(Path.Combine(_currentFolder, name)));
        Navigate(_currentFolder, false);
    }

    private void CompareFolders()
    {
        using var a = new FolderBrowserDialog { Description = "Ordner A wählen" };
        if (a.ShowDialog(this) != DialogResult.OK) return;
        using var b = new FolderBrowserDialog { Description = "Ordner B wählen" };
        if (b.ShowDialog(this) != DialogResult.OK) return;
        var mapA = Directory.EnumerateFiles(a.SelectedPath, "*", SearchOption.AllDirectories).ToDictionary(p => Path.GetRelativePath(a.SelectedPath, p), StringComparer.OrdinalIgnoreCase);
        var mapB = Directory.EnumerateFiles(b.SelectedPath, "*", SearchOption.AllDirectories).ToDictionary(p => Path.GetRelativePath(b.SelectedPath, p), StringComparer.OrdinalIgnoreCase);
        _rows.Clear();
        foreach (string rel in mapA.Keys.Concat(mapB.Keys).Distinct(StringComparer.OrdinalIgnoreCase).OrderBy(x => x))
        {
            bool inA = mapA.TryGetValue(rel, out var pa), inB = mapB.TryGetValue(rel, out var pb);
            string status = inA && inB ? (Sha256(pa!) == Sha256(pb!) ? "Identisch" : "Geändert") : inA ? "Nur Ordner A" : "Nur Ordner B";
            _rows.Add(FileRow.FromPath((inA ? pa : pb)!, false, status, rel));
        }
        _mode.SelectedIndex = 1;
        ApplyFilter();
        _statusText.Text = $"Vergleich: {_rows.Count} Dateien";
    }

    private void ExportCsv()
    {
        using var dialog = new SaveFileDialog { Filter = "CSV (*.csv)|*.csv", FileName = "s-series-export.csv" };
        if (dialog.ShowDialog(this) != DialogResult.OK) return;
        var lines = new List<string> { string.Join(';', _grid.Columns.Cast<DataGridViewColumn>().Select(c => Escape(c.HeaderText))) };
        foreach (DataGridViewRow row in _grid.Rows) lines.Add(string.Join(';', row.Cells.Cast<DataGridViewCell>().Select(c => Escape(c.Value?.ToString() ?? ""))));
        File.WriteAllLines(dialog.FileName, lines, Encoding.UTF8);
    }

    private static string Escape(string value) => '"' + value.Replace("\"", "\"\"") + '"';
    private static string Sha256(string path) { using var s = File.OpenRead(path); return Convert.ToHexString(SHA256.HashData(s)); }
    private static void CopyDirectory(string source, string target) { Directory.CreateDirectory(target); foreach (var file in Directory.GetFiles(source)) File.Copy(file, Path.Combine(target, Path.GetFileName(file))); foreach (var dir in Directory.GetDirectories(source)) CopyDirectory(dir, Path.Combine(target, Path.GetFileName(dir))); }
    private static string UniquePath(string path) { if (!File.Exists(path) && !Directory.Exists(path)) return path; string dir = Path.GetDirectoryName(path)!; string name = Path.GetFileNameWithoutExtension(path); string ext = Path.GetExtension(path); for (int i = 2; ; i++) { string candidate = Path.Combine(dir, $"{name} ({i}){ext}"); if (!File.Exists(candidate) && !Directory.Exists(candidate)) return candidate; } }

    private string? Prompt(string title, string defaultValue)
    {
        using var form = new Form { Text = title, Width = 420, Height = 140, StartPosition = FormStartPosition.CenterParent, FormBorderStyle = FormBorderStyle.FixedDialog, MinimizeBox = false, MaximizeBox = false };
        var input = new TextBox { Left = 12, Top = 12, Width = 380, Text = defaultValue };
        var ok = new Button { Text = "OK", DialogResult = DialogResult.OK, Left = 232, Top = 50 };
        var cancel = new Button { Text = "Abbrechen", DialogResult = DialogResult.Cancel, Left = 312, Top = 50 };
        form.Controls.AddRange(new Control[] { input, ok, cancel });
        form.AcceptButton = ok; form.CancelButton = cancel;
        return form.ShowDialog(this) == DialogResult.OK ? input.Text : null;
    }
}

internal sealed record FileRow(string Kind, string Name, string[] Segments, string Issue, string Language, string Corel, string Size, string Modified, string Status, string DisplayPath, string Path, bool IsDirectory)
{
    public string SearchText => string.Join(' ', ToCells());
    public object[] ToCells() => new object[] { Kind, Name }.Concat(Segments).Concat(new object[] { Issue, Language, Corel, Size, Modified, Status, DisplayPath }).ToArray();

    public static FileRow FromPath(string path, bool isDirectory, string status, string? displayPath = null)
    {
        string name = System.IO.Path.GetFileName(path);
        string stem = System.IO.Path.GetFileNameWithoutExtension(path);
        string[] segments = stem.Split('-', '_', '.', StringSplitOptions.None).Concat(Enumerable.Repeat("", 12)).Take(12).ToArray();
        string issue = segments.FirstOrDefault(s => s.StartsWith("ISS", StringComparison.OrdinalIgnoreCase)) ?? "";
        string language = segments.FirstOrDefault(s => s.Length == 2 && s.All(char.IsLetter)) ?? "";
        string corel = !isDirectory && string.Equals(System.IO.Path.GetExtension(path), ".des", StringComparison.OrdinalIgnoreCase) ? DetectCorel(path) : "";
        var info = new FileInfo(path);
        string size = isDirectory ? "" : info.Length.ToString("N0", CultureInfo.CurrentCulture);
        string modified = (isDirectory ? Directory.GetLastWriteTime(path) : info.LastWriteTime).ToString("yyyy-MM-dd HH:mm");
        return new FileRow(isDirectory ? "Ordner" : "Datei", name, segments, issue, language, corel, size, modified, status, displayPath ?? path, path, isDirectory);
    }

    private static string DetectCorel(string path)
    {
        byte[] bytes = File.ReadAllBytes(path).Take(4096).ToArray();
        string text = Encoding.Latin1.GetString(bytes);
        if (text.Contains("CDR", StringComparison.OrdinalIgnoreCase) || text.Contains("Corel", StringComparison.OrdinalIgnoreCase)) return "Corel-Marker gefunden";
        if (bytes.Length >= 4 && bytes[0] == 'P' && bytes[1] == 'K') return "ZIP-Container";
        if (bytes.Length >= 4 && bytes[0] == 'R' && bytes[1] == 'I' && bytes[2] == 'F' && bytes[3] == 'F') return "RIFF-Container";
        return "Version nicht erkannt";
    }
}
