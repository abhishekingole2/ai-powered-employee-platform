from app.llm_provider import OllamaProvider
from app.ai_tools import TOOL_DEFINITIONS


def main():
    provider = OllamaProvider()

    messages = [
        {
            "role": "system",
            "content": (
                "You are an employee platform assistant. "
                "When the user asks about their projects, "
                "use the get_my_projects tool."
            ),
        },
        {
            "role": "user",
            "content": "What projects am I working on?",
        },
    ]

    response = provider.chat(
        messages=messages,
        tools=TOOL_DEFINITIONS,
    )

    return response


if __name__ == "__main__":
    main()
