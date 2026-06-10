# Design Specification: RSI Plot Addition to Quant Dashboard

This specification defines the requirements, architecture, and changes required to integrate a new RSI (Relative Strength Index) scatter plot and data table into the Quant Dashboard.

---

## 1. Objectives

* **New Visual Element**: Position a new RSI scatter plot above the existing `Market Landscape` (MACD Z / T-Sigma) plot on the main dashboard.
* **Consistent Design**: Replicate the current dashboard's aesthetics, featuring an interactive ECharts scatter plot and a toggled details data table.
* **Unified Metrics**: Display RSI, RSI Signal, and the difference (RSI - RSI Signal) for all tracked assets.

---

## 2. Configuration & Constants

To avoid hardcoded parameters, the following logic-control constants will be defined in [cons.py](file:///home/junho/Labs/pinedance/Quant/quant-data-open/core/cons.py):

* `RSI_PERIOD`: Period for calculating the wilder-style RSI. Defaults to `14`.
* `RSI_SIGNAL_PERIOD`: Span for calculating the exponential moving average (EMA) signal of the RSI. Defaults to `9`.

In [cons.py](file:///home/junho/Labs/pinedance/Quant/quant-data-open/core/cons.py):
```python
RSI_PERIOD = _constants.get("RSI_PERIOD", 14)
RSI_SIGNAL_PERIOD = _constants.get("RSI_SIGNAL_PERIOD", 9)
```

---

## 3. Core Math (tFinance.py)

We will introduce a vectorized RSI calculation helper to [tFinance.py](file:///home/junho/Labs/pinedance/Quant/quant-data-open/core/tFinance.py) following standard Wilder's smoothing logic:

```python
def calculate_rsi(series, period=14):
    """
    Vectorized Wilder's Relative Strength Index calculation.
    """
    if len(series) < period:
        return pd.Series(50.0, index=series.index)
        
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    # Wilder's smoothing uses alpha = 1 / period
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    
    rs = avg_gain / (avg_loss + 1e-9)
    return 100.0 - (100.0 / (1.0 + rs))
```

---

## 4. Backend Updates & Data Flow

### 4.1 DashboardAnalyzer (`core/dashboard_analyzer.py`)

In `DashboardAnalyzer.analyze()`, we will:
1. Merge the monthly end-of-month prices (`df_us_m` / `df_kr_m`) with the latest daily price (`df_us_d` / `df_kr_d`) for each asset to calculate the most up-to-date monthly series.
2. Ensure the latest daily price is only appended if its date is strictly greater than the latest end-of-month date to avoid duplicates.
3. Compute the `rsi` series and its signal line `rsi_signal` (EMA of RSI).
4. Extract the latest computed `rsi` and `rsi_signal` value.
5. Create a new result array `rsi_extremes` consisting of objects matching this format:
   ```json
   {
     "ticker": "AAPL",
     "name": "Apple Inc.",
     "region": "US",
     "rsi": 65.42,
     "rsi_signal": 58.21,
     "rsi_diff": 7.21
   }
   ```
6. Sort `rsi_extremes` descending by the `rsi` value.
7. Return `"rsi_extremes"` as a key in the final analysis dictionary.

### 4.2 Data Filtering (`build.py`)

We will update `filter_dashboard_data(data, region)` in [build.py](file:///home/junho/Labs/pinedance/Quant/quant-data-open/build.py) to preserve regional isolation for the new array:
```python
"rsi_extremes": [e for e in data.get("rsi_extremes", []) if e["region"] == region],
```

---

## 5. UI Layout and Interaction (`dashboard.html.j2`)

### 5.1 HTML Structure
The new chart card is placed directly above the existing `Market Landscape` card:
* ID of the chart: `rsi-chart`
* Title: `RSI Landscape`
* Toggled table inside a `<details class="toggle-section">` block titled `RSI Table`.

### 5.2 ECharts Settings
* **X-Axis (RSI Diff)**: Symmetric scale around `0`.
* **Y-Axis (RSI)**: Fixed range `[0, 100]`.
* **Mark lines**:
  * Horizontals at `y = 70` (overbought / overheated) and `y = 30` (oversold / depressed).
  * Vertical at `x = 0`.
* **Points & Colors**:
  * Color-coded based on RSI value:
    * `rsi > 70` -> Soft Red (`#f87171`)
    * `rsi < 30` -> Soft Blue (`#60a5fa`)
    * Normal -> Indigo (`#6366f1`)
  * Label displays the ticker symbol.
  * Interactive tooltips show: Ticker, Name, RSI, RSI Signal, and RSI Diff.

---

## 6. Verification Plan

* **Unit Tests**:
  * Test `calculate_rsi` in [test_tfinance_vector.py](file:///home/junho/Labs/pinedance/Quant/quant-data-open/tests/test_tfinance_vector.py).
  * Test `rsi_extremes` presence and format in [test_dashboard_analyzer.py](file:///home/junho/Labs/pinedance/Quant/quant-data-open/tests/test_dashboard_analyzer.py).
* **Integration Verification**:
  * Execute `build.py` and inspect console outputs.
  * Verify the generated JSON contents `public/dist/US/dashboard.json` and `public/dist/KR/dashboard.json` contain the new `rsi_extremes` list.
  * Run local dev server to visually check chart layout and interaction.
