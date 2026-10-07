import argparse
import sys
from talkenglish.middleware import PromptMiddleware

def parse_args(args=None):
    parser = argparse.ArgumentParser(
        prog="talkenglish",
        description="Prompt translation and refinement for software engineering agents."
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless CLI mode instead of interactive TUI."
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default=None,
        help="Prompt text to refine."
    )
    return parser.parse_args(args)

def run_cli(prompt: str) -> None:
    middleware = PromptMiddleware()
    print(middleware.process(prompt))

def main():
    args = parse_args()
    # Check if prompt provided via positional argument
    prompt = args.prompt

    # If stdin is piped and no prompt provided in args
    if prompt is None and not sys.stdin.isatty():
        prompt = sys.stdin.read().strip()

    # If --headless, or prompt given, or running non-interactively
    if args.headless or prompt is not None or not sys.stdin.isatty():
        if not prompt:
            print("Error: No prompt provided for headless mode.", file=sys.stderr)
            sys.exit(1)
        run_cli(prompt)
    else:
        from talkenglish.tui import run_tui
        run_tui()

if __name__ == "__main__":
    main()
