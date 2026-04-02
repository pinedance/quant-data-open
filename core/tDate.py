import pandas as pd

#%% DATE
######################################################################
month2quarter_dict = {
    '01': 'Q1', '02': 'Q1', '03': 'Q1', '04': 'Q2', '05': 'Q2', '06': 'Q2',
    '07': 'Q3', '08': 'Q3', '09': 'Q3', '10': 'Q4', '11': 'Q4', '12': 'Q4'
}

def yyyymm2quarter(yyyymm, q_dict=month2quarter_dict):
    if not isinstance(yyyymm, str) or len(yyyymm) != 6:
        raise ValueError(f"yyyymm은 6자리 문자열이어야 합니다. (받은 값: {yyyymm!r})")
    y = yyyymm[:4]
    m = yyyymm[4:]
    if m not in q_dict:
        raise ValueError(f"유효하지 않은 월입니다. (받은 값: {m!r})")
    return f"{y}{q_dict[m]}"

def setup_date_range(months):
    if not isinstance(months, int) or months <= 0:
        raise ValueError(f"months는 양의 정수여야 합니다. (받은 값: {months!r})")
    day_end = pd.Timestamp.today()
    day_start = day_end - pd.DateOffset(months=months)
    return day_start.date(), day_end.date()