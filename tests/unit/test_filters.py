from avito_parser_console.domain.models import FilterConfig, Listing
from avito_parser_console.filters.engine import RuleEngine


def test_filter_engine_by_price():
    listing = Listing(listing_id="1", url="https://www.avito.ru/item1", price=2000000, title="test")
    config = FilterConfig(min_price=1000000, max_price=3000000)
    passed, filtered = RuleEngine().apply([listing], config)
    assert len(passed) == 1
    assert filtered == 0


def test_filter_engine_returns_rejection_reasons():
    listing = Listing(listing_id="2", url="https://www.avito.ru/item2", price=500000, title="test")
    config = FilterConfig(min_price=1000000)
    passed, filtered_records = RuleEngine().apply_with_report([listing], config)
    assert len(passed) == 0
    assert len(filtered_records) == 1
    assert "PriceRule" in filtered_records[0]["reasons"]
