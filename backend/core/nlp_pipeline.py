"""
core/nlp_pipeline.py
Enterprise NLP Pipeline — sentence transformers, TF-IDF + embedding-based
keyword extraction, and domain skill extraction.
"""

from __future__ import annotations

import re
import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from loguru import logger


# ─── Data models ──────────────────────────────────────────────────────────────

@dataclass
class KeywordResult:
    term:       str
    tfidf_score: float
    frequency:  int
    is_high_value: bool = False


@dataclass
class NLPResult:
    matched_keywords:   List[str]
    missing_keywords:   List[str]
    jd_top_keywords:    List[str]
    resume_keywords:    List[str]
    semantic_score:     int          # 0-100
    keyword_score:      int          # 0-100
    extracted_skills:   List[str]
    jd_skills:          List[str]
    resume_skills:      List[str]
    ngrams_matched:     List[str]
    similarity_raw:     float        # 0.0-1.0


# ─── Stop words ────────────────────────────────────────────────────────────────

_STOP_WORDS: Set[str] = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "not", "no", "nor",
    "so", "yet", "both", "either", "neither", "each", "every", "all",
    "both", "few", "more", "most", "other", "some", "such", "than", "that",
    "this", "these", "those", "then", "there", "their", "they", "what",
    "which", "who", "whom", "when", "where", "why", "how", "as", "if",
    "while", "although", "because", "since", "until", "unless", "after",
    "before", "during", "about", "above", "below", "between", "into",
    "through", "under", "over", "also", "just", "only", "very", "too",
    "up", "down", "out", "off", "much", "many", "same", "own", "us", "our",
    "we", "i", "you", "he", "she", "it", "its", "his", "her", "my", "your",
    "eg", "ie", "etc", "per", "via",
}

# ─── Domain skill taxonomy ─────────────────────────────────────────────────────

SKILL_TAXONOMY: Dict[str, List[str]] = {
    "programming": [
        "python", "java", "javascript", "typescript", "golang", "rust", "c++",
        "c#", "ruby", "php", "scala", "kotlin", "swift", "r", "matlab",
        "bash", "shell", "powershell", "perl", "haskell", "elixir", "clojure",
    ],
    "web_frameworks": [
        "react", "nextjs", "vuejs", "angular", "svelte", "node.js", "express",
        "fastapi", "django", "flask", "spring", "laravel", "rails", "gatsby",
        "nuxt", "nestjs", "graphql", "rest", "grpc", "websocket",
    ],
    "data_engineering": [
        "apache spark", "kafka", "airflow", "dbt", "databricks", "snowflake",
        "bigquery", "redshift", "hive", "flink", "hadoop", "nifi", "luigi",
        "prefect", "dagster", "great expectations",
    ],
    "databases": [
        "postgresql", "mysql", "sqlite", "mongodb", "redis", "cassandra",
        "elasticsearch", "neo4j", "dynamodb", "firestore", "clickhouse",
        "timescaledb", "cockroachdb", "planetscale",
    ],
    "cloud": [
        "aws", "gcp", "azure", "s3", "ec2", "lambda", "rds", "eks", "ecs",
        "cloud run", "app engine", "azure functions", "cloudflare",
        "heroku", "vercel", "netlify",
    ],
    "devops": [
        "kubernetes", "docker", "terraform", "ansible", "helm", "jenkins",
        "github actions", "gitlab ci", "circle ci", "argocd", "istio",
        "prometheus", "grafana", "datadog", "splunk", "new relic",
    ],
    "ml_ai": [
        "pytorch", "tensorflow", "scikit-learn", "keras", "hugging face",
        "transformers", "langchain", "llm", "gpt", "bert", "openai",
        "mlflow", "kubeflow", "ray", "xgboost", "lightgbm", "catboost",
        "computer vision", "nlp", "reinforcement learning", "fine-tuning",
    ],
    "soft_skills": [
        "leadership", "communication", "collaboration", "agile", "scrum",
        "cross-functional", "stakeholder", "mentoring", "problem-solving",
        "analytical", "strategic", "entrepreneurial",
    ],
}

_ALL_SKILLS: Set[str] = {skill for skills in SKILL_TAXONOMY.values() for skill in skills}


# ─── TF-IDF implementation ─────────────────────────────────────────────────────

class TFIDF:
    """
    Lightweight TF-IDF without sklearn dependency.
    Designed for 2-document corpora (resume + JD).
    """

    @staticmethod
    def tokenize(text: str) -> List[str]:
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s\-\./]", " ", text)
        tokens = text.split()
        return [t for t in tokens if t not in _STOP_WORDS and len(t) > 1]

    @staticmethod
    def tf(tokens: List[str]) -> Dict[str, float]:
        if not tokens:
            return {}
        count = Counter(tokens)
        total = len(tokens)
        return {term: freq / total for term, freq in count.items()}

    @staticmethod
    def idf(documents: List[List[str]]) -> Dict[str, float]:
        """IDF scores across a corpus of token lists."""
        n = len(documents)
        idf: Dict[str, float] = {}
        all_terms = {term for doc in documents for term in doc}
        for term in all_terms:
            df = sum(1 for doc in documents if term in doc)
            idf[term] = math.log((n + 1) / (df + 1)) + 1.0
        return idf

    @staticmethod
    def tfidf_scores(
        doc_tokens: List[str],
        corpus_tokens: List[List[str]],
    ) -> Dict[str, float]:
        tf  = TFIDF.tf(doc_tokens)
        idf = TFIDF.idf(corpus_tokens)
        return {term: tf.get(term, 0) * idf.get(term, 0) for term in tf}


# ─── Embedding similarity (pure numpy fallback) ────────────────────────────────

class EmbeddingSimilarity:
    """
    Semantic similarity without heavy dependencies.
    Uses sentence-level TF-IDF cosine similarity as a lightweight proxy.
    For production, swap with sentence-transformers.
    """

    def __init__(self) -> None:
        self._transformer_model: Optional[object] = None
        self._try_load_transformer()

    def _try_load_transformer(self) -> None:
        """Attempt to load sentence-transformers if available."""
        try:
            from sentence_transformers import SentenceTransformer
            self._transformer_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("EmbeddingSimilarity: sentence-transformers loaded.")
        except ImportError:
            logger.info("EmbeddingSimilarity: sentence-transformers not installed, using TF-IDF cosine fallback.")

    def similarity(self, text_a: str, text_b: str) -> float:
        """Returns cosine similarity in [0, 1]."""
        if self._transformer_model is not None:
            return self._transformer_similarity(text_a, text_b)
        return self._tfidf_cosine(text_a, text_b)

    def _transformer_similarity(self, text_a: str, text_b: str) -> float:
        try:
            import numpy as np
            emb = self._transformer_model.encode([text_a[:1500], text_b[:1500]])
            cos = float(np.dot(emb[0], emb[1]) / (np.linalg.norm(emb[0]) * np.linalg.norm(emb[1]) + 1e-9))
            return max(0.0, min(1.0, cos))
        except Exception as exc:
            logger.warning("Transformer similarity failed: {} — falling back.", exc)
            return self._tfidf_cosine(text_a, text_b)

    def _tfidf_cosine(self, text_a: str, text_b: str) -> float:
        """TF-IDF cosine similarity — no external dependencies."""
        tokens_a = TFIDF.tokenize(text_a)
        tokens_b = TFIDF.tokenize(text_b)
        scores_a = TFIDF.tfidf_scores(tokens_a, [tokens_a, tokens_b])
        scores_b = TFIDF.tfidf_scores(tokens_b, [tokens_a, tokens_b])
        vocab    = set(scores_a) | set(scores_b)
        if not vocab:
            return 0.0
        vec_a = [scores_a.get(t, 0.0) for t in vocab]
        vec_b = [scores_b.get(t, 0.0) for t in vocab]
        dot   = sum(a * b for a, b in zip(vec_a, vec_b))
        norm  = math.sqrt(sum(x**2 for x in vec_a)) * math.sqrt(sum(x**2 for x in vec_b))
        return dot / (norm + 1e-9)


# ─── Main NLP Pipeline ─────────────────────────────────────────────────────────

class NLPPipeline:
    """
    Enterprise NLP Pipeline.
    Combines TF-IDF keyword extraction, embedding-based semantic scoring,
    and domain skill taxonomy for structured resume analysis.
    """

    MAX_KEYWORDS     = 40
    NGRAM_SIZES      = [1, 2, 3]

    def __init__(self) -> None:
        self._similarity = EmbeddingSimilarity()

    # ── Public API ────────────────────────────────────────────────────────────

    def analyze(self, resume_text: str, jd_text: str) -> NLPResult:
        logger.info("NLPPipeline.analyze() | resume={}w jd={}w",
                    len(resume_text.split()), len(jd_text.split()))

        # Tokenize
        resume_tokens = TFIDF.tokenize(resume_text)
        jd_tokens     = TFIDF.tokenize(jd_text)

        # TF-IDF keyword extraction
        jd_scores     = TFIDF.tfidf_scores(jd_tokens,     [resume_tokens, jd_tokens])
        resume_scores = TFIDF.tfidf_scores(resume_tokens, [resume_tokens, jd_tokens])

        # Top JD keywords
        top_jd_kws = self._top_keywords(jd_scores, jd_tokens, self.MAX_KEYWORDS)

        # Match / missing
        resume_token_set = set(resume_tokens)
        matched  = [kw for kw in top_jd_kws if kw.lower() in resume_token_set]
        missing  = [kw for kw in top_jd_kws if kw.lower() not in resume_token_set]

        # N-gram matching (bigrams + trigrams)
        ngrams_matched = self._match_ngrams(resume_text, jd_text)
        # Add matched ngrams to matched list
        for ng in ngrams_matched:
            if ng not in matched:
                matched.append(ng)
                if ng in missing:
                    missing.remove(ng)

        # Semantic similarity
        similarity = self._similarity.similarity(resume_text, jd_text)
        semantic_score = int(min(100, max(0, similarity * 100)))

        # Keyword score
        total = max(len(matched) + len(missing), 1)
        keyword_score = int(min(100, 100 * len(matched) / total))

        # Skill extraction
        jd_skills     = self._extract_skills(jd_text)
        resume_skills = self._extract_skills(resume_text)
        all_skills    = list(set(jd_skills + resume_skills))

        return NLPResult(
            matched_keywords=matched[:30],
            missing_keywords=missing[:20],
            jd_top_keywords=top_jd_kws[:30],
            resume_keywords=self._top_keywords(resume_scores, resume_tokens, 30),
            semantic_score=semantic_score,
            keyword_score=keyword_score,
            extracted_skills=all_skills,
            jd_skills=jd_skills,
            resume_skills=resume_skills,
            ngrams_matched=ngrams_matched,
            similarity_raw=similarity,
        )

    # ── Keyword helpers ───────────────────────────────────────────────────────

    def _top_keywords(
        self, scores: Dict[str, float], tokens: List[str], n: int
    ) -> List[str]:
        """Return top-n terms by TF-IDF score, filtering noise."""
        freq = Counter(tokens)
        sorted_terms = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        result: List[str] = []
        seen: Set[str] = set()
        for term, score in sorted_terms:
            if len(result) >= n:
                break
            if (
                term in _STOP_WORDS
                or len(term) <= 1
                or not re.match(r"[a-z]", term)
            ):
                continue
            if term not in seen:
                result.append(term)
                seen.add(term)
        return result

    # ── N-gram matching ───────────────────────────────────────────────────────

    def _match_ngrams(self, resume_text: str, jd_text: str) -> List[str]:
        """Find bigram and trigram phrases from JD that appear in resume."""
        def ngrams(tokens: List[str], n: int) -> List[str]:
            return [" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]

        resume_lower = resume_text.lower()
        jd_tokens    = TFIDF.tokenize(jd_text)
        matched: List[str] = []

        for n in [2, 3]:
            for gram in ngrams(jd_tokens, n):
                if gram in matched:
                    continue
                if gram in resume_lower:
                    matched.append(gram)

        return matched[:15]

    # ── Skill extraction ──────────────────────────────────────────────────────

    def _extract_skills(self, text: str) -> List[str]:
        """
        Extract domain skills from text using the skill taxonomy.
        Returns skills sorted by category, deduped.
        """
        text_lower = text.lower()
        found: List[str] = []

        for category, skills in SKILL_TAXONOMY.items():
            for skill in skills:
                # Whole-word match
                pattern = rf"\b{re.escape(skill)}\b"
                if re.search(pattern, text_lower):
                    if skill not in found:
                        found.append(skill)

        return found

    # ── Keyword importance weighting ─────────────────────────────────────────

    def weight_keywords(
        self, keywords: List[str], jd_text: str
    ) -> List[KeywordResult]:
        """
        Assign importance weights to extracted keywords.
        High-value keywords get boosted scores.
        """
        jd_tokens = TFIDF.tokenize(jd_text)
        freq = Counter(jd_tokens)
        total = len(jd_tokens) or 1

        hv_pattern = re.compile(
            r"\b(python|java|kubernetes|aws|gcp|azure|machine learning|"
            r"deep learning|pytorch|tensorflow|react|leadership|senior|principal)\b",
            re.IGNORECASE,
        )

        results: List[KeywordResult] = []
        for kw in keywords:
            kw_tokens = TFIDF.tokenize(kw)
            kw_freq   = sum(freq.get(t, 0) for t in kw_tokens)
            tfidf_s   = kw_freq / total
            results.append(KeywordResult(
                term=kw,
                tfidf_score=round(tfidf_s, 4),
                frequency=kw_freq,
                is_high_value=bool(hv_pattern.search(kw)),
            ))

        return sorted(results, key=lambda r: (r.is_high_value, r.tfidf_score), reverse=True)