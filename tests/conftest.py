"""Keep this template's default pytest suite below 50 collected cases."""

import pytest


MAX_COLLECTED_TESTS = 49


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    # Count parameterized rows and skipped cases before ordinary -k/-m filtering.
    count = len(items)
    if count > MAX_COLLECTED_TESTS:
        raise pytest.UsageError(
            f"Collected {count} tests; the template budget is at most {MAX_COLLECTED_TESTS}. "
            "Remove duplicate or low-value cases before adding more; do not hide "
            "tests with skips or deselection to satisfy the budget."
        )
