"""
tests/test_optimizer.py
Unit tests for backend/ai_engine.py — PromptTemplates, AIEngine config,
retry logic, and provider fallback.
"""

import pytest
import sys
import os
from unittest.mock import MagicMock, patch, PropertyMock
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ai_engine import (
    AIEngine,
    AIProvider,
    GenerationResult,
    ModelConfig,
    PromptTemplates,
)


# ─── Prompt template tests ────────────────────────────────────────────────────

class TestPromptTemplates:

    @pytest.fixture
    def templates(self):
        return PromptTemplates()

    def test_resume_optimizer_returns_tuple(self, templates):
        system, user = templates.resume_optimizer("Resume text", "JD text")
        assert isinstance(system, str)
        assert isinstance(user, str)

    def test_resume_optimizer_system_contains_key_concepts(self, templates):
        system, _ = templates.resume_optimizer("Resume", "JD")
        assert "ATS" in system
        assert "resume" in system.lower()

    def test_resume_optimizer_user_contains_both_texts(self, templates):
        _, user = templates.resume_optimizer("MY RESUME CONTENT", "MY JOB DESCRIPTION")
        assert "MY RESUME CONTENT" in user
        assert "MY JOB DESCRIPTION" in user

    def test_resume_optimizer_includes_instructions(self, templates):
        _, user = templates.resume_optimizer("Resume", "JD")
        # Check at least 5 numbered rules are present
        rule_count = sum(1 for i in range(1, 9) if f"{i}." in user)
        assert rule_count >= 5

    def test_skill_gap_analysis_returns_valid_prompts(self, templates):
        system, user = templates.skill_gap_analysis("Resume text", "JD text")
        assert len(system) > 20
        assert "skill" in user.lower() or "gap" in user.lower()

    def test_cover_letter_includes_company_name(self, templates):
        _, user = templates.cover_letter("Resume", "JD", "Google")
        assert "Google" in user

    def test_cover_letter_without_company_name(self, templates):
        _, user = templates.cover_letter("Resume", "JD")
        assert "Google" not in user  # should not invent company

    def test_interview_questions_includes_both_texts(self, templates):
        _, user = templates.interview_questions("JD Content", "Resume Content")
        assert "JD Content" in user or "Resume Content" in user

    def test_resume_optimizer_truncates_very_long_input(self, templates):
        long_resume = "Python developer. " * 500
        long_jd     = "Looking for Python developer. " * 500
        system, user = templates.resume_optimizer(long_resume, long_jd)
        # Prompts should not be infinitely long
        assert len(user) < 20_000


# ─── Model config tests ───────────────────────────────────────────────────────

class TestModelConfig:

    def test_defaults_are_sensible(self):
        config = ModelConfig(provider=AIProvider.GROQ, model_id="llama3-70b-8192")
        assert config.max_tokens == 4096
        assert config.temperature == 0.4
        assert config.stream is True
        assert config.timeout_seconds == 60

    def test_custom_values_set_correctly(self):
        config = ModelConfig(
            provider=AIProvider.OPENAI,
            model_id="gpt-4o",
            max_tokens=2000,
            temperature=0.7,
            stream=False,
        )
        assert config.provider == AIProvider.OPENAI
        assert config.model_id == "gpt-4o"
        assert config.max_tokens == 2000
        assert config.temperature == 0.7
        assert config.stream is False


# ─── Generation result tests ──────────────────────────────────────────────────

class TestGenerationResult:

    def test_result_defaults(self):
        result = GenerationResult(
            text="Hello world",
            provider=AIProvider.GROQ,
            model_id="llama3-70b-8192",
        )
        assert result.fallback_used is False
        assert result.tokens_used is None
        assert result.latency_ms is None

    def test_result_with_all_fields(self):
        result = GenerationResult(
            text="Optimized resume",
            provider=AIProvider.GROQ,
            model_id="llama3-70b-8192",
            tokens_used=1024,
            latency_ms=3500,
            fallback_used=False,
        )
        assert result.text == "Optimized resume"
        assert result.tokens_used == 1024
        assert result.latency_ms == 3500


# ─── AIEngine initialization tests ───────────────────────────────────────────

class TestAIEngineInit:

    def test_no_keys_marks_unavailable(self):
        engine = AIEngine(groq_api_key=None, openai_api_key=None)
        assert not engine.is_available
        assert engine.available_providers == []

    def test_invalid_key_handled_gracefully(self):
        # Should not raise — just log warning
        engine = AIEngine(groq_api_key="invalid-key", openai_api_key=None)
        # May or may not be available depending on Groq's constructor validation
        assert isinstance(engine.is_available, bool)

    def test_provider_order_groq_first(self):
        engine = AIEngine()
        order  = engine._build_provider_order(AIProvider.GROQ)
        assert order[0] == AIProvider.GROQ
        assert order[1] == AIProvider.OPENAI

    def test_provider_order_openai_first(self):
        engine = AIEngine()
        order  = engine._build_provider_order(AIProvider.OPENAI)
        assert order[0] == AIProvider.OPENAI
        assert order[1] == AIProvider.GROQ

    def test_adapt_config_swaps_model_for_openai(self):
        engine = AIEngine()
        config = ModelConfig(provider=AIProvider.GROQ, model_id="llama3-70b-8192")
        adapted = engine._adapt_config(config, AIProvider.OPENAI)
        assert adapted.provider == AIProvider.OPENAI
        assert adapted.model_id == AIEngine.DEFAULT_OPENAI_MODEL
        assert adapted.stream is False  # OpenAI fallback is non-streaming

    def test_adapt_config_same_provider_unchanged(self):
        engine = AIEngine()
        config = ModelConfig(provider=AIProvider.GROQ, model_id="llama3-70b-8192", temperature=0.7)
        adapted = engine._adapt_config(config, AIProvider.GROQ)
        assert adapted is config  # same object, no copy


# ─── Fallback behavior tests (mocked) ────────────────────────────────────────

class TestFallbackBehavior:

    def _make_engine_with_mock_clients(self, groq_result=None, openai_result=None,
                                        groq_raises=None, openai_raises=None):
        engine = AIEngine.__new__(AIEngine)
        engine._templates = PromptTemplates()
        engine._primary   = AIProvider.GROQ

        if groq_raises:
            mock_groq = MagicMock()
            mock_groq.generate.side_effect = groq_raises
            engine._groq = mock_groq
        elif groq_result is not None:
            mock_groq = MagicMock()
            mock_groq.generate.return_value = groq_result
            engine._groq = mock_groq
        else:
            engine._groq = None

        if openai_raises:
            mock_openai = MagicMock()
            mock_openai.generate.side_effect = openai_raises
            engine._openai = mock_openai
        elif openai_result is not None:
            mock_openai = MagicMock()
            mock_openai.generate.return_value = openai_result
            engine._openai = mock_openai
        else:
            engine._openai = None

        return engine

    def test_groq_success_no_fallback(self):
        expected = GenerationResult(text="Optimized resume", provider=AIProvider.GROQ, model_id="llama3-70b-8192")
        engine   = self._make_engine_with_mock_clients(groq_result=expected)
        config   = ModelConfig(provider=AIProvider.GROQ, model_id="llama3-70b-8192")
        result   = engine._generate_with_fallback("system", "user", config)
        assert result.text == "Optimized resume"
        assert result.fallback_used is False

    def test_groq_failure_falls_back_to_openai(self):
        openai_result = GenerationResult(text="OpenAI resume", provider=AIProvider.OPENAI, model_id="gpt-4o-mini")
        engine        = self._make_engine_with_mock_clients(
            groq_raises=ConnectionError("Groq down"),
            openai_result=openai_result,
        )
        config = ModelConfig(provider=AIProvider.GROQ, model_id="llama3-70b-8192")
        result = engine._generate_with_fallback("system", "user", config)
        assert result.text == "OpenAI resume"
        assert result.fallback_used is True

    def test_both_providers_fail_raises(self):
        engine = self._make_engine_with_mock_clients(
            groq_raises=ConnectionError("Groq down"),
            openai_raises=ConnectionError("OpenAI down"),
        )
        config = ModelConfig(provider=AIProvider.GROQ, model_id="llama3-70b-8192")
        with pytest.raises(RuntimeError, match="All AI providers failed"):
            engine._generate_with_fallback("system", "user", config)

    def test_no_providers_raises(self):
        engine = self._make_engine_with_mock_clients()  # both None
        config = ModelConfig(provider=AIProvider.GROQ, model_id="llama3-70b-8192")
        with pytest.raises(RuntimeError):
            engine._generate_with_fallback("system", "user", config)


# ─── Output validation tests ──────────────────────────────────────────────────

class TestOutputValidation:
    """Tests that validate the quality/format of generated prompts."""

    @pytest.fixture
    def templates(self):
        return PromptTemplates()

    SAMPLE_RESUME = """
    John Doe | john@example.com
    Senior Python Developer
    5 years experience with Django, FastAPI, PostgreSQL
    Led team of 4 engineers
    """

    SAMPLE_JD = """
    Looking for Senior Python Developer with 5+ years experience.
    Requirements: Python, Django or FastAPI, PostgreSQL, AWS, Docker.
    Nice to have: Kubernetes, machine learning experience.
    """

    def test_optimizer_prompt_includes_action_verb_instruction(self, templates):
        _, user = templates.resume_optimizer(self.SAMPLE_RESUME, self.SAMPLE_JD)
        user_lower = user.lower()
        assert "action verb" in user_lower or "action" in user_lower

    def test_optimizer_prompt_mentions_quantification(self, templates):
        _, user = templates.resume_optimizer(self.SAMPLE_RESUME, self.SAMPLE_JD)
        assert "quantif" in user.lower() or "metric" in user.lower() or "measur" in user.lower()

    def test_optimizer_prompt_mentions_ats(self, templates):
        _, user = templates.resume_optimizer(self.SAMPLE_RESUME, self.SAMPLE_JD)
        assert "ats" in user.lower()

    def test_optimizer_system_mentions_accuracy_constraint(self, templates):
        system, _ = templates.resume_optimizer(self.SAMPLE_RESUME, self.SAMPLE_JD)
        # Should warn against fabrication
        assert "fabricat" in system.lower() or "invent" in system.lower() or "never" in system.lower()