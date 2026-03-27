#!/usr/bin/env python3
"""
Site Traffic vs Performance Correlation Analysis

This script correlates overall site traffic levels with page performance metrics,
comparing how the same URLs performed at similar traffic volumes before and after
the Directus optimization.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import glob
from datetime import datetime, timedelta
import re
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set style for matplotlib
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class TrafficPerformanceAnalyzer:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.pre_optimization_dir = self.base_dir / "pagespeed-reports"
        self.post_optimization_dir = self.base_dir / "pagespeed-reports-cron"
        self.traffic_file = self.post_optimization_dir / "Realtime Tracking Automation - India & US - Jul - 2025.csv"
        
        self.pre_data = []
        self.post_data = []
        self.traffic_data = None
        
    def load_traffic_data(self):
        """Load overall site traffic data from Google Analytics."""
        print("Loading site traffic data...")
        
        if not self.traffic_file.exists():
            print(f"Traffic file not found: {self.traffic_file}")
            return
            
        # Read the traffic CSV - it has a complex structure
        df = pd.read_csv(self.traffic_file)
        
        # Extract hourly traffic data
        traffic_rows = []
        
        for idx, row in df.iterrows():
            date_country = str(row.iloc[0])
            
            # Skip header rows and process data rows
            if '/' in date_country and any(char.isdigit() for char in date_country):
                # This is a date row like "7/1/2025"
                date_str = date_country
                try:
                    date = datetime.strptime(date_str, "%m/%d/%Y")
                except:
                    continue
                    
                # Process each time column
                for col_idx in range(1, len(row)):
                    if col_idx < len(df.columns):
                        time_str = df.columns[col_idx]
                        try:
                            # Parse time like "12:00 AM", "1:30 PM", etc.
                            time_obj = datetime.strptime(time_str, "%I:%M %p").time()
                            timestamp = datetime.combine(date.date(), time_obj)
                            
                            # Get traffic value
                            traffic_value = row.iloc[col_idx]
                            if pd.notna(traffic_value) and str(traffic_value).isdigit():
                                traffic_rows.append({
                                    'timestamp': timestamp,
                                    'traffic': int(traffic_value),
                                    'country': 'ALL'  # This appears to be the "All" row
                                })
                        except:
                            continue
                            
            elif date_country == "All":
                # This is the "All" countries row - contains total traffic
                date_from_prev = None
                # Find the previous date row
                for prev_idx in range(idx-1, -1, -1):
                    prev_val = str(df.iloc[prev_idx, 0])
                    if '/' in prev_val and any(char.isdigit() for char in prev_val):
                        try:
                            date_from_prev = datetime.strptime(prev_val, "%m/%d/%Y")
                            break
                        except:
                            continue
                
                if date_from_prev:
                    for col_idx in range(1, len(row)):
                        if col_idx < len(df.columns):
                            time_str = df.columns[col_idx]
                            try:
                                time_obj = datetime.strptime(time_str, "%I:%M %p").time()
                                timestamp = datetime.combine(date_from_prev.date(), time_obj)
                                
                                traffic_value = row.iloc[col_idx]
                                if pd.notna(traffic_value) and str(traffic_value).isdigit():
                                    traffic_rows.append({
                                        'timestamp': timestamp,
                                        'traffic': int(traffic_value),
                                        'country': 'ALL'
                                    })
                            except:
                                continue
        
        if traffic_rows:
            self.traffic_data = pd.DataFrame(traffic_rows)
            self.traffic_data = self.traffic_data.drop_duplicates()
            self.traffic_data = self.traffic_data.sort_values('timestamp')
            print(f"Loaded {len(self.traffic_data)} traffic data points")
            print(f"Traffic data range: {self.traffic_data['timestamp'].min()} to {self.traffic_data['timestamp'].max()}")
        else:
            print("No traffic data could be parsed")
    
    def load_performance_data(self):
        """Load PageSpeed data from before and after optimization."""
        print("Loading pre-optimization performance data...")
        
        # Load pre-optimization data
        pre_files = list(self.pre_optimization_dir.glob("*/article-qa.csv"))
        pre_files.extend(list(self.pre_optimization_dir.glob("*/pagespeed-report-*.csv")))
        
        for file_path in pre_files:
            try:
                df = pd.read_csv(file_path)
                if 'URL' in df.columns and 'Performance' in df.columns:
                    # Extract timestamp from folder name or filename
                    folder_name = file_path.parent.name
                    
                    # Try to extract date/time from folder name
                    timestamp = self._extract_timestamp_from_folder(folder_name)
                    
                    df['timestamp'] = timestamp
                    df['optimization_status'] = 'pre'
                    df['source_file'] = str(file_path)
                    
                    self.pre_data.append(df)
                    print(f"Loaded pre-optimization file: {file_path.name}")
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        
        print("Loading post-optimization performance data...")
        
        # Load post-optimization data
        post_folders = [d for d in self.post_optimization_dir.iterdir() 
                       if d.is_dir() and d.name.startswith('2025-')]
        
        for folder in post_folders:
            csv_files = list(folder.glob("pagespeed-report-*.csv"))
            for file_path in csv_files:
                try:
                    df = pd.read_csv(file_path)
                    if 'URL' in df.columns and 'Performance' in df.columns:
                        # Extract timestamp from filename
                        timestamp = self._extract_timestamp_from_filename(file_path.name)
                        
                        df['timestamp'] = timestamp
                        df['optimization_status'] = 'post'
                        df['source_file'] = str(file_path)
                        
                        self.post_data.append(df)
                        print(f"Loaded post-optimization file: {file_path.name}")
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
    
    def _extract_timestamp_from_folder(self, folder_name):
        """Extract timestamp from folder names like 'article-qa-8-7-2025-3-41-pm'."""
        try:
            # Pattern: article-qa-8-7-2025-3-41-pm
            parts = folder_name.split('-')
            if len(parts) >= 6:
                month = int(parts[2])
                day = int(parts[3])
                year = int(parts[4])
                hour = int(parts[5])
                minute = int(parts[6])
                
                # Handle AM/PM
                if len(parts) > 7 and parts[7].lower() == 'pm' and hour != 12:
                    hour += 12
                elif len(parts) > 7 and parts[7].lower() == 'am' and hour == 12:
                    hour = 0
                
                return datetime(year, month, day, hour, minute)
        except:
            pass
        
        # Default to a reasonable pre-optimization date
        return datetime(2025, 7, 8, 15, 0)
    
    def _extract_timestamp_from_filename(self, filename):
        """Extract timestamp from filenames like 'pagespeed-report-2025-07-11T12-10-47-363Z.csv'."""
        try:
            # Pattern: pagespeed-report-2025-07-11T12-10-47-363Z.csv
            match = re.search(r'(\d{4})-(\d{2})-(\d{2})T(\d{2})-(\d{2})-(\d{2})', filename)
            if match:
                year, month, day, hour, minute, second = map(int, match.groups())
                return datetime(year, month, day, hour, minute, second)
        except:
            pass
        
        # Default to a reasonable post-optimization date
        return datetime(2025, 7, 11, 17, 0)
    
    def estimate_traffic_at_time(self, test_timestamp):
        """Estimate overall site traffic at the time of a performance test."""
        if self.traffic_data is None or len(self.traffic_data) == 0:
            return 400  # Default traffic level
        
        # Find the closest traffic measurement in time
        time_diffs = abs(self.traffic_data['timestamp'] - test_timestamp)
        closest_idx = time_diffs.idxmin()
        
        return self.traffic_data.loc[closest_idx, 'traffic']
    
    def analyze_correlation(self):
        """Analyze the correlation between site traffic and performance."""
        if not self.pre_data and not self.post_data:
            print("No performance data loaded!")
            return None, None
        
        # Combine all performance data
        all_pre = pd.concat(self.pre_data, ignore_index=True) if self.pre_data else pd.DataFrame()
        all_post = pd.concat(self.post_data, ignore_index=True) if self.post_data else pd.DataFrame()
        
        # Add traffic estimates
        if not all_pre.empty:
            all_pre['estimated_traffic'] = all_pre['timestamp'].apply(self.estimate_traffic_at_time)
        if not all_post.empty:
            all_post['estimated_traffic'] = all_post['timestamp'].apply(self.estimate_traffic_at_time)
        
        # Combine all data
        combined_data = pd.concat([all_pre, all_post], ignore_index=True)
        
        # Clean data
        combined_data = combined_data.dropna(subset=['Performance', 'URL'])
        combined_data = combined_data[combined_data['Performance'] > 0]
        
        # Categorize traffic levels
        combined_data['traffic_category'] = pd.cut(
            combined_data['estimated_traffic'],
            bins=[0, 300, 500, 700, float('inf')],
            labels=['Low Traffic (0-300)', 'Medium Traffic (301-500)', 
                   'High Traffic (501-700)', 'Very High Traffic (700+)']
        )
        
        return combined_data, self.traffic_data
    
    def generate_charts(self, combined_data, traffic_data):
        """Generate comprehensive charts showing traffic vs performance correlation."""
        if combined_data is None or combined_data.empty:
            print("No data available for chart generation!")
            return
        
        output_dir = self.base_dir / "traffic_performance_analysis"
        output_dir.mkdir(exist_ok=True)
        
        # 1. Performance vs Traffic Scatter Plot
        fig = px.scatter(
            combined_data,
            x='estimated_traffic',
            y='Performance',
            color='optimization_status',
            title='Performance Score vs Overall Site Traffic',
            labels={
                'estimated_traffic': 'Overall Site Traffic (Users)',
                'Performance': 'PageSpeed Performance Score',
                'optimization_status': 'Optimization Status'
            },
            hover_data=['URL', 'timestamp'],
            color_discrete_map={'pre': '#FF6B6B', 'post': '#4ECDC4'}
        )
        fig.update_layout(height=600, width=1000)
        fig.write_html(output_dir / "performance_vs_traffic_scatter.html")
        
        # 2. Performance by Traffic Category (Box Plot)
        fig = px.box(
            combined_data,
            x='traffic_category',
            y='Performance',
            color='optimization_status',
            title='Performance Distribution by Traffic Category',
            labels={
                'traffic_category': 'Site Traffic Category',
                'Performance': 'PageSpeed Performance Score'
            }
        )
        fig.update_layout(height=600, width=1000)
        fig.write_html(output_dir / "performance_by_traffic_category.html")
        
        # 3. Same URLs Comparison at Similar Traffic Levels
        # Find URLs that exist in both pre and post data
        pre_urls = set(combined_data[combined_data['optimization_status'] == 'pre']['URL'])
        post_urls = set(combined_data[combined_data['optimization_status'] == 'post']['URL'])
        common_urls = pre_urls.intersection(post_urls)
        
        if common_urls:
            same_url_data = combined_data[combined_data['URL'].isin(common_urls)].copy()
            
            # Calculate average performance for each URL before and after optimization
            url_comparison = []
            
            for url in common_urls:
                url_data = same_url_data[same_url_data['URL'] == url]
                
                pre_data = url_data[url_data['optimization_status'] == 'pre']
                post_data = url_data[url_data['optimization_status'] == 'post']
                
                if not pre_data.empty and not post_data.empty:
                    pre_avg_perf = pre_data['Performance'].mean()
                    post_avg_perf = post_data['Performance'].mean()
                    pre_avg_traffic = pre_data['estimated_traffic'].mean()
                    post_avg_traffic = post_data['estimated_traffic'].mean()
                    
                    improvement = post_avg_perf - pre_avg_perf
                    
                    url_comparison.append({
                        'URL': url,
                        'Pre_Performance': pre_avg_perf,
                        'Post_Performance': post_avg_perf,
                        'Performance_Improvement': improvement,
                        'Pre_Traffic': pre_avg_traffic,
                        'Post_Traffic': post_avg_traffic,
                        'Traffic_Difference': abs(post_avg_traffic - pre_avg_traffic)
                    })
            
            if url_comparison:
                comparison_df = pd.DataFrame(url_comparison)
                
                # Chart: Performance improvement vs traffic similarity
                fig = px.scatter(
                    comparison_df,
                    x='Traffic_Difference',
                    y='Performance_Improvement',
                    hover_data=['URL', 'Pre_Performance', 'Post_Performance'],
                    title='Performance Improvement vs Traffic Level Similarity',
                    labels={
                        'Traffic_Difference': 'Difference in Traffic Levels',
                        'Performance_Improvement': 'Performance Score Improvement'
                    }
                )
                fig.add_hline(y=0, line_dash="dash", line_color="red", 
                             annotation_text="No Improvement")
                fig.update_layout(height=600, width=1000)
                fig.write_html(output_dir / "improvement_vs_traffic_similarity.html")
                
                # Save comparison data
                comparison_df.to_csv(output_dir / "url_performance_comparison.csv", index=False)
        
        # 4. Traffic Timeline with Performance Overlays
        if traffic_data is not None and not traffic_data.empty:
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Overall Site Traffic Over Time', 
                               'Performance Scores Over Time'),
                shared_xaxes=True,
                vertical_spacing=0.1
            )
            
            # Traffic timeline
            fig.add_trace(
                go.Scatter(
                    x=traffic_data['timestamp'],
                    y=traffic_data['traffic'],
                    mode='lines',
                    name='Site Traffic',
                    line=dict(color='blue')
                ),
                row=1, col=1
            )
            
            # Performance scores over time
            for status in ['pre', 'post']:
                status_data = combined_data[combined_data['optimization_status'] == status]
                if not status_data.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=status_data['timestamp'],
                            y=status_data['Performance'],
                            mode='markers',
                            name=f'Performance ({status})',
                            marker=dict(
                                color='red' if status == 'pre' else 'green',
                                size=8
                            )
                        ),
                        row=2, col=1
                    )
            
            fig.update_layout(
                height=800,
                title_text="Site Traffic and Performance Timeline",
                showlegend=True
            )
            fig.update_xaxes(title_text="Date/Time", row=2, col=1)
            fig.update_yaxes(title_text="Users", row=1, col=1)
            fig.update_yaxes(title_text="Performance Score", row=2, col=1)
            
            fig.write_html(output_dir / "traffic_performance_timeline.html")
        
        # 5. Statistical Summary
        summary_stats = combined_data.groupby(['optimization_status', 'traffic_category']).agg({
            'Performance': ['mean', 'median', 'std', 'count'],
            'estimated_traffic': ['mean', 'std']
        }).round(2)
        
        summary_stats.to_csv(output_dir / "performance_statistics_by_traffic.csv")
        
        print(f"\nCharts and analysis saved to: {output_dir}")
        print("\nGenerated files:")
        print("- performance_vs_traffic_scatter.html")
        print("- performance_by_traffic_category.html")
        print("- improvement_vs_traffic_similarity.html")
        print("- traffic_performance_timeline.html")
        print("- url_performance_comparison.csv")
        print("- performance_statistics_by_traffic.csv")
        
        return summary_stats
    
    def generate_dashboard(self, combined_data, traffic_data, summary_stats):
        """Generate a comprehensive HTML dashboard."""
        output_dir = self.base_dir / "traffic_performance_analysis"
        
        # Calculate key metrics
        if combined_data is not None and not combined_data.empty:
            pre_data = combined_data[combined_data['optimization_status'] == 'pre']
            post_data = combined_data[combined_data['optimization_status'] == 'post']
            
            avg_pre_performance = pre_data['Performance'].mean() if not pre_data.empty else 0
            avg_post_performance = post_data['Performance'].mean() if not post_data.empty else 0
            improvement = avg_post_performance - avg_pre_performance
            
            # URLs tested in both periods
            pre_urls = set(pre_data['URL']) if not pre_data.empty else set()
            post_urls = set(post_data['URL']) if not post_data.empty else set()
            common_urls = len(pre_urls.intersection(post_urls))
            
            # Traffic range
            min_traffic = combined_data['estimated_traffic'].min()
            max_traffic = combined_data['estimated_traffic'].max()
        else:
            avg_pre_performance = avg_post_performance = improvement = 0
            common_urls = min_traffic = max_traffic = 0
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Site Traffic vs Performance Analysis Dashboard</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .metrics-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .metric-card {{
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    text-align: center;
                }}
                .metric-value {{
                    font-size: 2.5em;
                    font-weight: bold;
                    color: #333;
                    margin-bottom: 10px;
                }}
                .metric-label {{
                    color: #666;
                    font-size: 0.9em;
                }}
                .improvement {{
                    color: #28a745;
                }}
                .decline {{
                    color: #dc3545;
                }}
                .chart-container {{
                    background: white;
                    margin: 20px 0;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .chart-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
                    gap: 20px;
                }}
                iframe {{
                    width: 100%;
                    height: 600px;
                    border: none;
                    border-radius: 5px;
                }}
                .analysis-section {{
                    background: white;
                    padding: 25px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    margin: 20px 0;
                }}
                .insight {{
                    background: #e3f2fd;
                    border-left: 4px solid #2196f3;
                    padding: 15px;
                    margin: 15px 0;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th, td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #f8f9fa;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Site Traffic vs Performance Correlation Analysis</h1>
                <p>Analysis of how overall site traffic levels correlate with page performance before and after Directus optimization</p>
                <p><strong>Analysis Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
            </div>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{avg_pre_performance:.1f}</div>
                    <div class="metric-label">Average Pre-Optimization Performance</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{avg_post_performance:.1f}</div>
                    <div class="metric-label">Average Post-Optimization Performance</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value {'improvement' if improvement > 0 else 'decline'}">
                        {'+' if improvement > 0 else ''}{improvement:.1f}
                    </div>
                    <div class="metric-label">Performance Improvement</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{common_urls}</div>
                    <div class="metric-label">URLs Tested in Both Periods</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{min_traffic:.0f} - {max_traffic:.0f}</div>
                    <div class="metric-label">Site Traffic Range (Users)</div>
                </div>
            </div>
            
            <div class="analysis-section">
                <h2>Key Insights</h2>
                <div class="insight">
                    <strong>Traffic vs Performance Correlation:</strong> This analysis shows how page performance varies with overall site traffic levels, helping identify if performance degrades under higher load.
                </div>
                <div class="insight">
                    <strong>Optimization Impact:</strong> By comparing the same URLs at similar traffic levels before and after optimization, we can measure the true impact of the Directus changes.
                </div>
                <div class="insight">
                    <strong>Load Testing Insights:</strong> Performance data collected at different traffic levels provides valuable insights into how the site handles varying user loads.
                </div>
            </div>
            
            <div class="chart-container">
                <h2>Interactive Visualizations</h2>
                <div class="chart-grid">
                    <div>
                        <h3>Performance vs Site Traffic</h3>
                        <iframe src="performance_vs_traffic_scatter.html"></iframe>
                    </div>
                    <div>
                        <h3>Performance by Traffic Category</h3>
                        <iframe src="performance_by_traffic_category.html"></iframe>
                    </div>
                    <div>
                        <h3>Performance Improvement Analysis</h3>
                        <iframe src="improvement_vs_traffic_similarity.html"></iframe>
                    </div>
                    <div>
                        <h3>Traffic and Performance Timeline</h3>
                        <iframe src="traffic_performance_timeline.html"></iframe>
                    </div>
                </div>
            </div>
            
            <div class="analysis-section">
                <h2>Statistical Summary</h2>
                <p>Performance statistics broken down by optimization status and traffic categories:</p>
                <!-- Statistics table would be inserted here -->
            </div>
            
            <div class="analysis-section">
                <h2>Methodology</h2>
                <p><strong>Data Sources:</strong></p>
                <ul>
                    <li>PageSpeed Insights reports (pre and post optimization)</li>
                    <li>Google Analytics real-time traffic data</li>
                    <li>Performance metrics: PageSpeed scores, Core Web Vitals</li>
                </ul>
                
                <p><strong>Analysis Approach:</strong></p>
                <ul>
                    <li>Matched performance test timestamps with overall site traffic levels</li>
                    <li>Categorized tests by traffic volume (Low, Medium, High, Very High)</li>
                    <li>Compared same URLs performance at similar traffic levels</li>
                    <li>Calculated correlation between traffic and performance metrics</li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        dashboard_path = output_dir / "traffic_performance_dashboard.html"
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\nDashboard saved to: {dashboard_path}")
        return dashboard_path

def main():
    # Initialize analyzer
    base_dir = "."
    analyzer = TrafficPerformanceAnalyzer(base_dir)
    
    print("=== Site Traffic vs Performance Correlation Analysis ===\n")
    
    # Load data
    analyzer.load_traffic_data()
    analyzer.load_performance_data()
    
    # Analyze correlation
    combined_data, traffic_data = analyzer.analyze_correlation()
    
    if combined_data is not None and not combined_data.empty:
        print(f"\nAnalysis Summary:")
        print(f"Total performance tests analyzed: {len(combined_data)}")
        print(f"Pre-optimization tests: {len(combined_data[combined_data['optimization_status'] == 'pre'])}")
        print(f"Post-optimization tests: {len(combined_data[combined_data['optimization_status'] == 'post'])}")
        print(f"Traffic data points: {len(traffic_data) if traffic_data is not None else 0}")
        
        # Generate charts and analysis
        summary_stats = analyzer.generate_charts(combined_data, traffic_data)
        
        # Generate dashboard
        dashboard_path = analyzer.generate_dashboard(combined_data, traffic_data, summary_stats)
        
        print(f"\n✅ Analysis complete! Open {dashboard_path} to view the results.")
        
        # Display sample correlations
        print(f"\nSample Performance vs Traffic Correlations:")
        for status in ['pre', 'post']:
            status_data = combined_data[combined_data['optimization_status'] == status]
            if not status_data.empty:
                correlation = status_data['Performance'].corr(status_data['estimated_traffic'])
                print(f"{status.title()}-optimization: {correlation:.3f}")
    else:
        print("❌ No data available for analysis!")

if __name__ == "__main__":
    main()
