from linksifty.domain.content_policy import ContentReadiness, IncompleteReason, evaluate_content


def test_login_wall_requires_manual_content() -> None:
    result = evaluate_content("Please log in to continue", fetched=True)

    assert result.readiness is ContentReadiness.AWAITING_MANUAL_CONTENT
    assert result.reason is IncompleteReason.LOGIN_REQUIRED


def test_pasted_content_is_ready_without_fetch_markers() -> None:
    result = evaluate_content("Useful source material " * 20, fetched=False)

    assert result.readiness is ContentReadiness.READY
    assert result.reason is None
