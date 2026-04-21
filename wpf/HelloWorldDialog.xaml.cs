using System;
using System.IO;
using System.Reflection;
using System.Windows;
using Microsoft.Web.WebView2.Core;

namespace HelloWorldWPF
{
    /// <summary>
    /// WPF Window that hosts a WebView2 browser control, forming the middle tier
    /// of the Python ↔ .NET ↔ JavaScript communication stack.
    ///
    /// <para>
    /// <b>Lifecycle note:</b> Closing the window via the X button only <em>hides</em> it;
    /// the WebView2 instance is kept alive so it can be shown again cheaply.
    /// Call <see cref="ForceClose"/> (mapped to <c>dispose()</c> in Python) to truly
    /// destroy the window when the PythonPart session ends.
    /// </para>
    ///
    /// <para>
    /// <b>Thread safety:</b> <see cref="SendToWeb"/> marshals the call to the UI
    /// thread via <c>Dispatcher.Invoke</c>, so it is safe to call from any thread
    /// (e.g. from a pythonnet callback).
    /// </para>
    /// </summary>
    public partial class HelloWorldDialog : Window
    {
        // Static fields are shared across all instances in the same AppDomain.
        // Because Allplan reuses the same AppDomain for the lifetime of the process,
        // we register the assembly resolver only once, no matter how many times the
        // script is activated.
        private static bool _assemblyResolverRegistered = false;
        private static string _resolvedPrgPath;

        private readonly string _prgPath;

        /// <summary>
        /// The COM-visible bridge object that is exposed to JavaScript.
        /// Python subscribes to its <c>MessageFromWeb</c> event to receive
        /// messages from the web app.
        /// </summary>
        public readonly WebBridge Bridge = new WebBridge();

        /// <summary>
        /// Initialises the dialog and wires up the WebView2 assembly resolver.
        /// </summary>
        /// <param name="prgPath">
        /// Absolute path to the Allplan <c>Prg</c> folder.  Must contain
        /// <c>Microsoft.Web.WebView2.Wpf.dll</c>, <c>Microsoft.Web.WebView2.Core.dll</c>,
        /// and the <c>Microsoft.WebView2.FixedVersionRuntime</c> sub-folder.
        /// </param>
        public HelloWorldDialog(string prgPath)
        {
            _prgPath = prgPath;
            _resolvedPrgPath = prgPath;

            // AppDomain.AssemblyResolve fires when the CLR cannot find an assembly
            // through its normal probing paths.  We redirect any Microsoft.Web.WebView2.*
            // load to prgPath.  If Allplan has already loaded those assemblies into the
            // AppDomain (very likely), this handler is never called — which is fine.
            if (!_assemblyResolverRegistered)
            {
                AppDomain.CurrentDomain.AssemblyResolve += ResolveWebViewAssembly;
                _assemblyResolverRegistered = true;
            }

            InitializeComponent();

            // Defer WebView2 initialisation to the Loaded event so the window handle
            // exists before we try to attach the browser.
            Loaded += OnLoaded;
        }
        private async void OnLoaded(object sender, RoutedEventArgs e)
        {
            // Use the fixed-version runtime bundled with Allplan rather than any
            // system-installed Edge / WebView2 runtime.  This guarantees the same
            // browser engine version on every customer machine.
            var runtimeFolder = Path.Combine(_prgPath, "Microsoft.WebView2.FixedVersionRuntime");

            // The user-data folder stores cookies, cache, and other browser state.
            // Using a dedicated sub-folder in TEMP avoids conflicts with other WebView2
            // instances that may be running inside Allplan.
            var userDataFolder = Path.Combine(Path.GetTempPath(), "AllplanWebView2UserData");

            var env = await CoreWebView2Environment.CreateAsync(runtimeFolder, userDataFolder);
            await webView.EnsureCoreWebView2Async(env);

            // Expose the bridge object to JavaScript under the name "bridge".
            // In the web app: const bridge = await window.chrome.webview.hostObjects.bridge;
            // Note: all host object method calls from JS are inherently async.
            webView.CoreWebView2.AddHostObjectToScript("bridge", Bridge);

            webView.CoreWebView2.Navigate("https://my-test-webapplication-for-allplan.lovable.app");
        }

        /// <summary>
        /// Intercepts the window-close request (X button or <c>Close()</c> call)
        /// and hides the window instead of destroying it.
        /// </summary>
        /// <remarks>
        /// WPF windows cannot be shown again after <c>Close()</c> is called — the
        /// underlying HWND is destroyed.  By hiding instead, we keep the WebView2
        /// instance alive so re-opening the dialog is instant (no re-navigation).
        /// <see cref="ForceClose"/> bypasses this guard for true disposal.
        /// </remarks>
        protected override void OnClosing(System.ComponentModel.CancelEventArgs e)
        {
            if (!_forceClose)
            {
                e.Cancel = true;
                Hide();
                return;
            }
            base.OnClosing(e);
        }

        // Flag that lets ForceClose() bypass the hide-instead-of-close guard.
        private bool _forceClose = false;

        /// <summary>
        /// Truly destroys the window.  Call this when the PythonPart session ends
        /// (i.e. from <c>WpfDialogWrapper.dispose()</c>).
        /// </summary>
        public void ForceClose()
        {
            _forceClose = true;
            Close();
        }

        /// <summary>
        /// Evaluates a JavaScript expression in the web app, passing <paramref name="json"/>
        /// as the argument to <c>window.__onHostMessage()</c>.
        /// </summary>
        /// <param name="json">A JSON string.  The web app receives the parsed value.</param>
        /// <remarks>
        /// <c>ExecuteScriptAsync</c> must be called on the WPF UI thread.
        /// <c>Dispatcher.Invoke</c> ensures this is the case even when Python calls
        /// this method from a background thread.
        /// </remarks>
        public void SendToWeb(string json)
        {
            Dispatcher.Invoke(() =>
                webView.CoreWebView2.ExecuteScriptAsync($"window.__onHostMessage({json})"));
        }

        /// <summary>
        /// Custom assembly resolver for the WebView2 managed DLLs.
        /// </summary>
        /// <remarks>
        /// Because the DLLs are not on any standard probing path, the CLR would
        /// otherwise throw a <see cref="FileNotFoundException"/>.  We redirect the
        /// load to <see cref="_resolvedPrgPath"/> — the Allplan Prg folder passed
        /// at construction time.  If Allplan has already loaded the assembly (typical),
        /// this handler simply returns <c>null</c> and the CLR uses the cached copy.
        /// </remarks>
        private static Assembly ResolveWebViewAssembly(object sender, ResolveEventArgs args)
        {
            var name = new AssemblyName(args.Name).Name;
            if (name.StartsWith("Microsoft.Web.WebView2"))
            {
                var path = Path.Combine(_resolvedPrgPath, name + ".dll");
                if (File.Exists(path))
                    return Assembly.LoadFrom(path);
            }
            return null;
        }
    }
}
