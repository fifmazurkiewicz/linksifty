from linksifty.domain.content_policy import ContentReadiness, IncompleteReason, evaluate_content


def test_login_wall_requires_manual_content() -> None:
    result = evaluate_content("Please log in to continue", fetched=True)

    assert result.readiness is ContentReadiness.AWAITING_MANUAL_CONTENT
    assert result.reason is IncompleteReason.LOGIN_REQUIRED


def test_short_bare_sign_in_page_requires_manual_content() -> None:
    result = evaluate_content("Sign in", fetched=True)

    assert result.readiness is ContentReadiness.AWAITING_MANUAL_CONTENT
    assert result.reason is IncompleteReason.LOGIN_REQUIRED


def test_long_fetched_article_with_sign_in_chrome_is_ready() -> None:
    result = evaluate_content("Sign in " + "Readable article evidence. " * 20, fetched=True)

    assert result.readiness is ContentReadiness.READY
    assert result.reason is None


def test_long_fetched_page_with_explicit_login_prompt_requires_manual_content() -> None:
    text = "Readable article evidence. " * 20 + "Sign in to continue"
    result = evaluate_content(text, fetched=True)

    assert result.readiness is ContentReadiness.AWAITING_MANUAL_CONTENT
    assert result.reason is IncompleteReason.LOGIN_REQUIRED


def test_pasted_content_is_ready_without_fetch_markers() -> None:
    result = evaluate_content("Useful source material " * 20, fetched=False)

    assert result.readiness is ContentReadiness.READY
    assert result.reason is None
