"""Python facade over the HelloWorldWPF .NET assembly.

This module is the only place in the Python layer that is aware of the .NET
DLL.  Everything above it (``script_objects.py``) works with plain Python
dicts and callables, with no knowledge of C# types.

How the .NET interop works
--------------------------
pythonnet (shipped with Allplan) allows Python code to load and call .NET
assemblies at runtime.  The key steps are:

1. ``clr.AddReference(path)`` — loads the DLL into the current AppDomain.
2. ``__import__("HelloWorldWPF").HelloWorldDialog`` — imports the class from
   the .NET namespace, just like a regular Python import.
3. Instantiating and calling the class works like any Python object.
   .NET events are subscribed to with ``+=``.

See https://pythonnet.github.io/ for the full pythonnet documentation.
"""

import json

from pathlib import Path
from typing import Callable

import clr
import NemAll_Python_AllplanSettings as AllplanSettings


class WpfDialogWrapper:
    """Class wrapping the WPF dialog"""

    def __init__(self):
        """Initialization of the dialog wrapper"""

        # Make sure this points to the compiled DLL location (e.g., ../wpf/bin/Release/HelloWorldWPF.dll)
        # Assuming it's copied next to the script for this example:
        dialog_assembly_path = Path(__file__).parent / Path("HelloWorldWPF.dll")
        prg_path = AllplanSettings.AllplanPaths.GetPrgPath()

        # Load the DLL
        clr.AddReference(str(dialog_assembly_path.resolve()))

        # After adding the reference, import the class from the DLL's namespace
        HelloWorldDialog = __import__("HelloWorldWPF").HelloWorldDialog

        # Instantiate the WPF dialog
        self.dialog = HelloWorldDialog(prg_path)

        # Subscribe to messages coming from the web app
        self.dialog.Bridge.MessageFromWeb += self._on_message_from_web

        # Optional user-supplied handler set via on_message()
        self._message_handler: Callable[[dict], None] | None = None

    def on_message(self, handler: Callable[[dict], None]) -> None:
        """Register a callback invoked when the web app sends a message.

        The callback receives a single argument: the parsed JSON payload (dict).

        Args:
            handler:  a function that takes a dict argument. This will be called whenever the web app sends a message.

        Examples:
            >>> wrapper.on_message(lambda data: print("From web:", data))
        """
        self._message_handler = handler

    def send(self, payload: dict) -> None:
        """Push a JSON-serialisable payload to the web application.

        The web application must implement:

        ```js
        window.__onHostMessage = function(data) { ... }
        ```

        Args:
            payload:  a JSON-serialisable Python dict to send to the web app.
        """
        self.dialog.SendToWeb(json.dumps(payload))

    def show(self, modal: bool = False) -> bool:
        """Shows the dialog

        Args:
            modal:  if True, ShowDialog is used and ALLPLAN is blocked until the dialog is closed.
                    If False, Show is used and the method returns immediately, not blocking ALLPLAN.

        Returns:
            If modal is True, returns the result of ShowDialog(). If modal is False, returns True.
        """
        # ShowDialog blocks until the window is closed
        if modal:
            return self.dialog.ShowDialog()
        else:
            self.dialog.Show()
            return True

    def close(self):
        """Hides the dialog. The window stays alive and can be shown again with show()."""
        self.dialog.Hide()

    def dispose(self):
        """Truly destroys the dialog. Call when the script is unloaded (on_cancel_function etc.).
        After this, the wrapper must not be used.
        """
        self.dialog.ForceClose()

    # ------------------------------------------------------------------
    # Internal

    def _on_message_from_web(self, message: str) -> None:
        """Receives raw JSON string from the C# bridge and dispatches it."""
        if self._message_handler is None:
            return
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            payload = {"raw": message}
        self._message_handler(payload)
