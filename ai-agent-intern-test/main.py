from app.agent import answer


def main():
    session_id = "cli-session"

    print("Aster & Row Support Agent")
    print("Type 'exit' to quit.")
    print()

    while True:
        message = input("You: ").strip()

        if message.lower() == "exit":
            print("Goodbye.")
            break

        if not message:
            continue

        result = answer(
            message,
            session_id=session_id
        )

        print("\nAgent:")
        print(result["answer"])

        if result.get("sources"):
            print("\nSources:")
            for source in result["sources"]:
                print(
                    f"- {source['file_name']} — "
                    f"{source['heading']}"
                )

        if result.get("handoff"):
            print("\nHuman assistance recommended.")

        print()


if __name__ == "__main__":
    main()