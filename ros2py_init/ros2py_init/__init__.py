import argparse
import glob
import os
import pathlib
import platform
import sys

SCRIPT_FILE = pathlib.Path(sys.prefix) / "bin" / "activate"
VAR_NAME = "LD_LIBRARY_PATH"
if platform.system() == "Darwin":
    VAR_NAME = "DYLD_LIBRARY_PATH"


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
    if VAR_NAME in script:
        print("activate is alrady updated")
        return
    script = insert_after(
        script,
        "export PATH",
        f'_OLD_{VAR_NAME}="${{{VAR_NAME}}}"; {VAR_NAME}="$(ros2py-init --path)"; AMENT_PREFIX_PATH=$VIRTUAL_ENV; export {VAR_NAME}; export AMENT_PREFIX_PATH; echo {VAR_NAME}=${{{VAR_NAME}}}',
    )
    script = insert_after(
        script,
        "        unset _OLD_VIRTUAL_PATH",
        f'        {VAR_NAME}="${{_OLD_{VAR_NAME}}}"; export {VAR_NAME}; unset _OLD_{VAR_NAME}; unset AMENT_INDEX_PREFIX',
    )
    SCRIPT_FILE.write_text(script)
    print("updated")


def restore() -> None:
    if not SCRIPT_FILE.exists():
        print(f"{SCRIPT_FILE} does not exist")
        return
    script = SCRIPT_FILE.read_text()
    if VAR_NAME not in script:
        print("nothing to do")
        return
    script = remove_line_if_includes(script, VAR_NAME)
    SCRIPT_FILE.write_text(script + "\n")
    print("restored")


def show_library_path() -> None:
    prefix = os.environ["VIRTUAL_ENV"]
    vendors = glob.glob(os.path.join(prefix, "opt", "*"))
    print(":".join([os.path.join(p, "lib") for p in [prefix] + vendors]))


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--restore", action="store_true")
    group.add_argument("--path", action="store_true")
    args = parser.parse_args()
    if args.path:
        show_library_path()
    elif args.restore:
        restore()
    else:
        update()
