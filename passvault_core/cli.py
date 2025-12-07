import argparse
from pathlib import Path
from .storage import create_vault, open_vault


def main():
    p = argparse.ArgumentParser(prog="passvault-core")
    sub = p.add_subparsers(dest="cmd")

    create = sub.add_parser("create")
    create.add_argument("path")
    create.add_argument("--password", required=True)

    show = sub.add_parser("show")
    show.add_argument("path")
    show.add_argument("--password", required=True)

    args = p.parse_args()
    if args.cmd == "create":
        create_vault(args.path, args.password)
        print(f"Created vault at {args.path}")
    elif args.cmd == "show":
        data = open_vault(args.path, args.password)
        print(data)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
