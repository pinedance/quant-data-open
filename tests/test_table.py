import numpy as np
import pandas as pd

from core.tTable import check_fill_nan, resample_monthly


def test_resample_monthly_eom():
    # Generate daily datetime index for 3 months
    idx = pd.date_range(start="2026-01-01", end="2026-03-15", freq="D")
    df = pd.DataFrame({"Price": range(len(idx))}, index=idx)
    
    # Resample EOM
    res = resample_monthly(df, method='eom')
    # Should have end of month dates for Jan and Feb 
    assert len(res) >= 2
    assert any("2026-01-31" in str(d) for d in res.index)
    assert any("2026-02-28" in str(d) for d in res.index)


def test_resample_monthly_current():
    idx = pd.date_range(start="2026-01-01", end="2026-03-15", freq="D")
    df = pd.DataFrame({"Price": range(len(idx))}, index=idx)
    
    # Resample current month using target day 15
    res = resample_monthly(df, method='current', target_day=15)
    # January 15, February 15, March 15
    assert len(res) == 3
    assert any("2026-01-15" in str(d) for d in res.index)
    assert any("2026-02-15" in str(d) for d in res.index)
    assert any("2026-03-15" in str(d) for d in res.index)


def test_check_fill_nan_returns_warnings():
    df = pd.DataFrame({'col1': [1.0, np.nan, 3.0], 'col2': [2.0, 4.0, np.nan]})
    df.index = pd.to_datetime(['2026-06-01', '2026-06-02', '2026-06-03'])
    
    # Test without fill
    df_out, warnings = check_fill_nan(df, fill_nan=False)
    assert len(warnings) > 0
    assert "col1" in warnings[0]
    assert df_out.isna().sum().sum() == 2
