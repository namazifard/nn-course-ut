#!/usr/bin/env python3
import argparse, os, re
from pathlib import Path

def main():
    p = argparse.ArgumentParser(description="Bulk rename files/folders safely (deepest-first).")
    p.add_argument("root", nargs="?", default=".", help="Root folder (default: current).")
    p.add_argument("--from", dest="from_str", required=True, help="Text to replace (e.g., x or x_)")
    p.add_argument("--to", dest="to_str", required=True, help="Replacement text (e.g., y or y_)")
    p.add_argument("--mode", choices=["substring", "prefix"], default="substring",
                   help="substring = replace anywhere; prefix = only at start of name.")
    p.add_argument("--ext", action="append", default=[],
                   help="Limit to extension (e.g., .pdf). Repeat for multiple.")
    p.add_argument("--files-only", action="store_true", help="Rename files only.")
    p.add_argument("--dirs-only", action="store_true", help="Rename directories only.")
    p.add_argument("--ignore-case", action="store_true", help="Case-insensitive match.")
    p.add_argument("--apply", action="store_true", help="Do the renames (otherwise dry-run).")
    p.add_argument("--include-root", action="store_true", help="Allow renaming the root folder last.")
    args = p.parse_args()

    # Determine targets
    rename_files = True
    rename_dirs = True
    if args.files_only and not args.dirs_only:
        rename_dirs = False
    if args.dirs_only and not args.files_only:
        rename_files = False

    # Normalize extensions list
    exts = [e if e.startswith(".") else "." + e for e in args.ext]
    exts_lower = [e.lower() for e in exts]

    # Build regex
    flags = re.IGNORECASE if args.ignore_case else 0
    pat = re.escape(args.from_str)
    if args.mode == "prefix":
        pat = r"^" + pat
    rx = re.compile(pat, flags)

    def should_keep_by_ext(path: Path) -> bool:
        if not exts:
            return True
        if path.is_file():
            return path.name.lower().endswith(tuple(exts_lower))
        return True  # extension filter applies to files only

    def rename_one(path: Path) -> bool:
        if not should_keep_by_ext(path):
            return False
        base = path.name
        new_base = rx.sub(lambda m: args.to_str, base)
        if new_base == base:
            return False
        dst = path.with_name(new_base)
        if dst.exists():
            print(f"SKIP (exists): {path} -> {dst}")
            return False
        print(("REN " if args.apply else "DRY") + f": {path} -> {dst}")
        if args.apply:
            path.rename(dst)
        return True

    root = Path(args.root).resolve()

    # Walk deepest-first so children are renamed before parents
    for cur, dirs, files in os.walk(root, topdown=False):
        cur_path = Path(cur)
        if rename_files:
            for f in files:
                rename_one(cur_path / f)
        if rename_dirs:
            for d in dirs:
                rename_one(cur_path / d)

    if args.include_root and rename_dirs:
        rename_one(root)

    if not args.apply:
        print("\nDry run complete. Re-run with --apply to perform changes.")

if __name__ == "__main__":
    main()
    