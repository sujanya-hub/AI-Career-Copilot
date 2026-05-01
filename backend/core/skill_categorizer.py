"""
core/skill_categorizer.py — Taxonomy-based skill categorization.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .logger import get_logger

logger = get_logger("skill_categorizer")


# ── Taxonomy (frozensets for O(1) lookup) ─────────────────────────────────────

_LANGS: frozenset[str] = frozenset({
    "python", "java", "javascript", "typescript", "c", "c++", "c#", "go",
    "golang", "rust", "ruby", "php", "swift", "kotlin", "scala", "r",
    "matlab", "perl", "bash", "shell", "powershell", "sql", "plsql",
    "solidity", "dart", "elixir", "haskell", "clojure", "lua",
    "objective-c", "fortran", "cobol", "groovy", "vba", "assembly",
    "julia", "ocaml", "f#",
})

_FRAMEWORKS: frozenset[str] = frozenset({
    "react", "angular", "vue", "next.js", "nextjs", "nuxt", "svelte",
    "gatsby", "remix", "express", "fastapi", "flask", "django", "rails",
    "spring", "spring boot", "asp.net", "laravel", "symfony", "nestjs",
    "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn",
    "xgboost", "lightgbm", "hugging face", "transformers", "langchain",
    "pandas", "numpy", "scipy", "matplotlib", "seaborn", "plotly",
    "flutter", "react native", "ionic", "xamarin",
    "jest", "pytest", "junit", "mocha", "cypress", "selenium", "playwright",
    "graphql", "grpc", "celery", "kafka", "spark", "hadoop", "flink",
    "dbt", "airflow", "prefect", "luigi",
})

_TOOLS: frozenset[str] = frozenset({
    "aws", "azure", "gcp", "google cloud", "ec2", "s3", "lambda",
    "cloudformation", "terraform", "ansible", "puppet", "chef",
    "docker", "kubernetes", "k8s", "helm", "jenkins", "github actions",
    "gitlab ci", "circleci", "travis ci", "argo", "rancher",
    "mysql", "postgresql", "postgres", "mongodb", "redis", "elasticsearch",
    "cassandra", "dynamodb", "bigquery", "snowflake", "redshift",
    "oracle", "mssql", "sqlite", "neo4j", "firebase",
    "git", "github", "gitlab", "bitbucket", "jira", "confluence",
    "notion", "slack", "trello", "asana",
    "vscode", "intellij", "xcode", "linux", "unix", "nginx", "apache",
    "postman", "figma", "tableau", "power bi", "looker",
    "grafana", "datadog", "prometheus", "splunk", "new relic",
})

_SOFT: frozenset[str] = frozenset({
    "leadership", "communication", "teamwork", "collaboration",
    "problem solving", "problem-solving", "critical thinking",
    "time management", "adaptability", "creativity", "mentoring",
    "coaching", "conflict resolution", "decision making",
    "project management", "stakeholder management", "agile", "scrum",
    "kanban", "cross-functional", "analytical", "detail-oriented",
    "self-motivated", "proactive", "strategic thinking",
    "presentation", "negotiation", "empathy", "ownership",
    "accountability", "prioritization",
})

# Ordered taxonomy list — first match wins
_TAXONOMY: list[tuple[str, frozenset[str]]] = [
    ("programming_languages", _LANGS),
    ("frameworks",            _FRAMEWORKS),
    ("tools",                 _TOOLS),
    ("soft_skills",           _SOFT),
]


@dataclass
class CategorizedSkills:
    programming_languages: list[str] = field(default_factory=list)
    frameworks:            list[str] = field(default_factory=list)
    tools:                 list[str] = field(default_factory=list)
    soft_skills:           list[str] = field(default_factory=list)
    uncategorized:         list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, list[str]]:
        return {
            "Programming Languages":  self.programming_languages,
            "Frameworks & Libraries": self.frameworks,
            "Tools & Platforms":      self.tools,
            "Soft Skills":            self.soft_skills,
            "Other":                  self.uncategorized,
        }

    def total(self) -> int:
        return sum(len(v) for v in self.as_dict().values())


class SkillCategorizer:
    """
    Assigns keywords to skill taxonomy buckets.

    Uses exact match first (fast O(1) frozenset lookup) then
    falls back to substring/partial match so that compound phrases
    like "python programming" or "spring boot framework" are caught.
    """

    def categorize(self, keywords: list[str]) -> CategorizedSkills:
        result = CategorizedSkills()

        for kw in keywords:
            clean = kw.lower().strip()
            bucket = self._classify(clean)
            getattr(result, bucket).append(kw)

        logger.info(
            "Categorized %d keywords — langs=%d, frameworks=%d, tools=%d, soft=%d, other=%d",
            len(keywords),
            len(result.programming_languages),
            len(result.frameworks),
            len(result.tools),
            len(result.soft_skills),
            len(result.uncategorized),
        )
        return result

    @staticmethod
    def _classify(token: str) -> str:
        # 1. Exact match (O(1))
        for bucket, taxonomy in _TAXONOMY:
            if token in taxonomy:
                return bucket

        # 2. Partial/substring match — covers compound bigrams from TF-IDF
        for bucket, taxonomy in _TAXONOMY:
            for term in taxonomy:
                if term in token or token in term:
                    return bucket

        return "uncategorized"