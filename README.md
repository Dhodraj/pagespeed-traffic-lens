# pagespeed-traffic-lens

Reads Google PageSpeed Insights reports, lines them up against site traffic, and draws charts that show whether a speed change moved the numbers that matter.

Built in 2026.

## What it does

- Reads PageSpeed Insights JSON reports from several runs and pulls out the scores: performance, FCP, LCP, CLS, TBT and speed index.
- Joins each URL's scores to its traffic from a CSV export.
- Draws before-and-after charts for a change, flags the worst performers, and plots score against traffic.

The scripts write interactive HTML charts with Plotly, and some static ones with Matplotlib and Seaborn.

## Run it

```bash
pip install pandas numpy plotly matplotlib seaborn
```

Each script reads from two folders next to it, which are not in the repository:

- `pagespeed-reports/` and `pagespeed-reports-cron/` hold the PageSpeed JSON reports, one folder per run.
- A traffic CSV sits in `pagespeed-reports-cron/`, with a `url` (or `URL`) column and an `estimated_traffic` column.

With those in place, run a script directly, for example:

```bash
python traffic_performance_correlation.py
```

Each script writes its charts to an output folder it names when it runs.
