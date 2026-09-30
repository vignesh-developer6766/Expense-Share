import pytest
from app.services.split_service import SplitService


def test_equal_split_even():
    splits = SplitService.calculate_equal_split(1200.0, [1, 2, 3, 4])
    assert len(splits) == 4
    for uid, amt in splits:
        assert amt == 300.0
    assert sum(amt for _, amt in splits) == 1200.0


def test_equal_split_rounding():
    splits = SplitService.calculate_equal_split(100.0, [1, 2, 3])
    assert len(splits) == 3
    # 100 / 3 = 33.33, remainder 0.01 goes to first user -> 33.34, 33.33, 33.33
    amounts = [amt for _, amt in splits]
    assert amounts == [33.34, 33.33, 33.33]
    assert round(sum(amounts), 2) == 100.0


def test_exact_split_valid():
    exact_map = {1: 500.0, 2: 300.0, 3: 400.0}
    splits = SplitService.calculate_exact_split(1200.0, exact_map)
    assert len(splits) == 3
    assert dict(splits) == exact_map


def test_exact_split_invalid_sum():
    exact_map = {1: 500.0, 2: 300.0, 3: 300.0}  # Sum = 1100 != 1200
    with pytest.raises(ValueError, match="Sum of exact amounts"):
        SplitService.calculate_exact_split(1200.0, exact_map)


def test_percentage_split_valid():
    pct_map = {1: 50.0, 2: 30.0, 3: 20.0}
    splits = SplitService.calculate_percentage_split(1200.0, pct_map)
    assert len(splits) == 3
    amount_dict = {uid: amt for uid, amt, pct in splits}
    assert amount_dict[1] == 600.0
    assert amount_dict[2] == 360.0
    assert amount_dict[3] == 240.0


def test_percentage_split_invalid_sum():
    pct_map = {1: 50.0, 2: 30.0, 3: 10.0}  # Sum = 90% != 100%
    with pytest.raises(ValueError, match="must equal 100%"):
        SplitService.calculate_percentage_split(1200.0, pct_map)


def test_shares_split_valid():
    shares_map = {1: 2.0, 2: 1.0, 3: 1.0}  # Total 4 shares -> 50%, 25%, 25%
    splits = SplitService.calculate_shares_split(1200.0, shares_map)
    assert len(splits) == 3
    amount_dict = {uid: amt for uid, amt, sh in splits}
    assert amount_dict[1] == 600.0
    assert amount_dict[2] == 300.0
    assert amount_dict[3] == 300.0
