import inspect

import flet as ft
from main import register_page_service


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


def test_dashboard_card_table_uses_data_rows():
    table = ft.DataTable(
        columns=[ft.DataColumn(ft.Text("Tipo"))],
        rows=[ft.DataRow(cells=[ft.DataCell(ft.Text("Débito"))])],
    )
    assert len(table.rows) == 1


def test_page_service_registration_supports_registry_and_list():
    service = object()

    class Registry:
        def __init__(self):
            self.items = []
        def register_service(self, item):
            self.items.append(item)

    registry_page = type("Page", (), {"services": Registry()})()
    register_page_service(registry_page, service)
    assert registry_page.services.items == [service]

    list_page = type("Page", (), {"services": []})()
    register_page_service(list_page, service)
    assert list_page.services == [service]
