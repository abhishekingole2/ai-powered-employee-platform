import json
from sqlalchemy.orm import Session
from app.llm_provider import OllamaProvider
from app.ai_tools import TOOL_DEFINITIONS
from app.ai_executor import execute_tool
from app.models import (
    UserDB,
    AIConversationDB,
    AIMessageDB,
)
from app.prompts import SYSTEM_PROMPT, FEW_SHOT_EXAMPLES
llm_provider = OllamaProvider()


def build_llm_messages(
    conversation_history: list[dict],
) -> list[dict]:
    """
    Build the message structure that will eventually
    be sent to an LLM.
    """

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]

    for example in FEW_SHOT_EXAMPLES:
        messages.append(
            {
                "role": "user",
                "content": example["user"],
            }
        )

        messages.append(
            {
                "role": "assistant",
                "content": example["assistant"],
            }
        )

    messages.extend(conversation_history)

    return messages

def get_conversation_history(
    conversation_id: int,
    current_user: UserDB,
    db: Session,
) -> list[dict]:

    conversation = (
        db.query(AIConversationDB)
        .filter(AIConversationDB.id == conversation_id)
        .first()
    )

    if conversation is None:
        raise ValueError("Conversation not found")

    if conversation.user_id != current_user.id:
        raise PermissionError(
            "You do not have access to this conversation"
        )

    messages = (
        db.query(AIMessageDB)
        .filter(
            AIMessageDB.conversation_id == conversation_id
        )
        .order_by(AIMessageDB.id.asc())
        .all()
    )

    history = []

    for message in messages:

        history_message = {
            "role": message.role,
            "content": message.content,
        }

        if message.tool_calls_data:
            if message.role == "tool":
                history_message.update(message.tool_calls_data)
            else:
                history_message["tool_calls"] = message.tool_calls_data

        history.append(history_message)

    return history

def process_ai_request(
    user_message: str,
    current_user: UserDB,
    db: Session,
    conversation_id: int | None = None,
) -> dict:

    # ---------------------------------------------------------
    # 1. Find existing conversation or create a new one
    # ---------------------------------------------------------

    if conversation_id is not None:
        conversation = (
            db.query(AIConversationDB)
            .filter(AIConversationDB.id == conversation_id)
            .first()
        )

        if conversation is None:
            raise ValueError("Conversation not found")

        if conversation.user_id != current_user.id:
            raise PermissionError(
                "You do not have access to this conversation"
            )

    else:
        conversation = AIConversationDB(
            user_id=current_user.id,
            title=user_message[:200],
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # ---------------------------------------------------------
    # 2. Save user's message
    # ---------------------------------------------------------

    user_message_db = AIMessageDB(
        conversation_id=conversation.id,
        role="user",
        content=user_message,
    )

    db.add(user_message_db)
    db.commit()

    # ---------------------------------------------------------
    # 3. Get conversation history
    # ---------------------------------------------------------

    conversation_history = get_conversation_history(
        conversation_id=conversation.id,
        current_user=current_user,
        db=db,
    )

    # ---------------------------------------------------------
    # 4. Build messages for the LLM
    # ---------------------------------------------------------

    messages = build_llm_messages(conversation_history)

    # ---------------------------------------------------------
    # 5. Ask LLM whether a tool is needed
    # ---------------------------------------------------------

    llm_provider = OllamaProvider()
    llm_response = llm_provider.chat(
        messages=messages,
        tools=TOOL_DEFINITIONS,
    )

    assistant_response = llm_response.get("message", {})

    tool_calls = assistant_response.get("tool_calls", [])

    # ---------------------------------------------------------
    # 6. No tool required
    # ---------------------------------------------------------

    if not tool_calls:

        assistant_message = assistant_response.get(
            "content",
            "I could not generate a response.",
        )

        assistant_message_db = AIMessageDB(
            conversation_id=conversation.id,
            role="assistant",
            content=assistant_message,
        )

        db.add(assistant_message_db)
        db.commit()

        return {
            "conversation_id": conversation.id,
            "message": assistant_message,
            "tool_used": None,
            "data": None,
            "history": conversation_history,
        }

    # ---------------------------------------------------------
    # 7. Execute the first tool selected by the LLM
    # ---------------------------------------------------------

    tool_call = tool_calls[0]

    tool_name = tool_call["function"]["name"]

    tool_arguments = tool_call["function"].get(
        "arguments",
        {},
    )

    assistant_tool_message = AIMessageDB(
        conversation_id=conversation.id,
        role="assistant",
        content="",
        tool_calls_data=tool_calls,
    )

    db.add(assistant_tool_message)
    db.commit()
    db.refresh(assistant_tool_message)

    result = execute_tool(
        tool_name=tool_name,
        current_user=current_user,
        db=db,
        arguments=tool_arguments,
        message_id=assistant_tool_message.id,
    )

    # Save tool result in conversation history
    tool_message_db = AIMessageDB(
        conversation_id=conversation.id,
        role="tool",
        content=json.dumps(result),
        tool_calls_data={
            key: value
            for key, value in {
                "tool_name": tool_name,
                "tool_call_id": tool_call.get("id"),
            }.items()
            if value is not None
        },
    )
    db.add(tool_message_db)
    db.commit()

    updated_history = get_conversation_history(
        conversation_id=conversation.id,
        current_user=current_user,
        db=db,
    )

    messages = build_llm_messages(updated_history)


    # ---------------------------------------------------------
    # 9. Ask LLM for final natural-language response
    # ---------------------------------------------------------

    final_response = llm_provider.chat(
        messages=messages,
    )

    final_assistant_message = final_response.get(
        "message",
        {},
    ).get(
        "content",
        "I could not generate a response.",
    )

    # ---------------------------------------------------------
    # 10. Save final assistant response
    # ---------------------------------------------------------

    assistant_message_db = AIMessageDB(
        conversation_id=conversation.id,
        role="assistant",
        content=final_assistant_message,
    )

    db.add(assistant_message_db)
    db.commit()

    # ---------------------------------------------------------
    # 11. Return API response
    # ---------------------------------------------------------
    updated_history = get_conversation_history(
        conversation_id=conversation.id,
        current_user=current_user,
        db=db,
    )
    return {
        "conversation_id": conversation.id,
        "message": final_assistant_message,
        "tool_used": tool_name,
        "data": result,
        "history": updated_history,
    }
