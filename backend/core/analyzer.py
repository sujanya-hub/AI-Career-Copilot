"""
core/analyzer.py — NLP analysis engine (production-hardened v3.1)

Scoring formula:
    ATS = 40% semantic (SentenceTransformer) + 30% TF-IDF cosine + 30% keyword overlap
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

import numpy as np

from .section_detector import SectionDetector, DetectedSections
from .skill_categorizer import SkillCategorizer, CategorizedSkills
from .jd_aligner import JDAligner, AlignmentResult
from .logger import get_logger

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

logger = get_logger("analyzer")


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}

# ── Built-in stopwords (no NLTK dependency) ───────────────────────────────────

_STOP_WORDS: frozenset[str] = frozenset({
    "a", "about", "above", "after", "again", "against", "all", "am", "an",
    "and", "any", "are", "as", "at", "be", "because", "been", "before",
    "being", "below", "between", "both", "but", "by", "can", "did", "do",
    "does", "doing", "don", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers",
    "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "is",
    "it", "its", "itself", "just", "me", "more", "most", "my", "myself", "no",
    "nor", "not", "now", "of", "off", "on", "once", "only", "or", "other",
    "our", "ours", "ourselves", "out", "over", "own", "s", "same", "she",
    "should", "so", "some", "such", "t", "than", "that", "the", "their",
    "theirs", "them", "themselves", "then", "there", "these", "they", "this",
    "those", "through", "to", "too", "under", "until", "up", "very", "was",
    "we", "were", "what", "when", "where", "which", "while", "who", "whom",
    "why", "will", "with", "you", "your", "yours", "yourself", "yourselves",
})

# ── scikit-learn ──────────────────────────────────────────────────────────────

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity as _cosine_similarity
    _SKLEARN_OK = True
except ImportError:
    _SKLEARN_OK = False
    logger.warning("scikit-learn not installed — TF-IDF scoring disabled.")


# ── Singleton model manager ───────────────────────────────────────────────────

class ModelManager:
    """Thread-safe lazy singleton for SentenceTransformer."""

    _instance: Optional["SentenceTransformer"] = None
    _load_attempted: bool = False

    @classmethod
    def get_model(cls) -> Optional["SentenceTransformer"]:
        if cls._load_attempted:
            return cls._instance
        cls._load_attempted = True
        if not _env_flag("ENABLE_SENTENCE_TRANSFORMER", default=False):
            logger.info(
                "SentenceTransformer disabled; set ENABLE_SENTENCE_TRANSFORMER=true to enable semantic embeddings."
            )
            return None
        try:
            from sentence_transformers import SentenceTransformer
            model_name = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2")
            local_only = _env_flag("SENTENCE_TRANSFORMER_LOCAL_ONLY", default=True)
            logger.info(
                "Loading SentenceTransformer model=%s local_only=%s",
                model_name,
                local_only,
            )
            cls._instance = SentenceTransformer(model_name, local_files_only=local_only)
            logger.info("SentenceTransformer ready.")
        except Exception as exc:
            logger.error("Failed to load embedding model: %s", exc)
            cls._instance = None
        return cls._instance


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class AnalysisResult:
    ats_score: int
    semantic_score: int
    tfidf_score: int
    keyword_score: int
    matched_keywords: list[str]
    missing_keywords: list[str]
    jd_top_keywords: list[str]
    resume_top_keywords: list[str]
    suggestions: list[str]
    resume_word_count: int
    jd_word_count: int
    warnings: list[str]
    sections: DetectedSections = field(default_factory=DetectedSections)
    categorized_skills: CategorizedSkills = field(default_factory=CategorizedSkills)
    alignment: AlignmentResult = field(default_factory=AlignmentResult)

    def to_json(self) -> str:
        return json.dumps(
            {
                "ats_score": self.ats_score,
                "semantic_score": self.semantic_score,
                "tfidf_score": self.tfidf_score,
                "keyword_score": self.keyword_score,
                "matched_keywords": self.matched_keywords,
                "missing_keywords": self.missing_keywords,
                "jd_top_keywords": self.jd_top_keywords,
                "resume_top_keywords": self.resume_top_keywords,
                "suggestions": self.suggestions,
                "resume_word_count": self.resume_word_count,
                "jd_word_count": self.jd_word_count,
                "warnings": self.warnings,
                "section_word_counts": self.sections.word_counts(),
                "skill_categories": {
                    k: v for k, v in self.categorized_skills.as_dict().items() if v
                },
                "alignment_gaps": self.alignment.gap_messages,
                "section_coverage": self.alignment.section_coverage,
            },
            indent=2,
        )


# ── Main analyzer ─────────────────────────────────────────────────────────────

class ResumeAnalyzer:
    """
    Full NLP analysis pipeline.
    Scoring: 40% embedding + 30% TF-IDF cosine + 30% keyword overlap.

    TfidfVectorizer instances are created once at __init__ and reused
    across all calls to avoid repeated vocabulary fitting overhead.
    """

    TOP_N_KEYWORDS = 30
    MIN_TOKEN_LEN = 3          # tokens shorter than this are filtered as noise

    def __init__(self) -> None:
        self._section_detector = SectionDetector()
        self._skill_categorizer = SkillCategorizer()
        self._jd_aligner = JDAligner()

        # Pre-built vectorizers — fitted lazily on first call, then reused
        self._similarity_vectorizer: Optional[TfidfVectorizer] = None
        self._keyword_vectorizer: Optional[TfidfVectorizer] = None

        if _SKLEARN_OK:
            self._similarity_vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),
                stop_words="english",
                max_features=8000,
                sublinear_tf=True,
            )
            self._keyword_vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),
                stop_words="english",
                max_features=150,
                sublinear_tf=True,
            )

    # ── Public API ────────────────────────────────────────────────────────────

    def analyze(
        self,
        resume_text: str,
        jd_text: str,
        warnings: Optional[list[str]] = None,
    ) -> AnalysisResult:
        warnings = list(warnings or [])

        if not resume_text.strip():
            raise ValueError("Resume text is empty.")
        if not jd_text.strip():
            raise ValueError("Job description text is empty.")

        resume_clean = self._preprocess(resume_text)
        jd_clean = self._preprocess(jd_text)

        semantic_score = self._semantic_similarity(resume_text, jd_text)
        tfidf_score = self._tfidf_similarity(resume_clean, jd_clean)

        resume_kw = self._extract_keywords(resume_clean)
        jd_kw = self._extract_keywords(jd_clean)
        matched, missing, kw_score = self._keyword_overlap(resume_kw, jd_kw)

        ats_score = max(0, min(100, int(round(
            0.40 * semantic_score + 0.30 * tfidf_score + 0.30 * kw_score
        ))))

        sections = self._section_detector.detect(resume_text)
        categorized = self._skill_categorizer.categorize(list(set(resume_kw)))
        alignment = self._jd_aligner.align(jd_kw[:self.TOP_N_KEYWORDS], sections)

        suggestions = self._build_suggestions(
            ats_score=ats_score,
            missing=missing,
            sections=sections,
            alignment=alignment,
            semantic_score=semantic_score,
            tfidf_score=tfidf_score,
        )

        logger.info(
            "ATS=%d (sem=%d, tfidf=%d, kw=%d) | matched=%d missing=%d",
            ats_score, semantic_score, tfidf_score, kw_score,
            len(matched), len(missing),
        )

        return AnalysisResult(
            ats_score=ats_score,
            semantic_score=semantic_score,
            tfidf_score=tfidf_score,
            keyword_score=kw_score,
            matched_keywords=sorted(matched),
            missing_keywords=sorted(missing),
            jd_top_keywords=jd_kw[: self.TOP_N_KEYWORDS],
            resume_top_keywords=resume_kw[: self.TOP_N_KEYWORDS],
            suggestions=suggestions,
            resume_word_count=len(resume_text.split()),
            jd_word_count=len(jd_text.split()),
            warnings=warnings,
            sections=sections,
            categorized_skills=categorized,
            alignment=alignment,
        )

    # ── Semantic similarity ────────────────────────────────────────────────────

    def _semantic_similarity(self, text1: str, text2: str) -> int:
        model = ModelManager.get_model()
        if model is None:
            return 50
        try:
            # all-MiniLM-L6-v2 max sequence length is 256 word-pieces.
            # Truncate to 400 whitespace tokens as a safe upper bound.
            t1 = " ".join(text1.split()[:400])
            t2 = " ".join(text2.split()[:400])
            embeddings = model.encode([t1, t2], show_progress_bar=False)
            norm = np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1]) + 1e-9
            cos = float(np.dot(embeddings[0], embeddings[1]) / norm)
            return int(round(max(0.0, min(1.0, cos)) * 100))
        except Exception as exc:
            logger.warning("Semantic scoring failed: %s", exc)
            return 50

    # ── TF-IDF cosine similarity ──────────────────────────────────────────────

    def _tfidf_similarity(self, text1: str, text2: str) -> int:
        if not _SKLEARN_OK or self._similarity_vectorizer is None:
            return 50
        try:
            matrix = self._similarity_vectorizer.fit_transform([text1, text2])
            score = float(_cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
            return int(round(score * 100))
        except Exception as exc:
            logger.warning("TF-IDF similarity failed: %s", exc)
            return 50

    # ── Keyword extraction ────────────────────────────────────────────────────

    def _extract_keywords(self, text: str) -> list[str]:
        if not _SKLEARN_OK or self._keyword_vectorizer is None:
            return self._fallback_keywords(text)
        try:
            tfidf = self._keyword_vectorizer.fit_transform([text])
            features = self._keyword_vectorizer.get_feature_names_out()
            scores = tfidf.toarray()[0]
            ranked = [
                features[i]
                for i in np.argsort(scores)[::-1]
                if self._is_valid_token(features[i])
            ]
            return ranked
        except Exception as exc:
            logger.warning("Keyword extraction failed: %s", exc)
            return self._fallback_keywords(text)

    def _fallback_keywords(self, text: str) -> list[str]:
        """Simple frequency-ranked fallback when scikit-learn is unavailable."""
        tokens = re.findall(r"\b[a-z][a-z0-9+#.\-]{2,}\b", text.lower())
        freq: dict[str, int] = {}
        for token in tokens:
            if self._is_valid_token(token):
                freq[token] = freq.get(token, 0) + 1
        return [w for w, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)]

    # ── Keyword overlap ───────────────────────────────────────────────────────

    def _keyword_overlap(
        self, resume_kw: list[str], jd_kw: list[str]
    ) -> tuple[list[str], list[str], int]:
        jd_set = set(jd_kw[: self.TOP_N_KEYWORDS])
        resume_set = set(resume_kw[: self.TOP_N_KEYWORDS])
        matched = sorted(jd_set & resume_set)
        missing = sorted(jd_set - resume_set)
        score = int(round(len(matched) / max(len(jd_set), 1) * 100))
        return matched, missing, score

    # ── Token validation (noise reduction) ───────────────────────────────────

    def _is_valid_token(self, token: str) -> bool:
        """Return False for stopwords, short tokens, and numeric-only strings."""
        if len(token) < self.MIN_TOKEN_LEN:
            return False
        if token in _STOP_WORDS:
            return False
        # Filter purely numeric tokens (e.g. "2023", "10")
        if re.fullmatch(r"[\d\s]+", token):
            return False
        return True

    # ── Preprocessing ──────────────────────────────────────────────────────────

    @staticmethod
    def _preprocess(text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s.#+\-]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    # ── Suggestions ──────────────────────────────────────────────────────────

    def _build_suggestions(
        self,
        ats_score: int,
        missing: list[str],
        sections: DetectedSections,
        alignment: AlignmentResult,
        semantic_score: int,
        tfidf_score: int,
    ) -> list[str]:
        sug: list[str] = []

        if missing:
            kw_str = ", ".join(f'"{k}"' for k in missing[:5])
            sug.append(
                f"Incorporate high-priority missing keywords: {kw_str}. "
                "Weave them naturally into your bullet points."
            )

        for msg in alignment.gap_messages[:2]:
            sug.append(f"Alignment fix — {msg}")

        if not sections.skills.strip():
            sug.append(
                "Add a dedicated 'Skills' section listing your technical and domain expertise. "
                "ATS parsers heavily weight this section."
            )
        if not sections.experience.strip():
            sug.append(
                "Ensure your Work Experience section is clearly labeled — "
                "ATS parsers rely on section headers to categorize content."
            )
        if not sections.education.strip():
            sug.append(
                "Add an Education section with degree, institution, and graduation year."
            )

        if semantic_score < 50:
            sug.append(
                "Your resume's language diverges significantly from the job description. "
                "Mirror the JD's terminology in your summary and experience bullets."
            )
        elif semantic_score < 70:
            sug.append(
                "Moderate semantic alignment detected. Strengthen your professional "
                "summary to reflect the role's core responsibilities."
            )

        if tfidf_score < 40:
            sug.append(
                "Low keyword density match. Increase the frequency of role-relevant "
                "terms throughout your resume without keyword stuffing."
            )

        if ats_score >= 80:
            sug.append(
                "Strong ATS profile. Ensure formatting is clean (no tables/columns) "
                "and the file is saved as a standard, text-based PDF."
            )
        elif ats_score < 45:
            sug.append(
                "Consider restructuring your resume to align more directly with the job "
                "description — use the exact terminology from the posting where applicable."
            )

        sug.append(
            "Quantify achievements with metrics wherever possible "
            "(e.g., 'Reduced load time by 40%', 'Led a team of 8')."
        )

        # Deduplicate while preserving insertion order
        seen: set[str] = set()
        unique: list[str] = []
        for s in sug:
            if s not in seen:
                seen.add(s)
                unique.append(s)
        return unique[:8]
