import sys
from talkenglish.middleware import PromptMiddleware

def main():
    if len(sys.argv) < 2:
        print("Usage: talkenglish '<prompt>'", file=sys.stderr)
        sys.exit(1)
    raw_prompt = sys.argv[1]
    middleware = PromptMiddleware()
    print(middleware.process(raw_prompt))

if __name__ == "__main__":
    main()
