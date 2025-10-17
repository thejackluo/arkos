import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from model_module.ArkModelNew import ArkModelLink, UserMessage, AIMessage, SystemMessage

from state_module.state import State
from state_module.state_registry import register_state

@register_state
class StateUser(State):
    type = "user"

    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self.is_terminal = True

    def check_transition_ready(self, context):
        return True

    def run(self, context, agent=None):
        return 
        # Instead of input(), read last user message from context
        user_messages = [m for m in context if isinstance(m, UserMessage)]
        if not user_messages:
            return None

        last_user_msg = user_messages[-1]
        content = last_user_msg.content.strip()

        if content.lower() == "exit":
            self.is_terminal = True
            return None

        return last_user_msg

