from apply.agents.cover_letter_judge import JudgeScores
from eval.runners.cover_letter_bench import CoverLetterBenchRow, CoverLetterBenchSummary


def test_summary_mean_delta_empty():
    assert CoverLetterBenchSummary().mean_delta("specificity") == 0.0


def test_summary_mean_delta_two_rows():
    s1 = JudgeScores(specificity=8, voice_match=7, hook_strength=7, professionalism=8,
                     specifics_cited=[], rationale="x")
    b1 = JudgeScores(specificity=4, voice_match=4, hook_strength=3, professionalism=7,
                     specifics_cited=[], rationale="y")
    s2 = JudgeScores(specificity=9, voice_match=8, hook_strength=9, professionalism=9,
                     specifics_cited=[], rationale="x")
    b2 = JudgeScores(specificity=3, voice_match=5, hook_strength=4, professionalism=8,
                     specifics_cited=[], rationale="y")

    rows = [
        CoverLetterBenchRow(jd_id="1", company_name="A", s_scores=s1, b1_scores=b1, s_body="", b1_body=""),
        CoverLetterBenchRow(jd_id="2", company_name="B", s_scores=s2, b1_scores=b2, s_body="", b1_body=""),
    ]
    summary = CoverLetterBenchSummary(rows=rows)

    # specificity: (8-4 + 9-3) / 2 = 5.0
    assert summary.mean_delta("specificity") == 5.0
    # voice_match: (7-4 + 8-5) / 2 = 3.0
    assert summary.mean_delta("voice_match") == 3.0
