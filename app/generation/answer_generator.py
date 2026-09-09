from __future__ import annotations

from typing import Dict, List

from app.generation.llm_client import LLMClient
from app.generation.prompt_builder import PromptBuilder
from app.reasoning.context_builder import ContextBuilder


class AnswerGenerator:
    def __init__(
        self,
        llm: LLMClient | None = None,
        prompt_builder: PromptBuilder | None = None,
        context_builder: ContextBuilder | None = None,
    ) -> None:
        self.llm = llm or LLMClient()
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.context_builder = context_builder or ContextBuilder()

    def generate(self, question: str, evidence: List[Dict]) -> str:
        context = self.context_builder.build(evidence)
        prompt = self.prompt_builder.build_answer_prompt(question, context)
        return self.llm.generate(prompt, temperature=0.1)
