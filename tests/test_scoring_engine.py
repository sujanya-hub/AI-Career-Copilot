"""
tests/test_scoring_engine.py
Unit tests for backend/services/scoring_engine.py
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.services.scoring_engine import ScoringEngine, ATSScoreResult, SECTION_WEIGHTS


# ─── Fixtures ─────────────────────────────────────────────────────────────────

STRONG_RESUME = """
John Smith
john.smith@email.com | +1-555-0101 | San Francisco, CA
linkedin.com/in/johnsmith | github.com/johnsmith

SUMMARY
Senior Software Engineer with 7+ years of experience building scalable distributed systems
using Python, Kubernetes, and AWS. Led cross-functional teams of 5-8 engineers. 
Reduced API latency by 40% and increased system uptime to 99.99%.

EXPERIENCE
Senior Software Engineer — TechCorp Inc.
Jan 2020 – Present
• Led development of microservices architecture serving 2M+ daily active users
• Reduced infrastructure costs by 35% through Kubernetes optimization
• Built real-time data pipeline processing 500K events/second using Kafka and Python
• Mentored 4 junior engineers; drove adoption of code review best practices

Software Engineer — StartupXYZ
Mar 2018 – Dec 2019
• Developed RESTful APIs using Django and FastAPI
• Implemented CI/CD pipelines with GitHub Actions and Docker
• Improved test coverage from 40% to 85% across core services

SKILLS
Python, Java, Golang | Kubernetes, Docker, Terraform | AWS (EC2, S3, Lambda, RDS)
PostgreSQL, MongoDB, Redis | Apache Kafka, Spark | React, TypeScript
Machine Learning, PyTorch | Agile, Scrum, Leadership

EDUCATION
B.S. Computer Science — Stanford University, 2018
GPA: 3.8/4.0

CERTIFICATIONS
AWS Solutions Architect Professional (2023)
Certified Kubernetes Administrator (2022)
"""

WEAK_RESUME = """
Bob Jones
bob@mail.com

EXPERIENCE
Developer at Some Company 2020-2022
Did some coding stuff.
Worked on projects.

SKILLS
Python, Java

EDUCATION
BS Computer Science 2018
"""

STRONG_JD = """
Senior Software Engineer — Backend Platform

REQUIREMENTS (must have):
• 5+ years of experience in Python, Golang, or Java
• Strong experience with Kubernetes, Docker, and cloud platforms (AWS, GCP)
• Experience with distributed systems and microservices architecture
• Proficiency in SQL and NoSQL databases (PostgreSQL, MongoDB, Redis)
• Experience with Apache Kafka or similar message queues

PREFERRED:
• Experience with machine learning infrastructure
• Kubernetes certification (CKA/CKAD)
• Experience with CI/CD pipelines (GitHub Actions, Jenkins)
• Leadership and mentoring experience

RESPONSIBILITIES:
• Design and build highly scalable backend services
• Lead technical architecture discussions
• Mentor junior engineers
• Collaborate with product and data science teams
"""

SIMPLE_JD = """
Looking for a Python developer with some backend experience.
Must know SQL. Nice to have: React experience.
"""


# ─── Engine fixture ────────────────────────────────────────────────────────────

@pytest.fixture
def engine() -> ScoringEngine:
    return ScoringEngine()


# ─── Test cases ───────────────────────────────────────────────────────────────

class TestATSScorerBasics:

    def test_strong_resume_scores_high(self, engine):
        matched  = ["python", "kubernetes", "aws", "docker", "postgresql", "kafka", "leadership"]
        missing  = ["gcp"]
        result   = engine.score(STRONG_RESUME, STRONG_JD, matched, missing, semantic_similarity=0.78)

        assert isinstance(result, ATSScoreResult)
        assert result.overall_score >= 70, f"Expected >=70 but got {result.overall_score}"
        assert result.grade in ["A+", "A", "B"]

    def test_weak_resume_scores_low(self, engine):
        matched  = ["python"]
        missing  = ["kubernetes", "aws", "docker", "kafka", "postgresql", "golang", "leadership", "machine learning"]
        result   = engine.score(WEAK_RESUME, STRONG_JD, matched, missing, semantic_similarity=0.25)

        assert result.overall_score < 60, f"Expected <60 but got {result.overall_score}"
        assert result.grade in ["D", "F", "C"]

    def test_score_is_bounded(self, engine):
        matched = ["python"] * 30
        result  = engine.score(STRONG_RESUME, STRONG_JD, matched, [], semantic_similarity=1.0)
        assert 0 <= result.overall_score <= 100

    def test_zero_keywords_returns_sensible_score(self, engine):
        result = engine.score("John Doe", "Looking for developer.", [], [], semantic_similarity=0.1)
        assert 0 <= result.overall_score <= 100

    def test_section_scores_present(self, engine):
        matched = ["python", "kubernetes"]
        result  = engine.score(STRONG_RESUME, STRONG_JD, matched, ["aws"], semantic_similarity=0.7)
        assert "keyword_match"      in result.section_scores
        assert "semantic_alignment" in result.section_scores
        assert "skills_coverage"    in result.section_scores
        assert "experience_match"   in result.section_scores
        assert "structure_quality"  in result.section_scores

    def test_weights_sum_to_one(self):
        total = sum(SECTION_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001, f"Weights sum to {total}, expected 1.0"


class TestGrading:

    @pytest.mark.parametrize("score,expected_grade", [
        (95, "A+"),
        (85, "A"),
        (75, "B"),
        (65, "C"),
        (55, "D"),
        (30, "F"),
    ])
    def test_grade_mapping(self, engine, score, expected_grade):
        assert engine._grade(score) == expected_grade


class TestStructureScoring:

    def test_complete_resume_scores_higher(self, engine):
        score_strong = engine._structure_score(STRONG_RESUME)
        score_weak   = engine._structure_score(WEAK_RESUME)
        assert score_strong > score_weak

    def test_max_structure_score_is_100(self, engine):
        score = engine._structure_score(STRONG_RESUME)
        assert 0 <= score <= 100

    def test_empty_resume_returns_low_score(self, engine):
        score = engine._structure_score("")
        assert score <= 20


class TestExperienceScoring:

    def test_matching_seniority_scores_highest(self, engine):
        jd_senior    = "Senior Software Engineer, 5+ years experience required."
        resume_senior = "Senior Software Engineer with 7 years of experience."
        resume_junior = "Junior Developer, 1 year of experience."

        score_match  = engine._experience_score(resume_senior, jd_senior)
        score_under  = engine._experience_score(resume_junior, jd_senior)

        assert score_match > score_under

    def test_no_experience_requirements_returns_midrange(self, engine):
        score = engine._experience_score("Some professional.", "Looking for developer.")
        assert 30 <= score <= 90


class TestSkillsCoverage:

    def test_cloud_skills_detected(self, engine):
        resume = "Experienced with AWS, GCP, Kubernetes, Docker, Terraform."
        jd     = "Must have experience with AWS and Kubernetes."
        score  = engine._skills_coverage(resume, jd)
        assert score >= 80

    def test_no_jd_skills_returns_default(self, engine):
        score = engine._skills_coverage("Some resume text.", "Looking for a good person.")
        assert score == 60

    def test_empty_resume_scores_low(self, engine):
        score = engine._skills_coverage("", "Must know Python, AWS, and Kubernetes.")
        assert score <= 20


class TestHighValueKeywords:

    def test_high_value_keywords_detected(self, engine):
        matched = ["python", "kubernetes", "aws", "machine learning", "senior"]
        hv = engine._high_value_matched(matched)
        assert len(hv) >= 3
        assert "python" in hv or "kubernetes" in hv

    def test_no_high_value_returns_empty(self, engine):
        matched = ["teamwork", "communication", "detail-oriented"]
        hv = engine._high_value_matched(matched)
        assert len(hv) == 0


class TestConfidence:

    def test_long_texts_have_high_confidence(self, engine):
        conf = engine._confidence(STRONG_RESUME, STRONG_JD)
        assert conf >= 0.8

    def test_short_texts_have_low_confidence(self, engine):
        conf = engine._confidence("Short resume.", "Short JD.")
        assert conf < 0.5

    def test_confidence_bounded(self, engine):
        conf = engine._confidence(STRONG_RESUME * 5, STRONG_JD * 5)
        assert 0.0 <= conf <= 1.0


class TestKeywordScoring:

    def test_high_match_scores_high(self, engine):
        matched = ["python", "kubernetes", "aws", "docker", "sql"]
        missing = []
        score   = engine._keyword_score(matched, missing)
        assert score >= 90

    def test_no_matches_scores_low(self, engine):
        score = engine._keyword_score([], ["python", "java", "aws"])
        assert score == 0

    def test_empty_keyword_lists_returns_50(self, engine):
        score = engine._keyword_score([], [])
        assert score == 50


class TestIntegration:

    def test_full_pipeline_returns_valid_result(self, engine):
        matched = ["python", "kubernetes", "aws", "docker", "postgresql"]
        missing = ["golang", "gcp"]
        result  = engine.score(
            STRONG_RESUME, STRONG_JD, matched, missing, semantic_similarity=0.72
        )
        assert isinstance(result, ATSScoreResult)
        assert 0 <= result.overall_score <= 100
        assert result.improvement_delta >= 0
        assert result.improvement_delta <= 30
        assert 0.0 <= result.confidence <= 1.0
        assert len(result.section_scores) == 5

    def test_full_pipeline_with_weak_resume(self, engine):
        matched = ["python"]
        missing = ["kubernetes", "aws", "docker", "kafka", "golang"]
        result  = engine.score(
            WEAK_RESUME, STRONG_JD, matched, missing, semantic_similarity=0.20
        )
        assert result.overall_score < 65
        assert result.improvement_delta > 0