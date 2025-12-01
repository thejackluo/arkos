import sys
import os
from model_module.ArkModelNew import AIMessage

from state_module.state import State
from state_module.state_registry import register_state

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@register_state
class StateAct(State):
    type = "act"

    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self.is_terminal = False

    def check_transition_ready(self, context):
        return True

    def run(self, context, agent):
        plan = agent.context.get("last_reasoning")
        if plan is None:
            return AIMessage(content="No plan available.")

        action = plan.action

        if action == "reply":
            return AIMessage(content=plan.final)

     
        # NOTE: below will be filled in once tool state is finished
        # if action == "tool":
        #     tool_name = plan.action_input.get("tool")
        #     args = plan.action_input.get("args", {})
        #     tool = agent.tool_registry.pull_tool_from_registry(tool_name)
        #     result = tool.run(args)
        #     return AIMessage(content=f"Tool result: {result}")

        if action == "user":
            return AIMessage(content="Waiting for user input.")

        return AIMessage(content=plan.final)
