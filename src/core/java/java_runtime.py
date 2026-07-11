import os
import subprocess
from datetime import datetime
from pathlib import Path

from src.models.instance.instance import Instance
from src.models.java.java import JavaInstallation


class JavaRuntime:

    @staticmethod
    def run(
        java: JavaInstallation,
        command: list[str],
        instance: Instance,
    ) -> subprocess.Popen:
        creation_flags = 0

        if os.name == "nt":
            creation_flags = subprocess.CREATE_NO_WINDOW

        log_dir = instance.instance_dir / "logs"
        log_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        timestamp = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

        log_path = log_dir / f"minecraft-{timestamp}.log"

        log_file = log_path.open(
            "w",
            encoding="utf-8",
            errors="replace",
        )

        try:
            return subprocess.Popen(
                [
                    str(java.path),
                    *command,
                ],
                cwd=instance.instance_dir,
                stdin=subprocess.DEVNULL,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                creationflags=creation_flags,
            )

        except Exception:
            log_file.close()
            raise


# import subprocess
# import threading
# from pathlib import Path
# from src.models.instance.instance import Instance
# from src.core.fs.paths import Paths

# class JavaRuntime:

#     @staticmethod
#     def _stream(pipe):
#         try:
#             for line in pipe:
#                 print(line.rstrip())
#         except Exception:
#             pass

#     @staticmethod
#     def run(java_path: Path, cmd: list[str], instance:Instance) -> subprocess.Popen:
#         full_cmd = [str(java_path), *cmd]

#         process = subprocess.Popen(
#             full_cmd,
#             cwd=str(Paths.load_instance_dir(instance.name)),
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE,
#             text=True,
#             bufsize=1,
#             creationflags=subprocess.CREATE_NO_WINDOW
#         )


#         threading.Thread(
#             target=JavaRuntime._stream,
#             args=(process.stdout,),
#             daemon=True
#         ).start()


#         threading.Thread(
#             target=JavaRuntime._stream,
#             args=(process.stderr,),
#             daemon=True
#         ).start()

#         return process