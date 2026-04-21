"""Helper functions for the Web Browser demo PythonPart."""

import NemAll_Python_AllplanSettings as AllplanSettings
import NemAll_Python_BasisElements as AllplanBasisEle
import NemAll_Python_Geometry as AllplanGeo
import NemAll_Python_IFW_ElementAdapter as AllplanEleAdapter
import NemAll_Python_IFW_Input as AllplanIFW

from DocumentManager import DocumentManager
from PythonPartTransaction import PythonPartTransaction
from TypeCollections.ModelEleList import ModelEleList
from TypeCollections.ModificationElementList import ModificationElementList


def create_text_ele(text: str,
                    coord_input: AllplanIFW.CoordinateInput) -> AllplanEleAdapter.BaseElementAdapterList:
    """Creates a text element in the current document with the current common properties

    Args:
        text: The text to display in the text element
        coord_input: The coordinate input to get the position and orientation of the text element

    Returns:
        A list of BaseElementAdapter containing the created text element
    """

    text_prop = AllplanBasisEle.TextProperties()
    text_prop.Height = 5

    common_prop = AllplanSettings.AllplanGlobalSettings.GetCurrentCommonProperties()

    model_ele_list = ModelEleList()

    model_ele_list.append(AllplanBasisEle.TextElement(
        common_prop,
        text_prop,
        text,
        AllplanGeo.Point2D()))

    pyp_transaction = PythonPartTransaction(DocumentManager.get_instance().document)

    return pyp_transaction.execute(
        AllplanGeo.Matrix3D(),
        coord_input.GetViewWorldProjection(),
        model_ele_list,
        ModificationElementList()
    )
