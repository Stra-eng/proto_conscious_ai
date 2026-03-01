import sys

from src.agent_core import AgentCore


def main() -> None:
    print("Proto-Conscious AI Assistant")
    print("Commands: 'exit' to quit | 'save <path>' to persist session")
    print("-" * 52)

    try:
        agent = AgentCore()
    except RuntimeError as e:
        print(f"Startup error: {e}")
        sys.exit(1)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSession ended.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit"):
            print("Goodbye.")
            break

        if user_input.lower().startswith("save "):
            path = user_input[5:].strip()
            agent.save_session(path)
            print(f"Session saved to {path}")
            continue

        response = agent.respond(user_input)
        print(f"\nAgent: {response}")


if __name__ == "__main__":
    main()
