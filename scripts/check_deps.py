#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.machinery
import subprocess
import sys
from pathlib import Path

from paper_summary_lib import DEFAULT_DEPS_TARGET, DEPENDENCIES


def module_available(module: str, search_path: Path | None = None) -> bool:
    if search_path is None:
        try:
            __import__(module)
            return True
        except ImportError:
            return False

    if not search_path.exists():
        return False
    return importlib.machinery.PathFinder.find_spec(module, [str(search_path)]) is not None


def check_dependencies(target: Path | None = None) -> dict[str, dict[str, bool]]:
    status: dict[str, dict[str, bool]] = {}
    for module in DEPENDENCIES:
        in_env = module_available(module)
        in_target = module_available(module, target) if target else False
        status[module] = {
            "env": in_env,
            "target": in_target,
            "available": in_env or in_target,
        }
    return status


def cmd_check(args: argparse.Namespace) -> int:
    target = Path(args.target).expanduser().resolve()
    status = check_dependencies(target)
    missing = [module for module, item in status.items() if not item["available"]]
    target_only = [module for module, item in status.items() if item["target"] and not item["env"]]

    print(f"Default dependency target: {target}")
    for module, item in status.items():
        meta = DEPENDENCIES[module]
        if item["env"]:
            state = "ok (current environment)"
        elif item["target"]:
            state = f"ok (target: {target})"
        else:
            state = "missing"
        print(f"{module}: {state} ({meta['purpose']}; package: {meta['package']})")

    if target_only:
        print()
        print(
            "Some dependencies are available only in the target directory. "
            "Run later commands with:"
        )
        print(f"PYTHONPATH={target} python3 scripts/paper_summary_cli.py ...")

    if missing:
        packages = " ".join(DEPENDENCIES[module]["package"] for module in missing)
        print()
        print(
            "Install missing packages with: "
            f"python3 scripts/check_deps.py install --target {target}"
        )
        print(f"Missing packages: {packages}")
        print(
            "Then run commands with: "
            f"PYTHONPATH={target} python3 scripts/paper_summary_cli.py ..."
        )
        return 1
    return 0


def cmd_install(args: argparse.Namespace) -> int:
    target = Path(args.target).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    status = check_dependencies(target)

    if args.all:
        modules = list(DEPENDENCIES)
    else:
        modules = [module for module, item in status.items() if not item["available"]]

    packages = [DEPENDENCIES[module]["package"] for module in modules]
    if not packages:
        print(
            "All dependencies are already available in the current Python environment "
            f"or target directory: {target}"
        )
        return 0

    cmd = [sys.executable, "-m", "pip", "install", "--target", str(target), *packages]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"Installed dependencies into {target}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check or install Summary-Papers dependencies.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="Check dependencies.")
    check.add_argument(
        "--target",
        default=DEFAULT_DEPS_TARGET,
        help=f"Dependency target directory to check (default: {DEFAULT_DEPS_TARGET}).",
    )
    check.set_defaults(func=cmd_check)

    install = subparsers.add_parser("install", help="Install missing dependencies.")
    install.add_argument("--target", default=DEFAULT_DEPS_TARGET)
    install.add_argument("--all", action="store_true")
    install.set_defaults(func=cmd_install)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
