import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from src.gui.pages.instances_page import InstancesPage
from src.models.modloader.fabric_loader_version import FabricLoaderVersion


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def make_instance(name="Fabric", version_id="1.21.1", mod_loader=("fabric", "0.18.6")):
    return SimpleNamespace(name=name, version_id=version_id, instance_dir=f"instances/{name}", mod_loader=mod_loader)


def test_create_uses_loader_name_without_loader_version_picker(app):
    page = InstancesPage()
    page.set_versions([SimpleNamespace(id="1.21.1", type="release")])
    page.create_name_input.setText("Modded")
    page.create_loader_combo.setCurrentText("Fabric")
    emitted = []
    page.create_requested.connect(lambda name, version_id, loader_name: emitted.append((name, version_id, loader_name)))

    page._request_create()

    assert emitted == [("Modded", "1.21.1", "fabric")]
    assert not hasattr(page, "loader_version_combo")


def test_selected_instance_only_updates_manage_loader_controls(app):
    page = InstancesPage()
    page.set_versions([
        SimpleNamespace(id="1.20.1", type="release"),
        SimpleNamespace(id="1.21.1", type="release"),
    ])
    page.version_combo.setCurrentText("1.20.1")
    page.create_loader_combo.setCurrentText("Vanilla")
    requested = []
    page.fabric_versions_requested.connect(requested.append)

    page.set_instances([make_instance()], "Fabric")

    assert page.version_combo.currentText() == "1.20.1"
    assert page.create_loader_combo.currentText() == "Vanilla"
    assert page.manage_loader_combo.currentText() == "Fabric"
    assert requested == ["1.21.1"]


def test_manage_loader_prefers_current_fabric_version(app):
    page = InstancesPage()
    instance = make_instance()
    page.set_instances([instance], instance.name)
    page.set_fabric_versions(
        instance.version_id,
        [
            FabricLoaderVersion(version="0.19.3", stable=True),
            FabricLoaderVersion(version="0.18.6", stable=True),
        ],
    )

    assert page.manage_loader_version_combo.currentData() == "0.18.6"
    assert page.apply_loader_button.isEnabled() is True


def test_manage_loader_uses_stable_version_when_applying_fabric_to_vanilla(app):
    page = InstancesPage()
    instance = make_instance(name="Vanilla", mod_loader=("vanilla", "-1"))
    page.set_instances([instance], instance.name)
    page._fabric_versions[instance.version_id] = [
        FabricLoaderVersion(version="0.20.0-beta", stable=False),
        FabricLoaderVersion(version="0.19.3", stable=True),
    ]

    page.manage_loader_combo.setCurrentText("Fabric")

    assert page.manage_loader_version_combo.currentData() == "0.19.3"
    assert page.selected_manage_loader() == ("fabric", "0.19.3")
