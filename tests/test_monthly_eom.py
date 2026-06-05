import pandas as pd
from core.tTable import resample_monthly

def test_resample_monthly_eom_appends_current_exact_date():
    # 2026-05-29 is last trading day of May, 2026-06-05 is current latest day
    idx = pd.to_datetime(['2026-05-29', '2026-06-01', '2026-06-02', '2026-06-05'])
    df = pd.DataFrame({'A': [10.0, 11.0, 12.0, 13.0]}, index=idx)
    
    res = resample_monthly(df, method='eom')
    
    # Should have May end-of-month (calendar 2026-05-31) and June current day (2026-06-05)
    assert len(res) == 2
    assert res.index[0] == pd.Timestamp('2026-05-31')
    assert res.index[1] == pd.Timestamp('2026-06-05')
