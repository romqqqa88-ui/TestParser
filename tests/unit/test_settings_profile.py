from avito_parser_console.config.settings import Settings


def test_quasi_realtime_profile_applies_safer_polling_defaults():
    s = Settings(runtime_profile="quasi_realtime")
    assert s.request_retries == 2
    assert s.request_delay_seconds == 3.0
    assert s.request_min_retry_delay_seconds == 0.8
    assert s.request_backoff_multiplier == 2.5
    assert s.request_jitter_seconds == 1.2
    assert s.request_max_backoff_seconds == 180.0
    assert s.request_retry_after_max_seconds == 240.0
    assert s.max_concurrency == 1
    assert s.max_pages_per_query == 2
    assert s.scheduler_interval_minutes == 1


def test_default_profile_keeps_existing_defaults():
    s = Settings(runtime_profile="default")
    assert s.request_retries == 6
    assert s.max_concurrency == 5
    assert s.max_pages_per_query == 5
