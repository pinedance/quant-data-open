import numpy as np
import pandas as pd
from core.message import send_telegram_message

#%% DATA PROCESSING
######################################################################

def select_column_by_name(df, col_name):
    if col_name in df.columns:
        return df[col_name]
    return pd.Series(dtype='float64')  # 빈 Series 반환

def check_fill_nan(df, fill_nan=False):
    n_nan = df.isna().sum().sum()
    if n_nan > 0:
        # NaN이 있는 컬럼별로 정보 수집
        nan_info = []
        for col in df.columns:
            nan_series = df[col].isna()
            if nan_series.sum() > 0:  # any()를 명시적으로 호출
                nan_indices = nan_series[nan_series].index
                
                # nan_indices가 비어 있는지 확인
                if len(nan_indices) == 0:
                    continue
                
                # "최초 index ~ 최종 index" 형태로 표시
                start_index = nan_indices[0].date()
                end_index = nan_indices[-1].date()
                nan_range = f"{start_index} ~ {end_index}"
                nan_info.append(f"{col}: {nan_range}")
        
        m_err = f"Warning: {n_nan} NaN values found in the data.\nLocation:\n" + "\n".join(nan_info)
        send_telegram_message(m_err)
        
        if fill_nan:
            send_telegram_message("Fill nan values with forward fill")
            # forward fill 후 backward fill로 남은 NaN 처리
            df_filled = df.fillna(method="ffill").fillna(method="bfill")
            
            # 여전히 NaN이 있는지 확인
            remaining_nan = df_filled.isna().sum().sum()
            if remaining_nan > 0:
                send_telegram_message(f"Warning: {remaining_nan} NaN values still remain after filling")
            
            return df_filled
            
    return df