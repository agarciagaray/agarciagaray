import inspect

import flet as ft


def test_flet_runtime_api_is_the_audited_version():
    assert getattr(ft, "__version__", None) == "0.86.5"
    assert hasattr(ft, "Alignment")
    assert not hasattr(ft.alignment, "center")
    assert hasattr(ft.FilePickerFileType, "CUSTOM")
    assert "on_result" not in str(inspect.signature(ft.FilePicker))


def test_file_picker_is_a_service_and_registry_supports_registration():
    assert "Service" in {base.__name__ for base in ft.FilePicker.__mro__}
    from flet.controls.page import ServiceRegistry
    assert hasattr(ServiceRegistry, "register_service")
