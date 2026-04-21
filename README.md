# Web Browser in ALLPLAN

A demonstration project showing how to embed a **modern web-based UI** (React, Vue, etc.) inside an [ALLPLAN](https://www.allplan.com) PythonPart, with **full bidirectional communication** between the web app and the ALLPLAN Python layer.

## Why this pattern?

ALLPLAN exposes a rich Python API, but its native UI toolkit (palette parameters, dialogs) is intentionally simple. If you want a rich, interactive UI — dashboards, 3D previews, data grids — you are better off building it as a web application with a modern JS framework and embedding it in ALLPLAN via this bridge.

The key insight is that **ALLPLAN already ships WebView2** (Microsoft Edge's embeddable browser engine). This project takes advantage of that: the C# and WebView2 layers add zero weight to your deployment — no NuGet packages, no bundled runtimes.

## Architecture

```
┌────────────────────────────────────────────────────────┐
│  ALLPLAN (host application)                            │
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Python layer  (PythonPart)                      │  │
│  │  · Receives ALLPLAN events (clicks, input, …)    │  │
│  │  · Calls WpfDialogWrapper.send() to push data    │  │
│  │  · Handles messages from the web app via         │  │
│  │    WpfDialogWrapper.on_message()                 │  │
│  └──────────────────────┬───────────────────────────┘  │
│                         │ pythonnet (.NET interop)     │
│  ┌──────────────────────▼───────────────────────────┐  │
│  │  .NET / WPF layer  (HelloWorldWPF.dll)           │  │
│  │  · HelloWorldDialog  — WPF Window hosting        │  │
│  │    a WebView2 control                            │  │
│  │  · WebBridge         — COM-visible message hub   │  │
│  │    between JS and .NET/Python                    │  │
│  └──────────────────────┬───────────────────────────┘  │
│                         │ WebView2 JS bridge           │
│  ┌──────────────────────▼───────────────────────────┐  │
│  │  JavaScript / Web app                            │  │
│  │  · Any framework (React, Vue, vanilla JS, …)     │  │
│  │  · Calls bridge.SendToHost() to send to Python   │  │
│  │  · Receives data via window.__onHostMessage()    │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

### Communication flow

| Direction | Mechanism |
|---|---|
| Python → Web app | `WpfDialogWrapper.send(dict)` → `HelloWorldDialog.SendToWeb()` → `ExecuteScriptAsync` → `window.__onHostMessage(data)` |
| Web app → Python | `bridge.SendToHost(json)` → `WebBridge.MessageFromWeb` event → `WpfDialogWrapper._on_message_from_web()` → your handler |

---

## Project structure

```
web-browser-in-allplan/
│
├── PythonPartsScripts/
│   └── web_browser_demo/         # Python package — the PythonPart implementation
│       ├── __init__.py           # ALLPLAN entry point: check_allplan_version, create_script_object
│       ├── script_objects.py     # WpfDialogScriptObject — handles ALLPLAN events
│       ├── dialog_wrapper.py     # WpfDialogWrapper — Python facade over the .NET dialog
│       └── HelloWorldWPF.dll     # Built artifact (not in this repo); copied here by build.bat
│
├── Library/
│   └── Web Browser Demo/
│       └── Web Browser Demo.pyp          # PythonPart definition file (UI palette, button wiring)
│
├── wpf/                          # C# / WPF project (compiles to HelloWorldWPF.dll)
│   ├── HelloWorldDialog.xaml     # WPF Window layout — contains only a WebView2 control
│   ├── HelloWorldDialog.xaml.cs  # Code-behind: WebView2 init, JS bridge wiring, show/hide logic
│   ├── WebBridge.cs              # COM-visible message hub (Python ↔ JS)
│   └── HelloWorldWPF.csproj      # SDK-style project; references WebView2 from ALLPLAN's Prg folder
│
├── .scripts/
│   └── build.bat                 # Builds the DLL and copies it to the Python package
│
└── add_to_allplan.bat            # Creates symlinks into your ALLPLAN Usr/Std folder for testing
```

### What to ship to customers

You only need to ship the `PythonPartsScripts` and `Library` folders. The `wpf/` folder is only needed on the developer machine to build the DLL, and the `.scripts/build.bat` is a helper for that process. The `add_to_allplan.bat` is only a convenience for testing.

## Prerequisites

| Requirement | Notes |
|---|---|
| ALLPLAN 2026 | Ships pythonnet, WebView2, and all required .NET assemblies |
| [.NET SDK](https://dotnet.microsoft.com/download) (≥ 6) | Only needed on the **developer machine** to build the DLL |

No NuGet packages. No pip installs. Everything the runtime needs is already in ALLPLAN.

## Getting started

### 1 — Build the .NET layer

Clone the repo and run the build script:

```bat
.scripts\build.bat
```

This does two things:
1. Runs `dotnet build -c Release` in the `wpf/` folder.
2. Copies `HelloWorldWPF.dll` into `PythonPartsScripts\web_browser_demo\`.

If your ALLPLAN installation is not in the default path (`C:\Program Files\Allplan\...\Prg`), pass the `Prg` folder explicitly:

```bat
dotnet build -c Release /p:PrgPath="D:\Allplan\Allplan 2026\Prg"
```

This only affects **compile-time** reference resolution. At runtime, the path is always taken from the value passed to `HelloWorldDialog(prgPath)`.

### 2 — Install into ALLPLAN

Run `add_to_allplan.bat` and enter your ALLPLAN `Usr` or `Std` folder when prompted. It creates symbolic links, so any change you make in this repo is immediately reflected in ALLPLAN without re-copying.

```txt
Please enter the Path to Usr or Std: C:\Users\you\Documents\Nemetschek\Allplan\2026\Usr\Local
```

### 3 — Open in ALLPLAN

The PythonPart appears in the ALLPLAN Library under **Web Browser Demo → Web Browser Demo**. Click **Start!** to open the WebView2 dialog.

---

## How to adapt this to your project

### Replacing the web app URL

In `HelloWorldDialog.xaml.cs`, change the hard-coded URL passed to `Navigate()`:

```csharp
webView.CoreWebView2.Navigate("https://your-app.example.com");
```

For local development, you can also point it at `localhost`:

```csharp
webView.CoreWebView2.Navigate("http://localhost:5173");  // Vite dev server, for example
```

### Sending data from Python to the web app

From your script object (or any Python code with access to the wrapper):

```python
self.wpf_dialog_wrapper.send({
    "event": "elementSelected",
    "id": 42,
    "coordinates": {"x": 100.0, "y": 200.0, "z": 0.0}
})
```

In your web app, receive it:

```js
window.__onHostMessage = function(data) {
    // data is the parsed object — update your app state here
    console.log("From ALLPLAN:", data);
};
```

### Receiving data from the web app in Python

In your web app, send a message:

```js
async function notifyAllplan(payload) {
    // hostObjects calls are always async in WebView2
    const bridge = await window.chrome.webview.hostObjects.bridge;
    await bridge.SendToHost(JSON.stringify(payload));
}

// Example: user clicked something
notifyAllplan({ action: "createWall", length: 5000 });
```

Register a handler on the Python side:

```python
def handle_web_message(data: dict) -> None:
    if data.get("action") == "createWall":
        length = data["length"]
        # ... create the wall element via ALLPLAN API

self.wpf_dialog_wrapper.on_message(handle_web_message)
```

### Replacing the script logic

`WpfDialogScriptObject` in `script_objects.py` is the main interaction handler. The most relevant hooks are:

| Method | When it is called | Typical use |
|---|---|---|
| `__init__` | Script starts | Initialise the dialog wrapper |
| `on_control_event(event_id)` | User clicks a palette button | Show the dialog, start an input interactor |
| `start_next_input()` | An interactor finishes | Send the result to the web app |
| `on_cancel_function()` | User presses Escape | Dispose the dialog and finish |

---

## Key implementation decisions

### WebView2 DLLs are not bundled

`<Private>false</Private>` in the `.csproj` means the WebView2 assemblies are referenced at compile time but **not copied** into the build output. At runtime they are resolved from `prgPath` (the ALLPLAN `Prg` folder) via `AppDomain.AssemblyResolve`. This keeps the repo and deployment tiny.

### Hide, don't Close

Calling `Window.Close()` in WPF destroys the window permanently. To allow the dialog to be re-opened without re-initialising WebView2 (expensive), the `OnClosing` override intercepts close requests and calls `Hide()` instead. `ForceClose()` / `dispose()` are the correct way to truly destroy the window when the script exits.

### Show() vs ShowDialog()

`ShowDialog()` is modal — it blocks the calling thread by running its own message pump. `Show()` is modeless — it returns immediately and relies on the host application's existing message loop (ALLPLAN's). Use `show()` (the default) unless you specifically need to block ALLPLAN during the dialog's lifetime.

### pythonnet event subscription

pythonnet maps .NET events to Python callables using `+=`. The handler signature must match the delegate:

```python
# Action<string>  →  one string argument
dialog.Bridge.MessageFromWeb += lambda msg: print(msg)
```

### Thread safety for JS calls

`ExecuteScriptAsync` must be called on the WPF UI thread. `Dispatcher.Invoke` ensures this regardless of which thread Python calls `SendToWeb` from.

---

## Debugging tips

- **DevTools**: Right-click inside the WebView2 and choose *Inspect* (if enabled). To enable it from C#: `webView.CoreWebView2.OpenDevToolsWindow()`.
- **Python output**: `print()` in your script object writes to the ALLPLAN Python console, visible in the ALLPLAN trace window.
- **AssemblyResolve not firing**: This only fires when the CLR cannot find the assembly through normal probing. If ALLPLAN has already loaded WebView2 into the AppDomain (which it likely has), the handler is simply never called — that's expected and correct.
