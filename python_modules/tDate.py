import pandas as pd

#%% DATE
######################################################################
month2quarter_dict = {
    '01': 'Q1', '02': 'Q1', '03': 'Q1', '04': 'Q2', '05': 'Q2', '06': 'Q2',
    '07': 'Q3', '08': 'Q3', '09': 'Q3', '10': 'Q4', '11': 'Q4', '12': 'Q4'
}

def yyyymm2quarter(yyyymm, q_dict=month2quarter_dict):
    y = yyyymm[:4]
    m = yyyymm[4:]
    q = q_dict[m]
    return f"{y}{q}"

def setup_date_range(days):
    days_offset = pd.Timedelta(days, unit="days")
    day_end = pd.Timestamp.today().date()
    day_start = day_end - days_offset
    return day_start, day_end