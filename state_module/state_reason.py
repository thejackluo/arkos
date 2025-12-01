import sys
import os
from pydantic import BaseModel, Field
from model_module.ArkModelNew import AIMessage, SystemMessage

from state_module.state import State
from state_module.state_registry import register_state

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# 1. Pydantic structured plan
class ReasoningPlan(BaseModel):
    reasoning: str = ""
    action: str = "reply"
    action_input: dict = Field(default_factory=dict)
    final: str = ""


@register_state
class StateReason(State):
    type = "reason"

    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self.is_terminal = False

    def check_transition_ready(self, context):
        return True

    def run(self, context, agent):
        messages = context.get("messages", [])

        # 1. Visible free text reasoning
        reasoning_prompt = SystemMessage(content=
            "Produce visible chain of thought for the user. "
            "Do not produce any JSON. "
            "Do not produce any structured output."
        )

        visible_reasoning = agent.llm.generate_response(
            [reasoning_prompt] + messages
        )
        # visible_reasoning is shown to the user

        # 2. Strict JSON structured output (model never produces free text here)
        plan_prompt = SystemMessage(content=(
            "You are the planning module. "
            "Produce JSON only. "
            "Do not produce free text. "
            "Keys: reasoning, action, action_input, final."
        ))

        plan_schema = ReasoningPlan.model_json_schema()

        structured_output = agent.llm.generate_response(
            [plan_prompt] + messages,
            json_schema={
                "type": "json_schema",
                "json_schema": {
                    "name": "ReasoningPlan",
                    "schema": plan_schema
                }
            }
        )

        # structured_output is guaranteed to be valid according to the schema
        parsed_plan = ReasoningPlan.parse_raw(structured_output)

        # store plan for Act state
        agent.context["last_reasoning"] = parsed_plan

        return AIMessage(content=visible_reasoning)
