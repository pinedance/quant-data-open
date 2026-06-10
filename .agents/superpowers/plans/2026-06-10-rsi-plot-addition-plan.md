# RSI Plot Addition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate a new RSI scatter plot and data table above the existing MACD/T-Sigma plot in the Quant Dashboard.

**Architecture:** Add logic-control constants for RSI to `cons.py`, implement vectorized RSI calculation in `tFinance.py`, extend `DashboardAnalyzer` and data filtering in `build.py`, and render the plot/table via ECharts in `dashboard.html.j2`.

**Tech Stack:** Python, Pandas, Jinja2, ECharts (JavaScript).

---

### Task 1: Logic-Control Constants

**Files:**
* Modify: `/home/junho/Labs/pinedance/Quant/quant-data-open/core/cons.py`

- [ ] **Step 1: Define RSI period constants in `core/cons.py`**

Open `/home/junho/Labs/pinedance/Quant/quant-data-open/core/cons.py` and locate the end of Section 1. Add the following lines:

```python
# RSI Configuration
RSI_PERIOD = _constants.get("RSI_PERIOD", 14)               # RSI 기간
RSI_SIGNAL_PERIOD = _constants.get("RSI_SIGNAL_PERIOD", 9)  # RSI 시그널 기간 (EMA span)
```

- [ ] **Step 2: Run tests to verify config loads**

Run: `pytest tests/test_tfinance_vector.py -v`
Expected: PASS (existing tests should not break)

- [ ] **Step 3: Commit changes**

Run:
```bash
git add core/cons.py
git commit -m "feat: add RSI period and signal period constants"
```

---

### Task 2: Vectorized RSI Calculation

**Files:**
* Modify: `/home/junho/Labs/pinedance/Quant/quant-data-open/core/tFinance.py`
* Modify: `/home/junho/Labs/pinedance/Quant/quant-data-open/tests/test_tfinance_vector.py`

- [ ] **Step 1: Write a failing unit test for `calculate_rsi` in `tests/test_tfinance_vector.py`**

Append the following test to `/home/junho/Labs/pinedance/Quant/quant-data-open/tests/test_tfinance_vector.py`:

```python
def test_calculate_rsi():
    from core.tFinance import calculate_rsi
    # Create a simple series where price rises steadily
    prices = pd.Series([100.0 + i for i in range(20)])
    rsi = calculate_rsi(prices, period=14)
    assert isinstance(rsi, pd.Series)
    assert len(rsi) == 20
    # RSI for steadily rising prices should be high (above 80) at the end
    assert rsi.iloc[-1] > 80.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_tfinance_vector.py::test_calculate_rsi -v`
Expected: FAIL (ImportError: cannot import name 'calculate_rsi')

- [ ] **Step 3: Implement `calculate_rsi` in `core/tFinance.py`**

Append the following helper function to `/home/junho/Labs/pinedance/Quant/quant-data-open/core/tFinance.py`:

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
    
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    
    rs = avg_gain / (avg_loss + 1e-9)
    return 100.0 - (100.0 / (1.0 + rs))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_tfinance_vector.py::test_calculate_rsi -v`
Expected: PASS

- [ ] **Step 5: Commit changes**

Run:
```bash
git add core/tFinance.py tests/test_tfinance_vector.py
git commit -m "feat: implement vectorized calculate_rsi function and unit tests"
```

---

### Task 3: DashboardAnalyzer Integration

**Files:**
* Modify: `/home/junho/Labs/pinedance/Quant/quant-data-open/core/dashboard_analyzer.py`
* Modify: `/home/junho/Labs/pinedance/Quant/quant-data-open/tests/test_dashboard_analyzer.py`

- [ ] **Step 1: Write a failing unit test in `tests/test_dashboard_analyzer.py` to check for RSI data output**

Add imports and test method at the end of `/home/junho/Labs/pinedance/Quant/quant-data-open/tests/test_dashboard_analyzer.py`:

```python
def test_dashboard_analyzer_rsi():
    from core.dashboard_analyzer import DashboardAnalyzer
    df_d = pd.DataFrame({'A': [100.0 + i * 0.05 for i in range(250)]})
    # Set index to datetime to mimic daily and monthly date logic
    df_d.index = pd.date_range(end='2026-06-10', periods=250, freq='D')
    
    df_m = pd.DataFrame({'A': [100.0 + i * 1.5 for i in range(20)]})
    df_m.index = pd.date_range(end='2026-05-31', periods=20, freq='ME')
    
    df_hist = pd.DataFrame({'A': [1.0] * 20})
    df_hist.index = df_m.index
    
    analyzer = DashboardAnalyzer(
        names_dict={'A': 'Asset A'},
        df_us_d=df_d, df_us_m=df_m, df_us_hist=df_hist,
        df_kr_d=df_d, df_kr_m=df_m, df_kr_hist=df_hist
    )
    result = analyzer.analyze()
    assert "rsi_extremes" in result
    assert len(result["rsi_extremes"]) > 0
    item = result["rsi_extremes"][0]
    assert "rsi" in item
    assert "rsi_signal" in item
    assert "rsi_diff" in item
    assert item["ticker"] == "A"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_dashboard_analyzer.py::test_dashboard_analyzer_rsi -v`
Expected: FAIL (AssertionError: assert 'rsi_extremes' in result)

- [ ] **Step 3: Implement RSI aggregation in `core/dashboard_analyzer.py`**

Modify `/home/junho/Labs/pinedance/Quant/quant-data-open/core/dashboard_analyzer.py` to:
1. Import `calculate_rsi` and `RSI_PERIOD`, `RSI_SIGNAL_PERIOD`.
2. Compute `rsi_extremes` list.

Update the imports at line 9:
```python
from core.tFinance import calculate_average_momentum, calculate_t_sigma, calculate_rsi
from core.tFinance import calculate_ema_crossovers as tf_ema
from core.tFinance import calculate_macd_z as tf_macd_z
from core.cons import RSI_PERIOD, RSI_SIGNAL_PERIOD
```

Inside `DashboardAnalyzer.analyze()` (e.g. before `return` statement around line 187), add calculation logic:
```python
        # Compute RSI extremes
        rsi_extremes = []
        
        def calculate_rsi_metrics(df_d, df_m, region):
            for col in df_d.columns:
                ticker = col[1:] if (region == "KR" and col.startswith('A')) else col
                name = self.names_dict.get(ticker, ticker)
                
                # Appending today's price to monthly series to calculate current RSI
                m_series = df_m[col].dropna()
                d_series = df_d[col].dropna()
                if m_series.empty or d_series.empty:
                    continue
                    
                last_m_date = m_series.index[-1]
                last_d_date = d_series.index[-1]
                
                if last_d_date > last_m_date:
                    # Create appended series
                    appended_val = pd.Series([d_series.iloc[-1]], index=[last_d_date])
                    merged_series = pd.concat([m_series, appended_val])
                else:
                    merged_series = m_series
                
                # Compute RSI
                rsi_series = calculate_rsi(merged_series, period=RSI_PERIOD)
                rsi_signal_series = rsi_series.ewm(span=RSI_SIGNAL_PERIOD, adjust=False).mean()
                
                val_rsi = float(rsi_series.iloc[-1])
                val_rsi_signal = float(rsi_signal_series.iloc[-1])
                
                rsi_extremes.append({
                    "ticker": ticker,
                    "name": name,
                    "region": region,
                    "rsi": round(val_rsi, 2),
                    "rsi_signal": round(val_rsi_signal, 2),
                    "rsi_diff": round(val_rsi - val_rsi_signal, 2)
                })
                
        calculate_rsi_metrics(self.df_us_d, self.df_us_m, "US")
        calculate_rsi_metrics(self.df_kr_d, self.df_kr_m, "KR")
        
        # Sort by RSI descending
        rsi_extremes.sort(key=lambda x: x["rsi"], reverse=True)
```

And update the returned dict structure to include:
```python
            "monthly_momentum": macd_positive,
            "valuation_extremes": ticker_stats,
            "rsi_extremes": rsi_extremes,
            "data_quality_status": [],
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_dashboard_analyzer.py::test_dashboard_analyzer_rsi -v`
Expected: PASS

- [ ] **Step 5: Commit changes**

Run:
```bash
git add core/dashboard_analyzer.py tests/test_dashboard_analyzer.py
git commit -m "feat: calculate and output rsi_extremes in DashboardAnalyzer"
```

---

### Task 4: build.py Integration

**Files:**
* Modify: `/home/junho/Labs/pinedance/Quant/quant-data-open/build.py`

- [ ] **Step 1: Update `filter_dashboard_data` in `build.py` to isolate `rsi_extremes`**

Modify `/home/junho/Labs/pinedance/Quant/quant-data-open/build.py` around line 37 inside `filter_dashboard_data`:
```python
        "valuation_extremes": [e for e in data["valuation_extremes"] if e["region"] == region],
        "rsi_extremes":       [e for e in data.get("rsi_extremes", []) if e["region"] == region],
        "data_quality_status": [e for e in data["data_quality_status"] if e["region"] == region],
```

- [ ] **Step 2: Run all unit tests to check regression**

Run: `pytest -v`
Expected: ALL PASS

- [ ] **Step 3: Commit changes**

Run:
```bash
git add build.py
git commit -m "feat: filter rsi_extremes by region in build.py"
```

---

### Task 5: Frontend Template & ECharts Layout

**Files:**
* Modify: `/home/junho/Labs/pinedance/Quant/quant-data-open/templates/pages/dashboard.html.j2`

- [ ] **Step 1: Add HTML template components for RSI plot and details table**

Modify `/home/junho/Labs/pinedance/Quant/quant-data-open/templates/pages/dashboard.html.j2`.
Insert the card HTML block right above the **Market Landscape** card (which begins with `<div class="dash-card">` and `<span>Market Landscape</span>` around line 517):

```html
  <!-- ②-2 RSI Landscape -->
  <div class="dash-card">
    <div class="dash-card-title">
      <span>RSI Landscape</span>
      <span style="font-size:0.65rem;color:#475569;font-weight:normal;">x: RSI Diff (RSI - Signal) &nbsp;·&nbsp; y: RSI</span>
    </div>

    <!-- ECharts.js scatter plot element -->
    <div id="rsi-chart" style="width: 100%; height: 600px; margin-top: 1rem;"></div>

    <script>
    (function() {
      var chartData = [
        {% for item in data.rsi_extremes %}
        {
          value: [{{ item.rsi_diff | default(0.0) }}, {{ item.rsi | default(50.0) }}],
          ticker: {{ item.ticker | tojson }},
          name: {{ item.name | tojson }},
          rsi: {{ item.rsi | default(50.0) }},
          rsi_signal: {{ item.rsi_signal | default(50.0) }},
          rsi_diff: {{ item.rsi_diff | default(0.0) }}
        }{% if not loop.last %},{% endif %}
        {% endfor %}
      ];

      function symAxisBound(v, pad) {
        return -(Math.max(Math.abs(v.min), Math.abs(v.max)) + pad);
      }

      var chart = echarts.init(document.getElementById('rsi-chart'));
      chart.setOption({
        backgroundColor: 'transparent',
        grid: { left: 48, right: 16, top: 35, bottom: 48 },
        toolbox: {
          show: true,
          top: 0,
          right: 10,
          feature: {
            restore: {
              show: true,
              title: 'Reset'
            }
          },
          iconStyle: {
            borderColor: '#94a3b8'
          },
          emphasis: {
            iconStyle: {
              borderColor: '#ffffff'
            }
          }
        },
        dataZoom: [
          { type: 'inside', xAxisIndex: 0, filterMode: 'none' },
          { type: 'inside', yAxisIndex: 0, filterMode: 'none' }
        ],
        xAxis: {
          type: 'value',
          min: function(v) { return  symAxisBound(v, 5); },
          max: function(v) { return -symAxisBound(v, 5); },
          name: 'RSI Diff (RSI - Signal)',
          nameLocation: 'middle',
          nameGap: 28,
          nameTextStyle: { color: '#94a3b8', fontSize: 11, fontWeight: 600 },
          axisLine: { lineStyle: { color: '#475569', width: 1.5 } },
          splitLine: { lineStyle: { color: '#334155', type: 'dashed' } },
          axisLabel: { color: '#cbd5e1', fontSize: 10 }
        },
        yAxis: {
          type: 'value',
          min: 0,
          max: 100,
          name: 'RSI',
          nameLocation: 'middle',
          nameGap: 32,
          nameTextStyle: { color: '#94a3b8', fontSize: 11, fontWeight: 600 },
          axisLine: { lineStyle: { color: '#475569', width: 1.5 } },
          splitLine: { lineStyle: { color: '#334155', type: 'dashed' } },
          axisLabel: { color: '#cbd5e1', fontSize: 10 }
        },
        tooltip: {
          trigger: 'item',
          backgroundColor: 'rgba(30, 41, 59, 0.95)',
          borderColor: '#475569',
          borderWidth: 1,
          padding: [10, 14],
          textStyle: { color: '#f1f5f9', fontSize: 12 },
          formatter: function(params) {
            var d = params.data;
            var header = {{ region | tojson }} === 'KR' ? (d.name + ' <span style="font-size:10px;color:#94a3b8;">' + d.ticker + '</span>') : (d.ticker + ' <span style="font-size:10px;color:#94a3b8;">' + d.name + '</span>');
            return '<div style="font-weight:700;margin-bottom:6px;border-bottom:1px solid #334155;padding-bottom:4px;">' + header + '</div>'
              + '<div style="display:flex;justify-content:space-between;gap:15px;margin-bottom:2px;">'
              + '<span style="color:#94a3b8;">RSI:</span>'
              + '<span style="font-weight:600;color:' + (d.rsi > 70 ? '#f87171' : (d.rsi < 30 ? '#60a5fa' : '#cbd5e1')) + '">' + d.rsi.toFixed(2) + '</span>'
              + '</div>'
              + '<div style="display:flex;justify-content:space-between;gap:15px;margin-bottom:2px;">'
              + '<span style="color:#94a3b8;">RSI Signal:</span>'
              + '<span style="font-weight:600;color:#cbd5e1">' + d.rsi_signal.toFixed(2) + '</span>'
              + '</div>'
              + '<div style="display:flex;justify-content:space-between;gap:15px;">'
              + '<span style="color:#94a3b8;">RSI Diff:</span>'
              + '<span style="font-weight:600;color:' + (d.rsi_diff > 0 ? '#10b981' : (d.rsi_diff < 0 ? '#ef4444' : '#cbd5e1')) + '">' + d.rsi_diff.toFixed(2) + '</span>'
              + '</div>';
          }
        },
        series: [{
          type: 'scatter',
          data: chartData,
          symbolSize: 10,
          itemStyle: {
            color: function(params) {
              var r = params.data.rsi;
              if (r > 70) return '#f87171'; // soft red
              if (r < 30) return '#60a5fa'; // soft blue
              return '#6366f1'; // indigo
            },
            shadowBlur: 8,
            shadowColor: 'rgba(99, 102, 241, 0.4)',
            opacity: 0.95
          },
          label: {
            show: true,
            formatter: function(params) {
              return params.data.ticker;
            },
            position: 'top',
            fontSize: 9,
            color: '#cbd5e1',
            fontWeight: 600,
            distance: 5
          },
          labelLayout: {
            hideOverlap: true
          },
          emphasis: {
            scale: true,
            itemStyle: {
              shadowBlur: 15,
              shadowColor: 'rgba(255, 255, 255, 0.6)',
              opacity: 1
            },
            label: {
              color: '#ffffff',
              fontSize: 10,
              fontWeight: 700
            }
          },
          markLine: {
            silent: true,
            symbol: 'none',
            label: { show: false },
            data: [
              { xAxis: 0, lineStyle: { type: 'solid', color: '#64748b', width: 1.5 } },
              { yAxis: 30, lineStyle: { type: 'dashed', color: '#475569', width: 1 } },
              { yAxis: 70, lineStyle: { type: 'dashed', color: '#475569', width: 1 } }
            ]
          }
        }]
      });

      chart.getZr().on('dblclick', function() {
        chart.dispatchAction({
          type: 'restore'
        });
      });

      window.addEventListener('resize', function() { chart.resize(); });
    })();
    </script>

    <!-- Toggle: RSI Table -->
    <details class="toggle-section" {% if not data.rsi_extremes %}style="display:none;"{% endif %}>
      <summary class="toggle-summary">RSI Table</summary>
      <div class="val-table-wrap">
        <table class="val-table">
          <thead>
            <tr>
              {% if region == 'KR' %}
                <th>Name</th>
                <th>Ticker</th>
              {% else %}
                <th>Ticker</th>
                <th>Name</th>
              {% endif %}
              <th>RSI</th>
              <th>RSI Signal</th>
              <th>RSI Diff</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {% for item in data.rsi_extremes %}
              {% set is_hot  = item.rsi > 70 %}
              {% set is_cold = item.rsi < 30 %}
              <tr class="{% if is_hot %}row-hot{% elif is_cold %}row-cold{% endif %}">
                {% if region == 'KR' %}
                  <td class="ticker-name-cell">{{ item.name }}</td>
                  <td class="ticker-symbol-cell">{{ item.ticker }}</td>
                {% else %}
                  <td class="ticker-symbol-cell">{{ item.ticker }}</td>
                  <td class="ticker-name-cell">{{ item.name }}</td>
                {% endif %}
                <td style="font-weight:700;">{{ "%.2f"|format(item.rsi) }}</td>
                <td>{{ "%.2f"|format(item.rsi_signal) }}</td>
                <td class="{{ 'text-green' if item.rsi_diff > 0 else ('text-red' if item.rsi_diff < 0 else '') }}" style="font-weight:600;">
                  {{ '+' if item.rsi_diff > 0 else '' }}{{ "%.2f"|format(item.rsi_diff) }}
                </td>
                <td>
                  {% if is_hot %}
                    <span class="status-badge status-overheated">{% if region == 'KR' %}과열{% else %}Overheated{% endif %}</span>
                  {% elif is_cold %}
                    <span class="status-badge status-depressed">{% if region == 'KR' %}침체{% else %}Depressed{% endif %}</span>
                  {% else %}
                    <span class="status-normal">{% if region == 'KR' %}정상{% else %}Normal{% endif %}</span>
                  {% endif %}
                </td>
              </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </details>
  </div>
```

- [ ] **Step 2: Commit changes**

Run:
```bash
git add templates/pages/dashboard.html.j2
git commit -m "feat: integrate RSI Landscape plot and Table in templates"
```

---

### Task 6: Execution and Verification

**Files:**
* Modify: None (Verification only)

- [ ] **Step 1: Execute `build.py` script**

Run: `./build.py`
Expected: Successful HTML page generation for both US and KR regions. Check output logs.

- [ ] **Step 2: Verify generated JSON structure**

Verify `public/dist/US/dashboard.json` has `rsi_extremes` list with `rsi`, `rsi_signal`, and `rsi_diff`.

Run: `grep -A 10 "rsi_extremes" public/dist/US/dashboard.json`
Expected: Non-empty output displaying calculated RSI objects.

- [ ] **Step 3: Commit all generated output files (if applicable/configured in repo)**

(Note: If `public/` is ignored by git, do nothing. Check if output changes need commit).
