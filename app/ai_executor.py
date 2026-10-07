from sqlalchemy.orm import Session
from pydantic import ValidationError
from app.ai_tools import TOOL_REGISTRY
from app.models import UserDB, AIToolCallDB


def execute_tool(
    tool_name: str,
    current_user: UserDB,
    db: Session,
    arguments: dict | None = None,
    message_id: int | None = None,
):
    """
    Execute an AI-requested tool after authorization
    and record the execution.
    """

    if tool_name not in TOOL_REGISTRY:
        raise ValueError(f"Unknown tool: {tool_name}")

    tool_config = TOOL_REGISTRY[tool_name]

    allowed_roles = tool_config["allowed_roles"]

    if current_user.role not in allowed_roles:
        raise PermissionError(
            f"User role '{current_user.role}' "
            f"is not authorized to use '{tool_name}'"
        )

    # argument validation
    args_model = tool_config["args_model"]
    try:
        validated_arguments = args_model.model_validate(
            arguments or {}
        )
    except ValidationError as exc:
        raise ValueError(
            f"Invalid arguments for tool '{tool_name}': "
            f"{exc.errors()}"
        )

    tool_function = tool_config["function"]
    arguments = arguments or {}
    validated_data = validated_arguments.model_dump()
    try:
        result = tool_function(
            current_user=current_user,
            db=db,
            **validated_data,
        )

        if message_id is not None:
            tool_call = AIToolCallDB(
                message_id=message_id,
                tool_name=tool_name,
                arguments=arguments,
                result=result,
                status="success",
            )

            db.add(tool_call)
            db.commit()

        return result

    except Exception:
        if message_id is not None:
            tool_call = AIToolCallDB(
                message_id=message_id,
                tool_name=tool_name,
                arguments=arguments,
                result=None,
                status="failed",
            )

            db.add(tool_call)
            db.commit()

        raise