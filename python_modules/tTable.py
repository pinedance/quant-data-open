import numpy as np
import pandas as pd
from message import send_telegram_message

#%% DATA PROCESSING
######################################################################

def select_column_by_name(df, col_name):
    if col_name in df.columns:
        return df[col_name]
    return pd.Series(dtype='float64')  # 빈 Series 반환

def check_fill_nan(df):
    n_nan = df.isna().sum().sum()
    if n_nan > 0:
        nan_where = np.where(df.isna())  
        m_err = f"Warning: {n_nan} NaN values found in the data. at: {nan_where}"
        send_telegram_message(m_err)
        send_telegram_message("Fill nan values with forward fill")
        
        # forward fill 후 backward fill로 남은 NaN 처리
        df_filled = df.fillna(method="ffill").fillna(method="bfill")
        
        # 여전히 NaN이 있는지 확인
        remaining_nan = df_filled.isna().sum().sum()
        if remaining_nan > 0:
            send_telegram_message(f"Warning: {remaining_nan} NaN values still remain after filling")
        
        return df_filled
    return df