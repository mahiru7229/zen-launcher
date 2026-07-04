import subprocess
import threading
from pathlib import Path
from src.models.instance.instance import Instance

class JavaRuntime:

    @staticmethod
    def _stream(pipe):
        try:
            for line in pipe:
                print(line.rstrip())
        except Exception:
            pass

    @staticmethod
    def run(java_path: Path, cmd: list[str], instance:Instance) -> subprocess.Popen:
        full_cmd = [str(java_path), *cmd]

        process = subprocess.Popen(
            full_cmd,
            cwd=str(instance.instance_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )


        threading.Thread(
            target=JavaRuntime._stream,
            args=(process.stdout,),
            daemon=True
        ).start()


        threading.Thread(
            target=JavaRuntime._stream,
            args=(process.stderr,),
            daemon=True
        ).start()

        return process