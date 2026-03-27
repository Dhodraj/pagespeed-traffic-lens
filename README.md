# AnalytiX

Performance and traffic analysis visualization tool for web page speed optimization. Ingests PageSpeed Insights JSON reports and Google Analytics traffic data, then generates comprehensive charts, histograms, and dashboards to track Core Web Vitals improvements over time.

## What It Does

- Parses PageSpeed Insights JSON reports across multiple test runs
- Correlates performance scores (FCP, LCP, CLS, TBT, SI) with real traffic data
- Generates before/after comparison charts for optimization tracking
- Identifies poor performers and visualizes improvement trends
- Produces statistical histograms and scatter plots for pattern analysis

## Tech Stack

- **Python 3** -- core scripting
- **Matplotlib / Seaborn** -- static chart generation (histograms, scatter plots)
- **Plotly** -- interactive HTML dashboards
- **Pandas / NumPy** -- data analysis and aggregation

## Project Structure

```
AnalytiX/
├── analysis_summary.py                  # Final summary report generator
├── url_analysis.py                      # Multi-source URL data extraction with Plotly
├── url_summary.py                       # URL-level summary statistics
├── url_by_url_traffic_analysis.py       # Per-URL traffic correlation
├── performance_vs_traffic_chart.py      # Performance vs traffic scatter plots
├── traffic_performance_correlation.py   # Correlation analysis
├── traffic_performance_histogram.py     # Traffic distribution histograms
├── enhanced_traffic_performance_histogram.py  # Extended histogram analysis
├── simple_performance_traffic_chart.py  # Quick-view charts
├── post_optimization_scatter.py         # Post-optimization comparison
├── individual_test_analysis.py          # Per-test-run breakdown
├── poor_performers_analysis.py          # Underperforming URL deep-dive
├── comparison-over-time/               # Before/after optimization scripts & charts
├── individual_test_analysis/           # Per-test CSV exports & reports
├── poor_performers_analysis/           # Underperformer reports & comparisons
├── traffic_performance_analysis/       # Traffic-bucketed performance analysis
├── url_traffic_analysis/               # Per-URL interactive dashboards
├── pagespeed-reports/                  # Raw PageSpeed JSON data (input)
└── pagespeed-reports-cron/             # Scheduled cron report data (input)
```

## Usage

1. Place PageSpeed Insights JSON reports in `pagespeed-reports/` (organized by test run folder).
2. Run any analysis script:

```bash
python3 url_analysis.py                    # Full interactive dashboard
python3 performance_vs_traffic_chart.py    # Performance vs traffic scatter
python3 poor_performers_analysis.py        # Deep-dive on underperformers
python3 comparison-over-time/optimization_comparison_analysis.py  # Before/after
```

3. Output charts are saved as `.png` files in the project root and subdirectories.

## Key Metrics Analyzed

| Metric | Description |
|--------|-------------|
| Performance Score | Lighthouse overall score (0-100) |
| FCP | First Contentful Paint |
| LCP | Largest Contentful Paint |
| CLS | Cumulative Layout Shift |
| TBT | Total Blocking Time |
| SI | Speed Index |

## License

MIT
