from validation_agent.skills.checks import looks_like_full_paid_pdf


def test_printable_full_pdf_exposure_detection():
    assert looks_like_full_paid_pdf("https://cdn.example.com/papers/mock-12.pdf") is True


def test_printable_sample_pdf_is_not_flagged():
    assert looks_like_full_paid_pdf("https://cdn.example.com/papers/mock-12-sample.pdf") is False
