from enum import Enum


class ProgressStage(Enum):
    PREPARING = "preparing"
    LOADING_VERSION = "loading_version"
    INSTALLING_MOD_LOADER = "installing_mod_loader"
    SELECTING_JAVA = "selecting_java"
    DOWNLOADING_JAVA = "downloading_java"
    INSTALLING_JAVA = "installing_java"
    DOWNLOADING_CLIENT = "downloading_client"
    DOWNLOADING_LIBRARIES = "downloading_libraries"
    DOWNLOADING_ASSET_INDEX = "downloading_asset_index"
    DOWNLOADING_ASSETS = "downloading_assets"
    BUILDING_CONTEXT = "building_context"
    BUILDING_COMMAND = "building_command"
    LAUNCHING = "launching"
    FINISHED = "finished"
