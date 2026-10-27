from app.agent import agent
from fastapi import FastAPI
from app.api import app as api_app

app = api_app


def main():

    print("=" * 60)
    print("Customer Support + CRM Agent")
    print("=" * 60)

    while True:

        question = input("\nYou: ")

        if question.lower() in [
            "exit",
            "quit",
            "bye"
        ]:
            print("Goodbye!")
            break

        try:

            response = agent.invoke({
                "messages": [
                    {
                        "role": "user",
                        "content": question
                    }
                ]
            })

            answer = response[
                "messages"
            ][-1].content

            print(
                f"\nAgent: {answer}"
            )

        except Exception as e:

            print(
                f"\nError: {e}"
            )


if __name__ == "__main__":
    main()