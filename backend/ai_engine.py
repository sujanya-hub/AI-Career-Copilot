"""
AI Engine for Resume Analyzer — powered by Groq (LLaMA 3).
Handles resume optimization, professional summary generation,
and general LLM completions with retry logic.
"""

import json
import os
import re
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

try:
    from groq import Groq, APIConnectionError, APIStatusError, RateLimitError
except Exception:  # pragma: no cover - optional dependency
    Groq = None

    class APIConnectionError(Exception):
        pass

    class APIStatusError(Exception):
        status_code = 500
        message = "Groq unavailable"

    class RateLimitError(Exception):
        pass

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency
    OpenAI = None
from loguru import logger

# ── Constants ─────────────────────────────────────────────────────────────────

MODEL_ID = "llama3-70b-8192"
DEFAULT_TEMPERATURE = 0.4
DEFAULT_MAX_TOKENS = 4096
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2  # base delay; doubles on each retry

OPTIMIZATION_INSTRUCTIONS = {
    "light": (
        "Make minimal edits: fix grammar, tighten phrasing, and naturally incorporate "
        "the missing keywords where they fit. Do NOT restructure sections or invent content."
    ),
    "moderate": (
        "Rewrite bullet points to be stronger and more results-oriented. "
        "Incorporate missing keywords naturally. Add quantifiable achievements where "
        "the context clearly supports them. Preserve the original structure."
    ),
    "aggressive": (
        "Fully rewrite the resume for maximum ATS impact. Restructure sections, "
        "use strong action verbs, add measurable outcomes, and integrate ALL missing "
        "keywords throughout the document. Keep all facts truthful — do NOT invent "
        "companies, roles, dates, or skills that are not implied by the original text."
    ),
}


# ── AIEngine ──────────────────────────────────────────────────────────────────

class AIEngine:
    """
    Groq-backed AI engine for resume optimization and generation tasks.

    All public methods implement:
    - Structured prompt engineering
    - Retry logic with exponential back-off
    - Full loguru logging
    - Clean return contracts
    """

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY environment variable is not set. "
                "Export it before starting the server."
            )
        self.client = Groq(api_key=api_key)
        self.model = MODEL_ID
        logger.info(f"AIEngine initialized — model={self.model}")

    # ── Core Generation ───────────────────────────────────────────────────────

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> str:
        """
        Send a prompt to the Groq LLaMA 3 model and return the text response.

        Args:
            prompt:        User-turn content.
            system_prompt: Optional system-turn instruction.
            temperature:   Sampling temperature (default 0.4 for determinism).
            max_tokens:    Maximum tokens in the completion.

        Returns:
            The model's text response as a plain string.

        Raises:
            RuntimeError: If all retry attempts are exhausted.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt.strip()})
        messages.append({"role": "user", "content": prompt.strip()})

        last_exception: Optional[Exception] = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.debug(
                    f"Groq API call — attempt {attempt}/{MAX_RETRIES}, "
                    f"model={self.model}, temperature={temperature}, "
                    f"max_tokens={max_tokens}"
                )
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                text = response.choices[0].message.content.strip()
                logger.debug(
                    f"Groq response received — "
                    f"tokens_used={response.usage.total_tokens}"
                )
                return text

            except RateLimitError as e:
                wait = RETRY_DELAY_SECONDS * (2 ** (attempt - 1))
                logger.warning(
                    f"Rate limit hit on attempt {attempt}. "
                    f"Retrying in {wait}s... ({e})"
                )
                last_exception = e
                time.sleep(wait)

            except APIConnectionError as e:
                wait = RETRY_DELAY_SECONDS * attempt
                logger.warning(
                    f"Connection error on attempt {attempt}. "
                    f"Retrying in {wait}s... ({e})"
                )
                last_exception = e
                time.sleep(wait)

            except APIStatusError as e:
                logger.error(
                    f"Groq API status error {e.status_code} on attempt {attempt}: "
                    f"{e.message}"
                )
                last_exception = e
                if e.status_code < 500:
                    # 4xx errors won't be fixed by retrying
                    break
                time.sleep(RETRY_DELAY_SECONDS * attempt)

            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt}: {e}")
                last_exception = e
                break

        raise RuntimeError(
            f"Groq API call failed after {MAX_RETRIES} attempts. "
            f"Last error: {last_exception}"
        )

    # ── Resume Optimization ───────────────────────────────────────────────────

    def optimize(
        self,
        resume_text: str,
        parsed_resume: dict,
        job_description: str,
        missing_keywords: list,
        optimization_level: str = "moderate",
    ) -> dict:
        """
        Rewrite a resume to maximize ATS compatibility with a given job description.

        Args:
            resume_text:        Raw original resume text.
            parsed_resume:      Structured dict from ResumeParser.
            job_description:    Target role's job description.
            missing_keywords:   Keywords present in JD but absent in resume.
            optimization_level: One of 'light', 'moderate', 'aggressive'.

        Returns:
            {
                "optimized_resume": str,   # Full rewritten resume text
                "changes_made": list[str], # Human-readable list of edits
            }
        """
        if optimization_level not in OPTIMIZATION_INSTRUCTIONS:
            logger.warning(
                f"Unknown optimization_level='{optimization_level}', "
                f"defaulting to 'moderate'."
            )
            optimization_level = "moderate"

        level_instruction = OPTIMIZATION_INSTRUCTIONS[optimization_level]

        keywords_str = (
            ", ".join(missing_keywords)
            if missing_keywords
            else "None identified — focus on general ATS improvements."
        )

        sections_overview = "\n".join(
            f"  - {k}: {str(v)[:120]}..." if len(str(v)) > 120 else f"  - {k}: {v}"
            for k, v in parsed_resume.items()
        )

        system_prompt = """You are an expert resume writer and ATS optimization specialist
with 15+ years of experience helping candidates land interviews at top companies.

Your role:
- Optimize resumes for Applicant Tracking Systems (ATS) without fabricating information
- Strengthen language using industry-standard action verbs
- Integrate keywords naturally so the resume reads well for human reviewers too
- Never invent companies, titles, dates, degrees, or skills not implied by the original

You always respond in valid JSON. No prose outside the JSON block."""

        prompt = f"""
## Task
Optimize the resume below for the given job description.
Optimization level: **{optimization_level.upper()}**

### Level Instructions
{level_instruction}

---

## Original Resume
{resume_text}

---

## Job Description
{job_description}

---

## Parsed Resume Sections
{sections_overview}

---

## Missing Keywords to Integrate
{keywords_str}

---

## Instructions
1. Rewrite the resume following the optimization level instructions.
2. Integrate the missing keywords naturally — do NOT just append them as a list.
3. Add specific, believable metrics (e.g., "reduced load time by 30%") ONLY where
   the original text implies a quantifiable achievement.
4. Maintain the original chronological structure.
5. Use strong past-tense action verbs (Led, Built, Designed, Optimized, etc.).
6. Ensure the output is clean, ATS-parseable plain text.

## Response Format (strict JSON, no extra keys)
{{
  "optimized_resume": "<full rewritten resume as plain text>",
  "changes_made": [
    "<short description of change 1>",
    "<short description of change 2>",
    ...
  ]
}}
"""

        logger.info(
            f"Starting resume optimization — level={optimization_level}, "
            f"missing_keywords={len(missing_keywords)}"
        )

        try:
            raw_response = self.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.35,
                max_tokens=DEFAULT_MAX_TOKENS,
            )
            result = self._parse_json_response(raw_response)

            # Validate required keys
            if "optimized_resume" not in result:
                raise ValueError(
                    "Model response missing 'optimized_resume' key."
                )
            if "changes_made" not in result or not isinstance(
                result["changes_made"], list
            ):
                result["changes_made"] = ["Resume rewritten for ATS optimization."]

            logger.info(
                f"Optimization complete — "
                f"changes={len(result['changes_made'])}, "
                f"output_length={len(result['optimized_resume'])} chars"
            )
            return result

        except Exception as e:
            logger.error(f"Resume optimization failed: {e}")
            # Graceful degradation — return original with error note
            return {
                "optimized_resume": resume_text,
                "changes_made": [
                    f"Optimization failed due to an AI engine error: {str(e)}"
                ],
            }

    # ── Professional Summary ──────────────────────────────────────────────────

    def generate_summary(
        self,
        parsed_resume: dict,
        job_description: Optional[str] = None,
        max_sentences: int = 4,
    ) -> str:
        """
        Generate a concise professional summary tailored to a job description.

        Args:
            parsed_resume:   Structured resume sections from ResumeParser.
            job_description: Optional target JD for tighter alignment.
            max_sentences:   Target length of the summary (default 4).

        Returns:
            A polished professional summary string.
        """
        sections_text = "\n".join(
            f"{k}: {v}" for k, v in parsed_resume.items()
            if k.lower() not in {"summary", "objective"}
        )

        jd_context = (
            f"\n\n## Target Job Description\n{job_description}"
            if job_description
            else ""
        )

        system_prompt = (
            "You are a professional resume writer. "
            "Write concise, impactful professional summaries in plain text. "
            "No bullet points. No markdown. No JSON. Just the summary paragraph."
        )

        prompt = f"""
## Task
Write a {max_sentences}-sentence professional summary for this candidate.

## Resume Sections
{sections_text}
{jd_context}

## Guidelines
- Lead with years of experience and primary specialty
- Highlight 2–3 strongest technical or domain skills
- Mention a key achievement or impact if inferable from the resume
- Align language with the job description when provided
- Avoid generic filler phrases ("results-driven", "team player")
- Write in third-person professional tone
- Output the summary paragraph only — no labels, no extra text
"""

        logger.info("Generating professional summary.")
        try:
            summary = self.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.45,
                max_tokens=300,
            )
            # Strip any accidental labels the model might prepend
            summary = re.sub(
                r"^(professional summary[:\-]?\s*)",
                "",
                summary,
                flags=re.IGNORECASE,
            ).strip()
            logger.info(
                f"Summary generated — {len(summary.split())} words"
            )
            return summary
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return "Experienced professional with a strong background in the relevant field."

    # ── Internal Helpers ──────────────────────────────────────────────────────

    def _parse_json_response(self, raw: str) -> dict:
        """
        Extract and parse a JSON object from a model response that may contain
        surrounding prose or markdown code fences.

        Args:
            raw: Raw string from the LLM.

        Returns:
            Parsed Python dict.

        Raises:
            ValueError: If no valid JSON object can be extracted.
        """
        # Strip markdown fences
        cleaned = re.sub(r"```(?:json)?", "", raw).strip()
        cleaned = cleaned.replace("```", "").strip()

        # Try direct parse first
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Attempt to extract the outermost JSON object
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Could not parse JSON from model response. Error: {e}\n"
                    f"Raw (truncated): {cleaned[:400]}"
                )

        raise ValueError(
            f"No JSON object found in model response. "
            f"Raw (truncated): {cleaned[:400]}"
        )


class AIProvider(str, Enum):
    GROQ = "groq"
    OPENAI = "openai"


@dataclass
class ModelConfig:
    provider: AIProvider
    model_id: str
    max_tokens: int = 4096
    temperature: float = 0.4
    stream: bool = True
    timeout_seconds: int = 60


@dataclass
class GenerationResult:
    text: str
    provider: AIProvider
    model_id: str
    tokens_used: int | None = None
    latency_ms: int | None = None
    fallback_used: bool = False


class PromptTemplates:
    MAX_PROMPT_CHARS = 12000

    def _truncate(self, text: str) -> str:
        clean = (text or "").strip()
        if len(clean) <= self.MAX_PROMPT_CHARS:
            return clean
        return clean[: self.MAX_PROMPT_CHARS] + "\n\n[truncated]"

    def resume_optimizer(
        self,
        resume_text: str,
        job_description: str,
        missing_keywords: list[str] | None = None,
        optimization_level: str = "moderate",
    ) -> tuple[str, str]:
        keywords = ", ".join(missing_keywords or []) or "No explicit missing keywords provided."
        system = (
            "You are an elite ATS resume writer and recruiter-calibrated career coach. "
            "You improve resumes without inventing facts and you always return valid JSON."
        )
        user = f"""
Optimize this resume for the target job description.

1. Preserve truthfulness and chronology.
2. Strengthen bullets with action verbs.
3. Make impact clearer with believable metrics only when supported.
4. Naturally integrate missing keywords.
5. Keep the output ATS-friendly and plain text.
6. Prioritize recruiter readability, not keyword stuffing.
7. Improve summary, skills, and experience where appropriate.
8. Return strict JSON only.

Optimization level: {optimization_level}
Missing keywords: {keywords}

Resume:
{self._truncate(resume_text)}

Job Description:
{self._truncate(job_description)}

JSON schema:
{{
  "optimized_resume": "full rewritten resume",
  "changes_made": ["change 1", "change 2"],
  "before_after_sections": [
    {{
      "section": "summary",
      "before": "old text",
      "after": "new text",
      "injected_keywords": ["python"]
    }}
  ]
}}
"""
        return system, user

    def recruiter_feedback(
        self,
        resume_text: str,
        job_description: str,
        analysis_snapshot: dict[str, Any] | None = None,
    ) -> tuple[str, str]:
        system = (
            "You are a sharp FAANG-level recruiter. Be honest, concise, and evidence-based. "
            "Return strict JSON only."
        )
        user = f"""
Review this candidate like a real recruiter.

Resume:
{self._truncate(resume_text)}

Job Description:
{self._truncate(job_description)}

Analysis snapshot:
{json.dumps(analysis_snapshot or {}, ensure_ascii=True)[:3000]}

Return JSON:
{{
  "strengths": ["bullet", "bullet"],
  "weaknesses": ["bullet", "bullet"],
  "hiring_decision": "Reject | Maybe | Strong Hire",
  "recruiter_verdict": "one-line verdict"
}}
"""
        return system, user

    def bullet_improver(
        self,
        bullet_text: str,
        resume_text: str,
        job_description: str,
        section: str = "experience",
    ) -> tuple[str, str]:
        system = (
            "You rewrite resume bullets for maximum recruiter impact. "
            "Use STAR framing, strong verbs, and recruiter clarity. Return strict JSON."
        )
        user = f"""
Improve this resume bullet from the {section} section.

Original bullet:
{bullet_text}

Candidate resume context:
{self._truncate(resume_text)}

Target job description:
{self._truncate(job_description)}

Return JSON:
{{
  "original_bullet": "original",
  "improved_bullet": "rewritten bullet",
  "rationale": ["point 1", "point 2"],
  "metrics_hint": "what metric could be added",
  "star_hint": "situation-task-action-result angle"
}}
"""
        return system, user

    def keyword_injection(
        self,
        resume_text: str,
        job_description: str,
        missing_keywords: list[str],
        sections: dict[str, str],
    ) -> tuple[str, str]:
        system = (
            "You are a resume tailoring assistant. Insert missing keywords naturally into the best sections. "
            "Return strict JSON only."
        )
        user = f"""
Inject these missing keywords into the resume without keyword stuffing.

Missing keywords: {", ".join(missing_keywords) or "None"}
Resume:
{self._truncate(resume_text)}

Job Description:
{self._truncate(job_description)}

Current sections:
{json.dumps(sections, ensure_ascii=True)[:4000]}

Return JSON:
{{
  "sections": [
    {{
      "section": "summary",
      "before": "old section text",
      "after": "rewritten section text",
      "injected_keywords": ["python", "aws"]
    }}
  ]
}}
"""
        return system, user

    def resume_chat(
        self,
        history: list[dict[str, str]],
        question: str,
        analysis_snapshot: dict[str, Any] | None = None,
    ) -> tuple[str, str]:
        system = (
            "You are an AI Career Copilot. Answer clearly, specifically, and actionably using the resume/JD context. "
            "Return strict JSON only."
        )
        user = f"""
Conversation history:
{json.dumps(history[-8:], ensure_ascii=True)}

Analysis snapshot:
{json.dumps(analysis_snapshot or {}, ensure_ascii=True)[:3500]}

User question:
{question}

Return JSON:
{{
  "answer": "helpful answer",
  "follow_up_questions": ["question 1", "question 2"]
}}
"""
        return system, user

    def job_fit_predictor(
        self,
        resume_text: str,
        job_description: str | None = None,
    ) -> tuple[str, str]:
        system = (
            "You infer the five best-fit roles for a candidate. "
            "Return strict JSON with recruiter-style reasoning."
        )
        user = f"""
Candidate resume:
{self._truncate(resume_text)}

Optional target job description:
{self._truncate(job_description or "")}

Return JSON:
{{
  "roles": [
    {{
      "role": "Machine Learning Engineer",
      "match_score": 84,
      "rationale": "why this fits",
      "missing_signals": ["signal 1"]
    }}
  ]
}}
"""
        return system, user

    def skill_gap_analysis(self, resume_text: str, job_description: str) -> tuple[str, str]:
        system = "You analyze skill gaps between a resume and a job description."
        user = (
            "Identify the biggest skill gaps and opportunities.\n\n"
            f"Resume:\n{self._truncate(resume_text)}\n\n"
            f"Job Description:\n{self._truncate(job_description)}"
        )
        return system, user

    def cover_letter(
        self,
        resume_text: str,
        job_description: str,
        company_name: str | None = None,
    ) -> tuple[str, str]:
        company_line = f"Company: {company_name}\n" if company_name else ""
        system = "You write concise, tailored cover letters."
        user = (
            f"{company_line}"
            f"Resume:\n{self._truncate(resume_text)}\n\n"
            f"Job Description:\n{self._truncate(job_description)}"
        )
        return system, user

    def interview_questions(self, job_description: str, resume_text: str) -> tuple[str, str]:
        system = "You prepare targeted interview questions."
        user = (
            f"Job Description:\n{self._truncate(job_description)}\n\n"
            f"Resume:\n{self._truncate(resume_text)}"
        )
        return system, user


class _GroqProviderClient:
    def __init__(self, api_key: str):
        if Groq is None:
            raise RuntimeError("groq package not installed")
        self.client = Groq(api_key=api_key)

    def generate(self, system_prompt: str, user_prompt: str, config: ModelConfig) -> GenerationResult:
        start = time.perf_counter()
        response = self.client.chat.completions.create(
            model=config.model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
        elapsed = int((time.perf_counter() - start) * 1000)
        usage = getattr(response, "usage", None)
        return GenerationResult(
            text=response.choices[0].message.content.strip(),
            provider=AIProvider.GROQ,
            model_id=config.model_id,
            tokens_used=getattr(usage, "total_tokens", None),
            latency_ms=elapsed,
        )


class _OpenAIProviderClient:
    def __init__(self, api_key: str):
        if OpenAI is None:
            raise RuntimeError("openai package not installed")
        self.client = OpenAI(api_key=api_key)

    def generate(self, system_prompt: str, user_prompt: str, config: ModelConfig) -> GenerationResult:
        start = time.perf_counter()
        response = self.client.chat.completions.create(
            model=config.model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
        elapsed = int((time.perf_counter() - start) * 1000)
        usage = getattr(response, "usage", None)
        tokens = getattr(usage, "total_tokens", None) if usage else None
        return GenerationResult(
            text=response.choices[0].message.content.strip(),
            provider=AIProvider.OPENAI,
            model_id=config.model_id,
            tokens_used=tokens,
            latency_ms=elapsed,
        )


class AIEngine:
    DEFAULT_GROQ_MODEL = "llama3-70b-8192"
    DEFAULT_OPENAI_MODEL = "gpt-4o-mini"

    def __init__(
        self,
        groq_api_key: str | None = None,
        openai_api_key: str | None = None,
        primary_provider: AIProvider = AIProvider.GROQ,
    ) -> None:
        self._templates = PromptTemplates()
        self._primary = primary_provider
        self._groq = None
        self._openai = None

        groq_key = groq_api_key or os.getenv("GROQ_API_KEY")
        openai_key = openai_api_key or os.getenv("OPENAI_API_KEY")

        if groq_key:
            try:
                self._groq = _GroqProviderClient(groq_key)
            except Exception as exc:
                logger.warning(f"Groq provider unavailable: {exc}")
        if openai_key:
            try:
                self._openai = _OpenAIProviderClient(openai_key)
            except Exception as exc:
                logger.warning(f"OpenAI provider unavailable: {exc}")

        logger.info(
            "AIEngine ready | providers=%s primary=%s",
            self.available_providers,
            self._primary.value,
        )

    @property
    def available_providers(self) -> list[AIProvider]:
        providers: list[AIProvider] = []
        if self._groq is not None:
            providers.append(AIProvider.GROQ)
        if self._openai is not None:
            providers.append(AIProvider.OPENAI)
        return providers

    @property
    def is_available(self) -> bool:
        return bool(self.available_providers)

    def _build_provider_order(self, preferred: AIProvider) -> list[AIProvider]:
        if preferred == AIProvider.OPENAI:
            return [AIProvider.OPENAI, AIProvider.GROQ]
        return [AIProvider.GROQ, AIProvider.OPENAI]

    def _adapt_config(self, config: ModelConfig, provider: AIProvider) -> ModelConfig:
        if config.provider == provider:
            return config
        if provider == AIProvider.OPENAI:
            return ModelConfig(
                provider=AIProvider.OPENAI,
                model_id=self.DEFAULT_OPENAI_MODEL,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                stream=False,
                timeout_seconds=config.timeout_seconds,
            )
        return ModelConfig(
            provider=AIProvider.GROQ,
            model_id=self.DEFAULT_GROQ_MODEL,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            stream=config.stream,
            timeout_seconds=config.timeout_seconds,
        )

    def _generate_with_fallback(
        self,
        system_prompt: str,
        user_prompt: str,
        config: ModelConfig,
    ) -> GenerationResult:
        errors: list[str] = []
        for provider in self._build_provider_order(config.provider):
            client = self._groq if provider == AIProvider.GROQ else self._openai
            if client is None:
                continue
            adapted = self._adapt_config(config, provider)
            try:
                result = client.generate(system_prompt, user_prompt, adapted)
                result.fallback_used = provider != config.provider
                return result
            except Exception as exc:
                errors.append(f"{provider.value}: {exc}")
                logger.warning(f"AI provider {provider.value} failed: {exc}")
        raise RuntimeError(f"All AI providers failed: {' | '.join(errors) or 'none configured'}")

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.4,
        max_tokens: int = 4096,
        provider: AIProvider | None = None,
    ) -> str:
        if not self.is_available:
            raise RuntimeError("No AI providers are configured.")
        config = ModelConfig(
            provider=provider or self._primary,
            model_id=self.DEFAULT_GROQ_MODEL if (provider or self._primary) == AIProvider.GROQ else self.DEFAULT_OPENAI_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        result = self._generate_with_fallback(system_prompt or "You are a helpful assistant.", prompt, config)
        return result.text

    def _safe_json(self, raw: str) -> dict[str, Any]:
        cleaned = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if not match:
                raise
            return json.loads(match.group(0))

    def _generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        preferred_provider: AIProvider = AIProvider.GROQ,
    ) -> dict[str, Any]:
        config = ModelConfig(
            provider=preferred_provider,
            model_id=self.DEFAULT_GROQ_MODEL if preferred_provider == AIProvider.GROQ else self.DEFAULT_OPENAI_MODEL,
        )
        result = self._generate_with_fallback(system_prompt, user_prompt, config)
        return self._safe_json(result.text)

    def optimize_resume(
        self,
        resume_text: str,
        job_description: str,
        missing_keywords: list[str],
        optimization_level: str = "moderate",
    ) -> dict[str, Any]:
        if not self.is_available:
            return self._fallback_optimize(resume_text, missing_keywords)
        try:
            system_prompt, user_prompt = self._templates.resume_optimizer(
                resume_text,
                job_description,
                missing_keywords,
                optimization_level,
            )
            data = self._generate_json(system_prompt, user_prompt)
            return {
                "optimized_resume": data.get("optimized_resume", resume_text),
                "changes_made": data.get("changes_made", ["Improved bullet phrasing and keyword coverage."]),
                "before_after_sections": data.get("before_after_sections", []),
            }
        except Exception as exc:
            logger.warning(f"optimize_resume fallback triggered: {exc}")
            return self._fallback_optimize(resume_text, missing_keywords)

    def recruiter_feedback(
        self,
        resume_text: str,
        job_description: str,
        analysis_snapshot: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self.is_available:
            return self._fallback_recruiter_feedback(analysis_snapshot or {})
        try:
            system_prompt, user_prompt = self._templates.recruiter_feedback(
                resume_text,
                job_description,
                analysis_snapshot,
            )
            data = self._generate_json(system_prompt, user_prompt)
            return {
                "strengths": data.get("strengths", []),
                "weaknesses": data.get("weaknesses", []),
                "hiring_decision": data.get("hiring_decision", "Maybe"),
                "recruiter_verdict": data.get("recruiter_verdict", "Promising profile with clear room to sharpen positioning."),
            }
        except Exception as exc:
            logger.warning(f"recruiter_feedback fallback triggered: {exc}")
            return self._fallback_recruiter_feedback(analysis_snapshot or {})

    def improve_bullet(
        self,
        resume_text: str,
        job_description: str,
        bullet_text: str,
        section: str = "experience",
    ) -> dict[str, Any]:
        if not self.is_available:
            return self._fallback_bullet_improvement(bullet_text)
        try:
            system_prompt, user_prompt = self._templates.bullet_improver(
                bullet_text,
                resume_text,
                job_description,
                section,
            )
            data = self._generate_json(system_prompt, user_prompt)
            return {
                "original_bullet": data.get("original_bullet", bullet_text),
                "improved_bullet": data.get("improved_bullet", bullet_text),
                "rationale": data.get("rationale", []),
                "metrics_hint": data.get("metrics_hint"),
                "star_hint": data.get("star_hint"),
            }
        except Exception as exc:
            logger.warning(f"improve_bullet fallback triggered: {exc}")
            return self._fallback_bullet_improvement(bullet_text)

    def inject_keywords(
        self,
        resume_text: str,
        job_description: str,
        missing_keywords: list[str],
        sections: dict[str, str],
    ) -> list[dict[str, Any]]:
        if not self.is_available:
            return self._fallback_keyword_injection(sections, missing_keywords)
        try:
            system_prompt, user_prompt = self._templates.keyword_injection(
                resume_text,
                job_description,
                missing_keywords,
                sections,
            )
            data = self._generate_json(system_prompt, user_prompt)
            return data.get("sections", [])
        except Exception as exc:
            logger.warning(f"inject_keywords fallback triggered: {exc}")
            return self._fallback_keyword_injection(sections, missing_keywords)

    def chat_resume(
        self,
        history: list[dict[str, str]],
        question: str,
        analysis_snapshot: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self.is_available:
            return self._fallback_chat(question, analysis_snapshot or {})
        try:
            system_prompt, user_prompt = self._templates.resume_chat(history, question, analysis_snapshot)
            data = self._generate_json(system_prompt, user_prompt)
            return {
                "answer": data.get("answer", "Focus on the highest-impact gaps first."),
                "follow_up_questions": data.get("follow_up_questions", []),
            }
        except Exception as exc:
            logger.warning(f"chat_resume fallback triggered: {exc}")
            return self._fallback_chat(question, analysis_snapshot or {})

    def predict_roles(self, resume_text: str, job_description: str | None = None) -> list[dict[str, Any]]:
        if not self.is_available:
            return self._fallback_roles(resume_text)
        try:
            system_prompt, user_prompt = self._templates.job_fit_predictor(resume_text, job_description)
            data = self._generate_json(system_prompt, user_prompt)
            return data.get("roles", [])
        except Exception as exc:
            logger.warning(f"predict_roles fallback triggered: {exc}")
            return self._fallback_roles(resume_text)

    def _fallback_optimize(self, resume_text: str, missing_keywords: list[str]) -> dict[str, Any]:
        lines = [line.rstrip() for line in resume_text.splitlines()]
        optimized_lines: list[str] = []
        changes = [
            "Strengthened phrasing with cleaner action verbs.",
            "Preserved original facts while improving ATS readability.",
        ]
        if missing_keywords:
            changes.append(f"Created room to reference missing keywords such as {', '.join(missing_keywords[:4])}.")
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(("-", "*", "•")):
                cleaned = stripped.lstrip("-*• ").strip()
                if not re.match(r"^(Led|Built|Designed|Developed|Delivered|Optimized|Improved|Launched|Owned)\b", cleaned, re.IGNORECASE):
                    cleaned = f"Delivered {cleaned[:1].lower() + cleaned[1:]}" if cleaned else cleaned
                optimized_lines.append(f"- {cleaned}")
            else:
                optimized_lines.append(line)
        return {
            "optimized_resume": "\n".join(optimized_lines).strip() or resume_text,
            "changes_made": changes,
            "before_after_sections": [],
        }

    def _fallback_recruiter_feedback(self, analysis_snapshot: dict[str, Any]) -> dict[str, Any]:
        score = int(analysis_snapshot.get("ats_score", 0))
        matched = analysis_snapshot.get("matched_keywords", []) or []
        missing = analysis_snapshot.get("missing_keywords", []) or []
        strengths = []
        weaknesses = []
        if score >= 75:
            strengths.append("The resume shows enough role-relevant evidence to justify an interview loop.")
        if len(matched) >= 8:
            strengths.append(f"Keyword and capability coverage is solid with {len(matched)} aligned signals.")
        if analysis_snapshot.get("has_metrics"):
            strengths.append("Impact is easier to trust because the resume includes quantified outcomes.")
        if len(missing) >= 5:
            weaknesses.append(f"Too many critical requirements are not visible yet: {', '.join(missing[:5])}.")
        if score < 60:
            weaknesses.append("The narrative is not yet strong enough for a recruiter to confidently push this forward.")
        if not analysis_snapshot.get("has_metrics"):
            weaknesses.append("Bullets read task-heavy rather than outcome-heavy, which weakens seniority perception.")

        if score >= 80:
            decision = "Strong Hire"
            verdict = "Strong signal overall; the profile feels interview-worthy for this lane."
        elif score >= 62:
            decision = "Maybe"
            verdict = "There is real potential here, but the positioning still needs tightening."
        else:
            decision = "Reject"
            verdict = "The resume does not yet prove enough fit for this role."

        return {
            "strengths": strengths[:4] or ["Relevant background is visible, but not fully maximized."],
            "weaknesses": weaknesses[:4] or ["Some role-fit evidence still needs to be made explicit."],
            "hiring_decision": decision,
            "recruiter_verdict": verdict,
        }

    def _fallback_bullet_improvement(self, bullet_text: str) -> dict[str, Any]:
        clean = bullet_text.strip().lstrip("-*• ").strip()
        improved = clean
        if clean and not re.match(r"^(Led|Built|Designed|Developed|Optimized|Improved|Delivered|Launched|Owned)\b", clean, re.IGNORECASE):
            improved = f"Delivered {clean[:1].lower() + clean[1:]}"
        if not re.search(r"\d", improved):
            improved += " while improving a measurable business or engineering outcome."
        return {
            "original_bullet": bullet_text,
            "improved_bullet": improved,
            "rationale": [
                "Front-loaded the bullet with a stronger action verb.",
                "Shifted the phrasing toward impact instead of responsibility only.",
            ],
            "metrics_hint": "Add a metric such as speed, revenue, conversion, time saved, cost saved, or scale.",
            "star_hint": "Clarify the challenge, what you changed, and the result it produced.",
        }

    def _fallback_keyword_injection(self, sections: dict[str, str], missing_keywords: list[str]) -> list[dict[str, Any]]:
        if not sections:
            return []
        previews: list[dict[str, Any]] = []
        remaining = list(dict.fromkeys(missing_keywords))
        for section_name in ("summary", "skills", "experience"):
            before = (sections.get(section_name) or "").strip()
            if not before:
                continue
            injected = remaining[:2]
            if not injected:
                break
            if section_name == "skills":
                after = before + (", " if before and not before.endswith(",") else "") + ", ".join(injected)
            else:
                after = before + f"\nAdded emphasis on {', '.join(injected)} where it truthfully applies."
            previews.append(
                {
                    "section": section_name,
                    "before": before,
                    "after": after,
                    "injected_keywords": injected,
                }
            )
            remaining = remaining[2:]
        return previews

    def _fallback_chat(self, question: str, analysis_snapshot: dict[str, Any]) -> dict[str, Any]:
        lower = question.lower()
        missing = analysis_snapshot.get("missing_keywords", []) or []
        suggestions = analysis_snapshot.get("suggestions", []) or []
        if "skill" in lower and missing:
            answer = f"The biggest missing skills/signals right now are {', '.join(missing[:6])}. Prioritize the ones that appear in both the job requirements and your strongest real experience."
        elif "project" in lower:
            answer = "Make each project bullet show problem, stack, ownership, and measurable result. Recruiters want proof that your projects map to the role, not just that you built something interesting."
        elif "summary" in lower:
            answer = "Open with your years of experience, strongest domain fit, and one concrete impact signal. The summary should help a recruiter understand your lane in under 10 seconds."
        else:
            answer = suggestions[0] if suggestions else "Focus first on missing requirements, impact-heavy bullets, and a clearer skills section."
        return {
            "answer": answer,
            "follow_up_questions": [
                "Which section should I improve first?",
                "Can you rewrite one of my bullets?",
            ],
        }

    def _fallback_roles(self, resume_text: str) -> list[dict[str, Any]]:
        lower = resume_text.lower()
        role_bank = [
            ("Machine Learning Engineer", ["python", "pytorch", "tensorflow", "ml"]),
            ("Backend Engineer", ["python", "fastapi", "django", "api", "sql"]),
            ("Full Stack Engineer", ["react", "javascript", "typescript", "node", "api"]),
            ("Data Engineer", ["spark", "airflow", "kafka", "sql", "warehouse"]),
            ("Cloud / Platform Engineer", ["aws", "docker", "kubernetes", "terraform", "devops"]),
        ]
        predictions: list[dict[str, Any]] = []
        for role, signals in role_bank:
            hits = [signal for signal in signals if signal in lower]
            score = min(95, 45 + len(hits) * 12)
            predictions.append(
                {
                    "role": role,
                    "match_score": score,
                    "rationale": f"This role matches {len(hits)} visible signals in your resume: {', '.join(hits) or 'general engineering fit'}.",
                    "missing_signals": [signal for signal in signals if signal not in hits][:3],
                }
            )
        predictions.sort(key=lambda item: item["match_score"], reverse=True)
        return predictions[:5]
