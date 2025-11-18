from openai import OpenAI
import re
import json
from typing import List
from ai_wayang_single.config.settings import DEBUGGER_MODEL_CONFIG
from ai_wayang_single.llm.prompt_loader import PromptLoader
from ai_wayang_single.llm.models import WayangPlan


class Debugger:
    """
    Debugger Agent based on OpenAI's GPT-models.
    The agent takes a failed Wayang plan and tries to fix it. Returns a fixed plan.

    """

    def __init__(
        self,
        model: str | None = None,
        reasoning: str | None = None,
        system_prompt: str | None = None,
        version: int | None = None,
    ):
        self.client = OpenAI()
        self.model = model or DEBUGGER_MODEL_CONFIG.get("model")
        self.reasoning = reasoning or DEBUGGER_MODEL_CONFIG.get("reason_effort")
        self.system_prompt = (
            system_prompt or PromptLoader().load_debugger_system_prompt()
        )
        self.version = version or 0
        self.chat = []

    def set_model_and_reasoning(self, model: str, reasoning: str) -> None:
        """
        Sets objects model and reasoning if any.
        Mostly for testing

        Args:
            model (str): GPT-model
            reasoning (str): Reasoning level if any

        """
        self.model = model
        self.reasoning = reasoning

    def get_version(self) -> int:
        """
        Get the iteration of the plan

        Returns:
            int: Plan version

        """

        return self.version

    def set_vesion(self, version: int) -> int:
        """
        Set the plan iteration or version

        Args:
            version (int): Plan version

        Returns:
            int: Plan version

        """

        # Sets plan version
        self.version = version

        return self.get_version()

    def debug_plan(
        self, query: str, plan: WayangPlan, wayang_errors: str, val_errors: List
    ):
        """
        Debug a failed plan and tries to return. a new one

        Args:
            query (str): The original natural-language user query
            plan (WayangPlan): The failed Wayang plan for debugging
            wayang_errors (str): The error given by the Wayang server if any
            val_errors (List): The error given by the PlanValidator if any

        Returns:
            A fixed plan

        """

        # increment version
        self.version += 1

        # Create new user prompt
        prompt = PromptLoader().load_debugger_prompt(
            query, plan, wayang_errors, val_errors
        )

        # Add user prompt to chat
        self.chat.append({"role": "user", "content": prompt})

        # Add model and current chat
        params = {"model": self.model, "input": self.chat, "text_format": WayangPlan}

        # Initialize effort
        effort = self.reasoning
        if effort:
            params["reasoning"] = {"effort": effort}

        # Generate response
        response = self.client.responses.parse(**params)

        # Format text answer from agent
        wayang_plan = response.output_parsed
        answer = PromptLoader().load_debugger_answer(wayang_plan)

        # Add agent answer to chat - necessary if another debug iteration is needed
        self.chat.append({"role": "assistant", "content": answer})

        # Return output
        return {"raw": response, "wayang_plan": wayang_plan, "version": self.version}

    def start_debugger(self) -> None:
        """
        Cleans the Debugger Agents chat so it only includes the system prompt

        """

        self.chat = [{"role": "system", "content": self.system_prompt}]
