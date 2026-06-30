import subprocess
import threading
from pathlib import Path


class JavaRuntime:

    @staticmethod
    def _stream(pipe):
        try:
            for line in pipe:
                print(line.rstrip())
        except Exception:
            pass

    @staticmethod
    def run(java_path: Path, cmd: list[str]) -> subprocess.Popen:
        full_cmd = [str(java_path), *cmd]

        process = subprocess.Popen(
            full_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        # 🔥 realtime stdout
        threading.Thread(
            target=JavaRuntime._stream,
            args=(process.stdout,),
            daemon=True
        ).start()

        # 🔥 realtime stderr
        threading.Thread(
            target=JavaRuntime._stream,
            args=(process.stderr,),
            daemon=True
        ).start()

        return process