from app.models.enums import PromptMode
from app.prompts.prompt_builder import build_system_prompt, build_user_prompt


def test_each_mode_has_distinct_instruction():
    prompts = {mode: build_system_prompt(mode) for mode in PromptMode}
    assert len(set(prompts.values())) == len(PromptMode)


def test_guardrails_present_in_every_mode():
    for mode in PromptMode:
        prompt = build_system_prompt(mode)
        assert "Return only" in prompt
        assert "Do not add explanations" in prompt


def test_user_prompt_passthrough():
    assert build_user_prompt("hello world") == "hello world"


def test_mode_label_roundtrip():
    for mode in PromptMode:
        assert PromptMode.from_label(mode.label) is mode
