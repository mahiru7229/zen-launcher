from __future__ import annotations

from datetime import datetime, timezone

from src.core.curseforge.curseforge_client import CurseForgeClient
from src.core.curseforge.curseforge_downloader import CurseForgeDownloader
from src.core.curseforge.curseforge_registry import CurseForgeRegistry
from src.core.fs.paths import Paths
from src.core.instance.instance_run_lock import InstanceRunLock
from src.core.mod.mod_manager import ModManager
from src.core.modloader.mod_loader_manager import ModLoaderManager
from src.core.progress.progress_reporter import ProgressReporter
from src.models.curseforge.file import CurseForgeFile
from src.models.curseforge.install_result import CurseForgeModInstallResult
from src.models.instance.instance import Instance
from src.models.progress.progress_stage import ProgressStage


class CurseForgeModInstaller:
    MAX_DEPENDENCIES = 64

    @staticmethod
    def install(instance: Instance, project_id: int, file_id: int, install_dependencies: bool = True, allowed_release_types: tuple[str, ...] | list[str] | set[str] | None = None, reporter: ProgressReporter | None = None) -> CurseForgeModInstallResult:
        loader_name, _ = ModLoaderManager.normalize(instance.mod_loader)
        if loader_name != ModLoaderManager.FORGE:
            raise RuntimeError("CurseForge mod installation requires a Forge instance.")
        if InstanceRunLock.is_active(instance):
            raise RuntimeError("Close Minecraft before installing or updating mods.")
        allowed = CurseForgeClient.normalize_release_types(allowed_release_types)
        root = CurseForgeClient.get_file(project_id, file_id)
        if root.release_type not in allowed:
            raise RuntimeError(f"CurseForge file '{root.display_name}' uses the disabled {root.release_type} channel.")
        plan = CurseForgeModInstaller._build_plan(root, instance.version_id, install_dependencies, allowed)
        registry = CurseForgeRegistry.load(instance)
        mods = registry.setdefault("mods", {})
        installed_projects: list[str] = []
        installed_files: list[str] = []
        warnings: list[str] = []

        for file in plan:
            project = CurseForgeClient.get_project(file.project_id)
            cache = Paths.curseforge_file_cache(file.project_id, file.file_id, file.file_name)
            previous = mods.get(str(file.project_id), {}) if isinstance(mods.get(str(file.project_id)), dict) else {}
            entry = {
                "projectId": file.project_id,
                "fileId": file.file_id,
                "fileName": file.file_name,
                "displayName": project.name,
                "sha1": file.sha1,
                "size": file.file_length,
                "downloadUrl": file.download_url,
                "releaseType": file.release_type,
                "datePublished": file.file_date,
                "source": "curseforge",
                "updatedAt": datetime.now(timezone.utc).isoformat(),
            }
            try:
                CurseForgeDownloader.download_file(file, cache, reporter=reporter, stage=ProgressStage.DOWNLOADING_MODS, message=f"Downloading {project.name}...")
                added = ModManager.add_mods(instance, [cache], replace=True)
                if not added:
                    raise RuntimeError(f"'{project.name}' was downloaded but could not be added to the instance.")
                old_name = str(previous.get("fileName") or "")
                new_name = added[0].file_name
                if old_name and old_name.casefold() != new_name.casefold():
                    old_path = CurseForgeRegistry.safe_tracked_path(instance, old_name)
                    if old_path is not None:
                        old_path.unlink(missing_ok=True)
                        old_path.with_name(old_path.name + ModManager.DISABLED_SUFFIX).unlink(missing_ok=True)
                entry["fileName"] = new_name
                entry["pendingDownload"] = False
                entry["lastDownloadError"] = ""
                installed_projects.append(project.name)
                installed_files.append(new_name)
            except Exception as error:
                entry["pendingDownload"] = True
                entry["lastDownloadError"] = str(error)
                warnings.append(f"{project.name}: {error}")
            mods[str(file.project_id)] = entry

        CurseForgeRegistry.save(instance, registry)
        return CurseForgeModInstallResult(installed_projects=tuple(installed_projects), installed_files=tuple(installed_files), warnings=tuple(warnings))

    @staticmethod
    def _build_plan(root: CurseForgeFile, game_version: str, install_dependencies: bool, allowed_release_types: tuple[str, ...]) -> list[CurseForgeFile]:
        plan: list[CurseForgeFile] = []
        visited: set[int] = set()
        visiting: set[int] = set()

        def visit(file: CurseForgeFile) -> None:
            if file.project_id in visited:
                return
            if len(visited) >= CurseForgeModInstaller.MAX_DEPENDENCIES:
                raise RuntimeError("The CurseForge dependency graph is too large to install safely.")
            if file.release_type not in allowed_release_types:
                raise RuntimeError(f"Required CurseForge file '{file.display_name}' uses the disabled {file.release_type} channel.")
            if game_version and game_version not in file.game_versions:
                raise RuntimeError(f"CurseForge file '{file.display_name}' does not support Minecraft {game_version}.")
            if file.project_id in visiting:
                return
            visiting.add(file.project_id)
            try:
                if install_dependencies:
                    for dependency in file.dependencies:
                        if not dependency.required:
                            continue
                        dependency_file = CurseForgeClient.latest_compatible_file(dependency.project_id, game_version, allowed_release_types)
                        visit(dependency_file)
            finally:
                visiting.discard(file.project_id)
            visited.add(file.project_id)
            plan.append(file)

        visit(root)
        return plan
