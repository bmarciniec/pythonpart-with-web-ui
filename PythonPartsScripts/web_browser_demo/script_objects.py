"""Script object — the interaction handler of the web_browser_demo PythonPart.

This module sits at the boundary between Allplan and the rest of the stack.
It translates Allplan events (button clicks, point input, ESC key) into calls
on the WpfDialogWrapper, and routes messages from the web app back into
Allplan operations.

Typical flow
------------
1. User opens the PythonPart palette and clicks **Start!** (event 1001).
2. ``on_control_event`` starts a point-input interactor and shows the dialog.
3. User picks a point in the model; ``start_next_input`` forwards the
   coordinates to the web app via ``WpfDialogWrapper.send()``.
4. The web app processes the data and calls ``bridge.SendToHost()``, which
   fires ``_web_message_handler`` on the Python side.
5. User presses ESC; ``on_cancel_function`` disposes the dialog and ends
   the session.
"""
import NemAll_Python_BaseElements as AllplanBaseEle

from BaseScriptObject import BaseScriptObject, BaseScriptObjectData
from BuildingElement import BuildingElement
from CreateElementResult import CreateElementResult
from ScriptObjectInteractors.OnCancelFunctionResult import OnCancelFunctionResult
from ScriptObjectInteractors.PointInteractor import PointInteractor, PointInteractorResult

from .dialog_wrapper import WpfDialogWrapper
from .utils import create_text_ele


class WpfDialogScriptObject(BaseScriptObject):
    """Allplan interaction handler for the web-browser PythonPart.

    Inherits from ``BaseScriptObject``, which provides the coordinate-input
    machinery and the interactor slot (``self.script_object_interactor``).
    Allplan calls the ``on_*`` methods as the user interacts with the model.
    """

    def __init__(self,
                 build_ele         : BuildingElement,
                 script_object_data: BaseScriptObjectData):
        """Initialise the script object and set up the WPF dialog.

        The dialog is created here — not on first show — so that WebView2
        has time to initialise in the background while the user interacts
        with the palette.

        Args:
            build_ele:          palette parameters as a BuildingElement.
            script_object_data: Allplan-provided services bundle.
        """

        super().__init__(script_object_data)

        self.build_ele = build_ele
        self.wpf_dialog_wrapper      = WpfDialogWrapper()
        self.point_interactor_result = PointInteractorResult()
        self.zoom_service            = AllplanBaseEle.ZoomService()

        # register the web message handler
        self.wpf_dialog_wrapper.on_message(self._web_message_handler)

    def execute(self) -> CreateElementResult:
        """Called by Allplan when it needs a geometry result (e.g. for the library thumbnail).

        This demo does not create any model elements, so an empty result is
        returned.  In a real PythonPart you would build and return geometry here.

        Returns:
            Empty ``CreateElementResult``.
        """
        return CreateElementResult()

    # def start_input(self):
    #     """Start the point input"""

    #     self.script_object_interactor = SingleElementSelectInteractor(
    #         self.selection_result,
    #         prompt_msg = "Select anything",)

    def start_next_input(self):
        """Called after an interactor completes its input.

        Forwards the picked point coordinates to the web app as a JSON object.
        The web app receives this via ``window.__onHostMessage(data)``.
        """
        if (point := self.point_interactor_result.input_point) is not None:
            self.wpf_dialog_wrapper.send({
                "x": point.X,
                "y": point.Y,
                "z": point.Z,
            })

    def on_control_event(self, _event_id: int) -> bool:
        """Handle palette button clicks.

        Event IDs are declared in the ``.pyp`` file (``<EventId>`` element).
        1001 is the **Start!** button that triggers point input and shows the dialog.

        Args:
            _event_id: numeric ID of the button that was pressed.

        Returns:
            False — returning True would signal that the palette should refresh,
            which is not needed here.
        """
        if _event_id == 1001:
            self.script_object_interactor = PointInteractor(
                self.point_interactor_result,
                True,
                "Select a point")

            self.script_object_interactor.start_input(self.coord_input)

            self.wpf_dialog_wrapper.show(False)

        return False

    def on_cancel_function(self) -> OnCancelFunctionResult:
        """Called when the user presses Escape or otherwise ends the session.

        ``dispose()`` calls ``ForceClose()`` on the C# side, which sets a flag
        that allows ``OnClosing`` to proceed with actual window destruction
        (normally ``OnClosing`` intercepts the close and just hides the window).

        Returns:
            ``CANCEL_INPUT`` to signal that this PythonPart session should end.
        """
        self.wpf_dialog_wrapper.dispose()
        return OnCancelFunctionResult.CANCEL_INPUT

    def _web_message_handler(self, data: dict) -> None:
        """Handle a message arriving from the web app.

        This is where you act on user interactions that happened inside the
        WebView2.  Replace the ``print`` with real Allplan API calls, e.g.
        creating elements, modifying properties, or starting another interactor.

        Args:
            data: parsed JSON payload sent from the web app via
                  ``bridge.SendToHost(JSON.stringify(payload))``.
        """
        print("Received data from web app:", data)

        created_text = create_text_ele("Hello, World!", self.coord_input)

        self.zoom_service.ZoomToElementWithFactor(
            created_text[0],
            self.coord_input.GetViewWorldProjection(),
            factor   = 1.0,
            bZoomAll = False)
