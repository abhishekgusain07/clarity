from pathlib import Path

import pytest

from apply.mcp_servers.resume_mcp.corpus import ResumeCorpus


@pytest.fixture
def corpus(tmp_path) -> ResumeCorpus:
    # Build a self-contained corpus at a tmp_path; don't depend on real seed files
    profile = tmp_path / "profile.json"
    profile.write_text(
        '{"name":"Test User","email":"t@example.com","phone":"","linkedin_url":"",'
        '"github_url":"","portfolio_url":"","location":"Remote","work_auth":"",'
        '"salary_expectation_usd":null,"remote_preference":"REMOTE_OK"}'
    )
    resume = tmp_path / "resume.md"
    resume.write_text("# Test User\n\n## Skills\nPython, async.\n")
    samples = tmp_path / "voice_samples.json"
    samples.write_text(
        '{"version":1,"samples":['
        '{"id":"s1","kind":"cover_letter","text":"I love shipping reliable agent systems."},'
        '{"id":"s2","kind":"essay","text":"Debugging agents starts with a readable trace."}'
        "]}"
    )
    return ResumeCorpus(seed_dir=tmp_path)


def test_load_resume_markdown(corpus):
    md = corpus.resume_markdown()
    assert "Test User" in md
    assert "Python" in md


def test_get_profile_field_existing(corpus):
    assert corpus.profile_field("name") == "Test User"
    assert corpus.profile_field("location") == "Remote"


def test_get_profile_field_missing(corpus):
    assert corpus.profile_field("nonexistent") is None


def test_list_voice_samples(corpus):
    samples = corpus.list_voice_samples()
    assert len(samples) == 2
    assert {s.id for s in samples} == {"s1", "s2"}


def test_find_voice_samples_returns_all_when_unfiltered(corpus):
    hits = corpus.find_voice_samples(query=None, kind=None, top_k=10)
    assert len(hits) == 2


def test_find_voice_samples_filters_by_kind(corpus):
    hits = corpus.find_voice_samples(query=None, kind="essay", top_k=10)
    assert len(hits) == 1
    assert hits[0].id == "s2"


def test_find_voice_samples_top_k(corpus):
    hits = corpus.find_voice_samples(query=None, kind=None, top_k=1)
    assert len(hits) == 1
