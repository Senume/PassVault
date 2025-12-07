import argparse
from pathlib import Path
from .storage import create_vault, open_vault
import os


def main():
    p = argparse.ArgumentParser(prog="passvault-core")
    sub = p.add_subparsers(dest="cmd")

    create = sub.add_parser("create")
    create.add_argument("path")
    create.add_argument("--password", required=True)

    show = sub.add_parser("show")
    show.add_argument("path")
    show.add_argument("--password", required=True)

    listp = sub.add_parser("list")
    listp.add_argument("path")
    listp.add_argument("--password", required=True)

    addp = sub.add_parser("add")
    addp.add_argument("path")
    addp.add_argument("--password", required=True)
    addp.add_argument("--name", required=True)
    addp.add_argument("--username", required=False, default="")
    addp.add_argument("--password-field", required=False, default="")

    delp = sub.add_parser("delete")
    delp.add_argument("path")
    delp.add_argument("--password", required=True)
    delp.add_argument("--name", required=True, help="Name of the entry to delete")

    args = p.parse_args()
    if args.cmd == "create":
        create_vault(args.path, args.password)
        print(f"Created vault at {args.path}")
    elif args.cmd == "show":
        data = open_vault(args.path, args.password)
        print(data)
    elif args.cmd == "list":
        data = open_vault(args.path, args.password)
        items = data.get("items") if isinstance(data, dict) else None
        if not items:
            print("(no items)")
            return
        for idx, it in enumerate(items, start=1):
            name = it.get("name") if isinstance(it, dict) else str(it)
            user = it.get("username", "") if isinstance(it, dict) else ""
            print(f"{idx}. {name} {('<' + user + '>') if user else ''}")
    elif args.cmd == "add":
        # either create or append
        try:
            data = open_vault(args.path, args.password)
        except FileNotFoundError:
            data = {}
        if not isinstance(data, dict):
            data = {}
        items = data.setdefault("items", [])
        entry = {"name": args.name, "username": args.username, "password": args.password_field}
        items.append(entry)
        # if file existed, save_vault, else create_vault
        from .storage import save_vault

        if os.path.exists(args.path):
            save_vault(args.path, args.password, data)
            print(f"Added entry '{args.name}' to {args.path}")
        else:
            create_vault(args.path, args.password, initial_data=data)
            print(f"Created vault and added entry '{args.name}' to {args.path}")
    elif args.cmd == "delete":
        data = open_vault(args.path, args.password)
        if not isinstance(data, dict):
            print("Vault format unsupported")
            return
        items = data.get("items", [])
        new_items = [it for it in items if not (isinstance(it, dict) and it.get("name") == args.name)]
        if len(new_items) == len(items):
            print(f"No entry named '{args.name}' found")
            return
        data["items"] = new_items
        from .storage import save_vault
        save_vault(args.path, args.password, data)
        print(f"Deleted entry '{args.name}'")
    else:
        p.print_help()


if __name__ == "__main__":
    main()
