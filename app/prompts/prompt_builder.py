"""Builds prompts for each rewrite mode."""
from __future__ import annotations

from app.models.enums import PromptMode, ResultLanguage

_SHARED_GUARDRAILS = (
    "Return only the resulting text. "
    "Do not add explanations, labels, or commentary. "
    "Do not wrap the answer in quotation marks. "
    "Do not use bullet points unless the original text already used them."
)

_MODE_INSTRUCTIONS = {
    PromptMode.CORRECT_GRAMMAR: (
        "Correct the grammar, spelling, and obvious sentence-structure issues only. "
        "Keep the original meaning and tone unchanged."
    ),
    PromptMode.MAKE_IT_BETTER: (
        "Improve this text for clarity, fluency, and professionalism "
        "while keeping the original meaning. Make it sound natural."
    ),
    PromptMode.SUPER: (
        "Rewrite this text to be polished, professional, clear, and impactful "
        "while preserving the original intent."
    ),
}

_LANGUAGE_INSTRUCTIONS = {
    ResultLanguage.ENGLISH: "Return the final text in English.",
    ResultLanguage.CHINESE: "Return the final text in Chinese.",
    ResultLanguage.JAPANESE: "Return the final text in Japanese.",
    ResultLanguage.SWISS_GERMAN: (
        "Return the final text in Swiss Standard German using Swiss spelling "
        "conventions (for example, use 'ss' instead of 'ß')."
    ),
}


def build_system_prompt(
    mode: PromptMode,
    result_language: ResultLanguage = ResultLanguage.ENGLISH,
) -> str:
    return (
        f"{_MODE_INSTRUCTIONS[mode]} {_SHARED_GUARDRAILS} "
        f"{_LANGUAGE_INSTRUCTIONS[result_language]}"
    )


def build_user_prompt(text: str) -> str:
    return text
