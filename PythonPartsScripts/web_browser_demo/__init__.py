"""Entry point for the web_browser_demo PythonPart.

Allplan discovers a PythonPart package through two mandatory module-level
functions defined here:

- ``check_allplan_version``  — version guard, called once on load.
- ``create_script_object``   — factory that produces the interaction handler.

Everything else lives in the sub-modules:
- ``script_objects.py`` — Allplan event handling
- ``dialog_wrapper.py`` — Python facade over the .NET WPF dialog
"""
from BaseScriptObject import BaseScriptObject, BaseScriptObjectData
from BuildingElement import BuildingElement

from .script_objects import WpfDialogScriptObject


def check_allplan_version(_build_ele: BuildingElement,
                          _version  : str) -> bool:
    """Version guard called by Allplan before loading the script.

    Return False here to prevent the script from loading on unsupported
    Allplan versions (e.g., if you rely on an API introduced in 2025).

    Args:
        _build_ele: building element carrying the palette parameters.
        _version:   Allplan version string, e.g. ``"2026.0"``.

    Returns:
        True to signal that this version is supported.
    """
    return True


def create_script_object(build_ele         : BuildingElement,
                         script_object_data: BaseScriptObjectData) -> BaseScriptObject:
    """Factory function — Allplan calls this once to create the interaction handler.

    The returned object's lifetime is tied to the active PythonPart session.
    Allplan will call its methods (``on_control_event``, ``on_cancel_function``,
    etc.) in response to user actions.

    Args:
        build_ele:          building element carrying the current palette values.
        script_object_data: bundle of Allplan services (coordinate input, document, …).

    Returns:
        A ``WpfDialogScriptObject`` instance that handles this session.
    """
    return WpfDialogScriptObject(build_ele, script_object_data)
