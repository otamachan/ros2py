import argparse
import pathlib
import sys

SCRIPT_FILE = pathlib.Path(sys.prefix) / "bin" / "activate"


def insert_after(content: str, match_line: str, new_line: str) -> str:
    lines = []
    for line in content.splitlines():
        lines.append(line)
        if line == match_line:
            lines.append(new_line)
    return "\n".join(lines)


def remove_line_if_includes(content: str, remove_word: str) -> str:
    lines = []
    for line in content.splitlines():
        if remove_word not in line:
            lines.append(line)
    return "\n".join(lines)


def update() -> None:
    if not SCRIPT_FILE.exists():
        print(f"{SCRIPT_FILE} does not exist")
        return
    script = SCRIPT_FILE.read_text()
    if "LD_LIBRARY_PATH" in script:
        print("activate is alrady updated")
        return
    script = insert_after(
        script,
        "export PATH",
        '_OLD_LD_LIBRARY_PATH="${LD_LIBRARY_PATH}"; LD_LIBRARY_PATH="$VIRTUAL_ENV/lib:$LD_LIBRARY_PATH"; export LD_LIBRARY_PATH; echo LD_LIBRARY_PATH=${LD_LIBRARY_PATH}',
    )
    script = insert_after(
        script,
        "        unset _OLD_VIRTUAL_PATH",
        '        LD_LIBRARY_PATH="${_OLD_LD_LIBRARY_PATH}"; export LD_LIBRARY_PATH; unset _OLD_LD_LIBRARY_PATH;',
    )
    SCRIPT_FILE.write_text(script)
    print("updated")


def restore() -> None:
    if not SCRIPT_FILE.exists():
        print(f"{SCRIPT_FILE} does not exist")
        return
    script = SCRIPT_FILE.read_text()
    if "LD_LIBRARY_PATH" not in script:
        print("nothing to do")
        return
    script = remove_line_if_includes(script, "LD_LIBRARY_PATH")
    SCRIPT_FILE.write_text(script + "\n")
    print("restored")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--restore", action="store_true")
    args = parser.parse_args()
    if args.restore:
        restore()
    else:
        update()
