using System;
using System.Runtime.InteropServices;

namespace HelloWorldWPF
{
    /// <summary>
    /// Message hub between the JavaScript web app and the .NET/Python layers.
    ///
    /// <para>
    /// An instance of this class is registered with WebView2 via
    /// <c>CoreWebView2.AddHostObjectToScript("bridge", Bridge)</c>, making it
    /// accessible in JavaScript as:
    /// <code>
    /// const bridge = await window.chrome.webview.hostObjects.bridge;
    /// await bridge.SendToHost(JSON.stringify({ action: "doSomething" }));
    /// </code>
    /// </para>
    ///
    /// <para>
    /// <b>Why COM-visible?</b>  WebView2's host-object protocol uses COM under the hood
    /// to marshal calls between the browser process and the host process.  The
    /// <see cref="ComVisibleAttribute"/> and <see cref="ClassInterfaceAttribute"/> attributes
    /// are required for WebView2 to introspect and expose the object's methods to JS.
    /// </para>
    ///
    /// <para>
    /// <b>All JS calls are async.</b>  Even synchronous-looking methods become Promises
    /// on the JS side because of the cross-process nature of the bridge.
    /// Always <c>await</c> them.
    /// </para>
    /// </summary>
    [ClassInterface(ClassInterfaceType.AutoDual)]
    [ComVisible(true)]
    public class WebBridge
    {
        /// <summary>
        /// Raised on the .NET side whenever the web app calls <c>bridge.SendToHost()</c>.
        /// Python subscribes with: <c>dialog.Bridge.MessageFromWeb += my_handler</c>
        /// </summary>
        public event Action<string> MessageFromWeb;

        /// <summary>
        /// Entry point for messages coming from JavaScript.
        /// Called by the web app: <c>await bridge.SendToHost(JSON.stringify(payload))</c>
        /// </summary>
        /// <param name="message">Raw JSON string sent from the web app.</param>
        public void SendToHost(string message)
        {
            MessageFromWeb?.Invoke(message);
        }
    }
}
