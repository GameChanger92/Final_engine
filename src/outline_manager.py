# src/outline_manager.py
import argparse, json, pathlib, sys

def init_engine(args):
    anchors = json.loads(pathlib.Path(args.anchors_file).read_text())
    print(f"[✓] Init complete — episodes: {args.eps}, anchors: {len(anchors)}")

def main():
    parser = argparse.ArgumentParser(prog="outline_manager")
    sub = parser.add_subparsers(dest="cmd")

    p_init = sub.add_parser("init", help="Initialize project")
    p_init.add_argument("--eps", type=int, required=True)
    p_init.add_argument("--arc", type=int, required=True)
    p_init.add_argument("--load-anchors", dest="anchors_file", required=True)
    p_init.set_defaults(func=init_engine)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
