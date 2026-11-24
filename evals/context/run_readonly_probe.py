#!/usr/bin/env python3
"""Run one permitted check on a read-only synthetic Linux project and return its streams."""
import argparse
import os
from pathlib import Path
import shutil
import stat
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="synthetic project exposed read-only at /project")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="-- executable and arguments")
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("supply the probe command")
    sandbox = shutil.which("bwrap")
    if sys.platform != "linux" or not sandbox:
        parser.error("Linux with Bubblewrap (bwrap) and user namespaces is required")
    try:
        project = args.project.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        parser.error(str(exc))
    if not project.is_dir() or project == Path("/"):
        parser.error("select an individual project directory")

    def fail_walk(error):
        raise error

    try:
        for directory, dirs, files in os.walk(project, onerror=fail_walk, followlinks=False):
            for name in dirs + files:
                item = Path(directory, name)
                mode = item.lstat().st_mode
                if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                    parser.error(f"select a static fixture with regular files and directories: {item}")
    except OSError as exc:
        parser.error(str(exc))

    flags = ["--unshare-all", "--unshare-user", "--disable-userns", "--die-with-parent",
             "--new-session", "--cap-drop", "ALL", "--clearenv", "--setenv", "PATH", "/usr/bin:/bin",
             "--setenv", "LANG", "C.UTF-8", "--setenv", "PYTHONDONTWRITEBYTECODE", "1"]
    for directory in ("/usr/bin", "/usr/lib", "/usr/lib64", "/bin", "/lib", "/lib64"):
        if Path(directory).is_dir():
            flags.extend(["--ro-bind", directory, directory])
    flags.extend(["--dev-bind", "/dev/null", "/dev/null", "--dir", "/tmp",
                  "--ro-bind", str(project), "/project", "--remount-ro", "/", "--chdir", "/project"])
    os.execve(sandbox, [sandbox, *flags, "--", *command], {"PATH": "/usr/bin:/bin"})


if __name__ == "__main__":
    main()
