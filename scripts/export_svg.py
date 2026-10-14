"""draw.io CLI で構成図を SVG にエクスポートする。

draw.io の実行ファイルは以下の順で探す。

1. 環境変数 DRAWIO_PATH
2. PATH 上の drawio / draw.io
3. OS ごとの標準インストール先
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = ROOT / "docs" / "diagrams" / "communication.drawio"
OUTPUT_PATH = ROOT / "docs" / "diagrams" / "communication.svg"

DEFAULT_LOCATIONS = [
    Path("/Applications/draw.io.app/Contents/MacOS/draw.io"),
    Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "draw.io" / "draw.io.exe",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "draw.io" / "draw.io.exe",
]


def find_drawio() -> str | None:
    if os.environ.get("DRAWIO_PATH"):
        return os.environ["DRAWIO_PATH"]
    for name in ("drawio", "draw.io"):
        if found := shutil.which(name):
            return found
    for path in DEFAULT_LOCATIONS:
        if path.is_file():
            return str(path)
    return None


def main() -> int:
    drawio = find_drawio()
    if drawio is None:
        print("ERROR: draw.io が見つかりません。インストールするか DRAWIO_PATH を設定してください", file=sys.stderr)
        return 1

    subprocess.run(
        [drawio, "--export", "--format", "svg", "--output", str(OUTPUT_PATH), str(INPUT_PATH)],
        check=True,
    )

    print(f"Generated: {OUTPUT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
