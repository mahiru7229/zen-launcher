import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from src.gui.pages.mods_page import ModsPage
from src.models.curseforge.cache import CurseForgeCacheInfo
from src.models.curseforge.file import CurseForgeFile
from src.models.curseforge.project import CurseForgeProject, CurseForgeSearchResult
from src.models.modrinth.project import ModrinthProject, ModrinthSearchResult
from src.models.modrinth.version import ModrinthFile, ModrinthVersion


def _project() -> ModrinthProject:
    return ModrinthProject(
        project_id="project",
        slug="example",
        title="Example Mod",
        description="Example description",
        project_type="mod",
        author="Tester",
        downloads=123,
        date_modified="2026-07-20T00:00:00Z",
    )


def _version(version_id: str, loader: str, game_version: str = "1.21.1") -> ModrinthVersion:
    return ModrinthVersion(
        version_id=version_id,
        project_id="project",
        name=version_id,
        version_number="1.0.0",
        version_type="release",
        game_versions=(game_version,),
        loaders=(loader,),
        files=(ModrinthFile(url="https://example.invalid/mod.jar", filename="mod.jar", sha1="a", sha512="b", size=1, primary=True),),
    )


def _curseforge_project() -> CurseForgeProject:
    return CurseForgeProject(
        project_id=42,
        name="Forge Example",
        slug="forge-example",
        summary="CurseForge example",
        download_count=456,
        authors=("Tester",),
        logo_url="",
        class_id=6,
        date_modified="2026-07-21T00:00:00Z",
        game_versions=("1.20.1",),
        loaders=("forge",),
    )


def _curseforge_file() -> CurseForgeFile:
    return CurseForgeFile(
        file_id=99,
        project_id=42,
        display_name="Forge Example 1.0",
        file_name="forge-example.jar",
        release_type="release",
        file_date="2026-07-21T00:00:00Z",
        file_length=100,
        download_url="https://example.invalid/forge-example.jar",
        sha1="abc",
        game_versions=("1.20.1",),
        dependencies=(),
        loaders=("forge",),
    )


def test_mods_page_filters_versions_by_loader_and_requests_instance_choice(gui_app):
    page = ModsPage()
    emitted = []
    page.install_requested.connect(lambda version, loader, channels: emitted.append((version, loader, tuple(channels))))

    page.set_search_result(ModrinthSearchResult(projects=(_project(),), total_hits=1, offset=0, limit=25), "fabric")
    page.set_versions("project", [_version("fabric-version", "fabric"), _version("forge-version", "forge")], "fabric")

    assert page.version_combo.count() == 1
    assert page.version_combo.currentData() == "fabric-version"
    assert "Minecraft 1.21.1" in page.version_combo.currentText()

    page._request_install()

    assert len(emitted) == 1
    assert emitted[0][0].version_id == "fabric-version"
    assert emitted[0][1] == "fabric"
    assert emitted[0][2] == ("release",)


def test_mods_page_ignores_results_for_another_loader(gui_app):
    page = ModsPage()
    page.loader_combo.setCurrentIndex(page.loader_combo.findData("forge"))

    page.set_search_result(ModrinthSearchResult(projects=(_project(),), total_hits=1, offset=0, limit=25), "fabric")

    assert page.results_table.rowCount() == 0


def test_channel_checkbox_updates_before_deferred_reload(gui_app):
    from PySide6.QtTest import QTest

    page = ModsPage()
    emitted = []
    page.channel_preferences_changed.connect(lambda beta, alpha: emitted.append((beta, alpha)))

    page.include_beta_checkbox.setChecked(True)

    assert page.include_beta_checkbox.isChecked() is True
    assert emitted == []

    QTest.qWait(40)
    gui_app.processEvents()

    assert emitted == [(True, False)]


def test_provider_and_loader_selector_use_the_same_inline_catalog(gui_app):
    page = ModsPage()
    curseforge_searches = []
    modrinth_searches = []
    page.curseforge_search_requested.connect(lambda query, sort, offset, loader: curseforge_searches.append((query, sort, offset, loader)))
    page.search_requested.connect(lambda query, sort, offset, loader: modrinth_searches.append((query, sort, offset, loader)))

    assert page.selected_provider == "modrinth"
    assert page.selected_loader == "fabric"
    assert page.browser_card.isHidden() is False
    assert page.cache_status_label.isHidden() is True

    page.provider_combo.setCurrentIndex(page.provider_combo.findData("curseforge"))
    page.loader_combo.setCurrentIndex(page.loader_combo.findData("forge"))
    page.search_input.setText("Evil Hunter")

    assert page.browser_card.isHidden() is False
    assert page.cache_status_label.isHidden() is False
    assert curseforge_searches == []
    assert modrinth_searches == []

    page.search_button.click()

    assert curseforge_searches == [("Evil Hunter", "popularity", 0, "forge")]
    assert modrinth_searches == []


def test_curseforge_results_files_and_install_are_rendered_inline(gui_app):
    page = ModsPage()
    files_requested = []
    install_requested = []
    page.curseforge_files_requested.connect(lambda project_id, loader, channels: files_requested.append((project_id, loader, tuple(channels))))
    page.curseforge_install_requested.connect(lambda file, loader, channels: install_requested.append((file, loader, tuple(channels))))
    page.provider_combo.setCurrentIndex(page.provider_combo.findData("curseforge"))
    page.loader_combo.setCurrentIndex(page.loader_combo.findData("forge"))

    result = CurseForgeSearchResult(
        projects=(_curseforge_project(),),
        total_count=1,
        index=0,
        page_size=25,
        cache_info=CurseForgeCacheInfo(from_cache=True),
    )
    page.set_curseforge_search_result("forge", result)

    assert page.results_table.rowCount() == 1
    assert files_requested == [(42, "forge", ("release",))]

    page.set_curseforge_files(42, "forge", [_curseforge_file()])

    assert page.version_combo.count() == 1
    assert page.version_combo.currentData() == 99
    assert page.install_button.isEnabled() is True

    page._request_install()

    assert len(install_requested) == 1
    assert install_requested[0][0].file_id == 99
    assert install_requested[0][1] == "forge"
    assert install_requested[0][2] == ("release",)


def test_catalog_selector_controls_follow_busy_state(gui_app):
    page = ModsPage()

    page.set_busy(True)

    assert page.provider_combo.isEnabled() is False
    assert page.loader_combo.isEnabled() is False
    assert page.search_button.isEnabled() is False

    page.set_busy(False)

    assert page.provider_combo.isEnabled() is True
    assert page.loader_combo.isEnabled() is True
    assert page.search_button.isEnabled() is True
