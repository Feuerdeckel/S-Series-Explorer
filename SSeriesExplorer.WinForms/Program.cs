using System;
using System.IO;
using System.Windows.Forms;

namespace SSeriesExplorer;

internal static class Program
{
    public const string Version = "1.0.0";

    [STAThread]
    private static void Main()
    {
        ApplicationConfiguration.Initialize();
        Application.SetUnhandledExceptionMode(UnhandledExceptionMode.CatchException);
        Application.ThreadException += (_, e) => LogAndShow(e.Exception);
        AppDomain.CurrentDomain.UnhandledException += (_, e) => LogAndShow(e.ExceptionObject as Exception);
        Application.Run(new MainForm());
    }

    private static void LogAndShow(Exception? exception)
    {
        string message = exception?.ToString() ?? "Unbekannter Fehler";
        File.WriteAllText(Path.Combine(AppContext.BaseDirectory, "startup.log"), message);
        MessageBox.Show("S-Series Explorer wurde unerwartet beendet. Details stehen in startup.log.", "S-Series Explorer", MessageBoxButtons.OK, MessageBoxIcon.Error);
    }
}
