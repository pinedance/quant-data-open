import numpy as np
import pandas as pd

#%% DATA PROCESSING
######################################################################

def select_column_by_name(df, col_name):
    if col_name in df.columns:
        return df[col_name]
    return pd.Series(dtype='float64')  # 빈 Series 반환

def check_fill_nan(df, fill_nan=False):
    n_nan = df.isna().sum().sum()
    warnings = []
    if n_nan > 0:
        nan_info = []
        for col in df.columns:
            nan_series = df[col].isna()
            if nan_series.sum() > 0:
                nan_indices = nan_series[nan_series].index
                start_index = nan_indices[0]
                end_index = nan_indices[-1]
                if hasattr(start_index, 'date'):
                    start_index = start_index.date()
                if hasattr(end_index, 'date'):
                    end_index = end_index.date()
                nan_info.append(f"{col}: {start_index} ~ {end_index}")

        warnings.append(f"NaN 값 감지 ({n_nan:,}개)\n" + "\n".join(nan_info))

        if fill_nan:
            df_filled = df.ffill().bfill()
            remaining_nan = df_filled.isna().sum().sum()
            if remaining_nan > 0:
                warnings.append(f"Warning: {remaining_nan} NaN values still remain after filling")
            return df_filled, warnings

    return df, warnings

def post_process_price(df):
    df_new = df.dropna(how='all')
    df_new.index = df_new.index.date
    return df_new

def resample_monthly(daily_prices, method='eom', target_day=None):
    if not isinstance(daily_prices.index, pd.DatetimeIndex):
        raise ValueError("daily_prices의 인덱스는 DatetimeIndex 형식이어야 합니다.")
    if daily_prices.empty:
        raise ValueError("daily_prices가 비어 있습니다.")

    daily_prices = daily_prices.sort_index()

    if method == 'eom':
        # 1. Resample to standard month end
        monthly = daily_prices.resample('ME').last()
        # 2. Extract standard EOM up to the previous month
        last_date = daily_prices.index[-1]
        prev_months = monthly[monthly.index < pd.Timestamp(last_date.year, last_date.month, 1)]
        
        # 3. Create a single-row DataFrame for the current exact daily date
        current_row = daily_prices.iloc[[-1]].copy()
        
        # 4. Concatenate
        combined = pd.concat([prev_months, current_row])
        # drop duplicates in index just in case last_date is exactly last day of month
        combined = combined[~combined.index.duplicated(keep='last')]
        return combined

    if method == 'current':
        if target_day is None:
            target_day = daily_prices.index[-1].day

        month_starts = daily_prices.resample('MS').first().index
        valid_days = np.minimum(target_day, month_starts.days_in_month)
        target_dates = pd.to_datetime({
            'year': month_starts.year,
            'month': month_starts.month,
            'day': valid_days
        })

        pos = daily_prices.index.searchsorted(target_dates, side='right') - 1
        pos = pos[pos >= 0]

        actual_dates = daily_prices.index[pos]
        monthly_prices = daily_prices.iloc[pos].copy()
        monthly_prices.index = actual_dates

        return monthly_prices

    raise ValueError(f"method는 'eom' 또는 'current'이어야 합니다. (받은 값: {method})")