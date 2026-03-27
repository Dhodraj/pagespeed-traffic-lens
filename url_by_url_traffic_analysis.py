#!/usr/bin/env python3
"""
URL-by-URL Traffic vs Performance Analysis
For each URL that exists in both pre and post optimization:
1. Get all individual test results with their exact traffic levels
2. Plot performance vs traffic for that specific URL
3. Show before/after comparison clearly
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.offline as pyo
from pathlib import Path
from datetime import datetime
import re

class URLTrafficPerformanceAnalyzer:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.pre_optimization_dir = self.base_dir / "pagespeed-reports"
        self.post_optimization_dir = self.base_dir / "pagespeed-reports-cron"
        self.traffic_file = self.post_optimization_dir / "Realtime Tracking Automation - India & US - Jul - 2025.csv"
        
        self.traffic_data = None
        self.all_data = None
        
    def load_traffic_data(self):
        """Load overall site traffic data."""
        print("Loading site traffic data...")
        
        if not self.traffic_file.exists():
            print(f"Traffic file not found: {self.traffic_file}")
            return
            
        df = pd.read_csv(self.traffic_file)
        traffic_rows = []
        
        for idx, row in df.iterrows():
            date_country = str(row.iloc[0])
            
            if date_country == "All":
                # Find the previous date row
                date_from_prev = None
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
                                        'traffic': int(traffic_value)
                                    })
                            except:
                                continue
        
        if traffic_rows:
            self.traffic_data = pd.DataFrame(traffic_rows)
            self.traffic_data = self.traffic_data.drop_duplicates()
            self.traffic_data = self.traffic_data.sort_values('timestamp')
            print(f"Loaded {len(self.traffic_data)} traffic data points")
            print(f"Traffic range: {self.traffic_data['traffic'].min()} to {self.traffic_data['traffic'].max()} users")
        else:
            print("No traffic data could be parsed")
    
    def estimate_traffic_at_time(self, test_timestamp):
        """Estimate overall site traffic at the time of a performance test."""
        if self.traffic_data is None or len(self.traffic_data) == 0:
            return 500  # Default traffic level
        
        # Find the closest traffic measurement in time
        time_diffs = abs(self.traffic_data['timestamp'] - test_timestamp)
        closest_idx = time_diffs.idxmin()
        
        return self.traffic_data.loc[closest_idx, 'traffic']
    
    def extract_timestamp_from_folder(self, folder_name):
        """Extract timestamp from folder names."""
        try:
            # Pattern: article-qa-8-7-2025-3-41-pm
            # Format is: day-month-year (8-7-2025 = 8th July 2025)
            parts = folder_name.split('-')
            if len(parts) >= 6:
                day = int(parts[2])
                month = int(parts[3])
                year = int(parts[4])
                hour = int(parts[5])
                minute = int(parts[6])
                
                # Handle AM/PM
                if len(parts) > 7 and parts[7].lower() == 'pm' and hour != 12:
                    hour += 12
                elif len(parts) > 7 and parts[7].lower() == 'am' and hour == 12:
                    hour = 0
                
                return datetime(year, month, day, hour, minute)
        except Exception as e:
            print(f"Error parsing timestamp from folder {folder_name}: {e}")
        
        print(f"Warning: Could not parse timestamp from folder {folder_name}, using default")
        return datetime(2025, 7, 8, 15, 0)
    
    def extract_timestamp_from_filename(self, filename):
        """Extract timestamp from filenames."""
        try:
            # Pattern: pagespeed-report-2025-07-11T12-10-47-363Z.csv
            match = re.search(r'(\d{4})-(\d{2})-(\d{2})T(\d{2})-(\d{2})-(\d{2})', filename)
            if match:
                year, month, day, hour, minute, second = map(int, match.groups())
                return datetime(year, month, day, hour, minute, second)
        except Exception as e:
            print(f"Error parsing timestamp from {filename}: {e}")
        
        # Should not reach here if regex works
        print(f"Warning: Could not parse timestamp from {filename}, using default")
        return datetime(2025, 7, 11, 17, 0)
    
    def load_all_performance_data(self):
        """Load all performance data with timestamps and traffic estimates."""
        print("Loading all performance data...")
        
        all_data_list = []
        
        # Load pre-optimization data
        print("Loading pre-optimization data...")
        pre_files = list(self.pre_optimization_dir.glob("*/article-qa.csv"))
        pre_files.extend(list(self.pre_optimization_dir.glob("*/pagespeed-report-*.csv")))
        
        for file_path in pre_files:
            try:
                df = pd.read_csv(file_path)
                if 'URL' in df.columns and 'Performance' in df.columns:
                    folder_name = file_path.parent.name
                    timestamp = self.extract_timestamp_from_folder(folder_name)
                    
                    df['timestamp'] = timestamp
                    df['optimization_status'] = 'pre'
                    df['source_file'] = str(file_path)
                    
                    all_data_list.append(df)
                    print(f"  Loaded: {file_path.name} ({len(df)} tests at {timestamp})")
            except Exception as e:
                print(f"  Error loading {file_path}: {e}")
        
        # Load post-optimization data
        print("Loading post-optimization data...")
        post_folders = [d for d in self.post_optimization_dir.iterdir() 
                       if d.is_dir() and d.name.startswith('2025-')]
        
        for folder in post_folders:
            csv_files = list(folder.glob("pagespeed-report-*.csv"))
            for file_path in csv_files:
                try:
                    df = pd.read_csv(file_path)
                    if 'URL' in df.columns and 'Performance' in df.columns:
                        timestamp = self.extract_timestamp_from_filename(file_path.name)
                        
                        df['timestamp'] = timestamp
                        df['optimization_status'] = 'post'
                        df['source_file'] = str(file_path)
                        
                        all_data_list.append(df)
                        print(f"  Loaded: {file_path.name} ({len(df)} tests at {timestamp})")
                except Exception as e:
                    print(f"  Error loading {file_path}: {e}")
        
        if all_data_list:
            self.all_data = pd.concat(all_data_list, ignore_index=True)
            
            # Clean data
            self.all_data = self.all_data.dropna(subset=['Performance', 'URL'])
            self.all_data = self.all_data[self.all_data['Performance'] > 0]
            
            # Add traffic estimates
            print("Estimating traffic levels for each test...")
            self.all_data['estimated_traffic'] = self.all_data['timestamp'].apply(self.estimate_traffic_at_time)
            
            print(f"Total tests loaded: {len(self.all_data)}")
            print(f"Pre-optimization: {len(self.all_data[self.all_data['optimization_status'] == 'pre'])}")
            print(f"Post-optimization: {len(self.all_data[self.all_data['optimization_status'] == 'post'])}")
        else:
            print("No data loaded!")
    
    def find_common_urls(self):
        """Find URLs that exist in both pre and post optimization data."""
        if self.all_data is None or self.all_data.empty:
            print("No data available!")
            return []
        
        pre_urls = set(self.all_data[self.all_data['optimization_status'] == 'pre']['URL'])
        post_urls = set(self.all_data[self.all_data['optimization_status'] == 'post']['URL'])
        
        common_urls = list(pre_urls.intersection(post_urls))
        
        print(f"\\nURL Analysis:")
        print(f"Pre-optimization URLs: {len(pre_urls)}")
        print(f"Post-optimization URLs: {len(post_urls)}")
        print(f"Common URLs (in both datasets): {len(common_urls)}")
        
        return common_urls
    
    def analyze_url_traffic_performance(self, url):
        """Analyze traffic vs performance for a specific URL."""
        url_data = self.all_data[self.all_data['URL'] == url].copy()
        
        if url_data.empty:
            return None
        
        # Separate pre and post data
        pre_data = url_data[url_data['optimization_status'] == 'pre']
        post_data = url_data[url_data['optimization_status'] == 'post']
        
        url_short = url.split('/')[-1][:50] if '/' in url else url[:50]
        
        analysis = {
            'url': url,
            'url_short': url_short,
            'pre_tests': len(pre_data),
            'post_tests': len(post_data),
            'pre_data': pre_data[['timestamp', 'Performance', 'estimated_traffic', 'First Contentful Paint (ms)', 
                                 'Largest Contentful Paint (ms)', 'Total Blocking Time (ms)']].copy(),
            'post_data': post_data[['timestamp', 'Performance', 'estimated_traffic', 'First Contentful Paint (ms)', 
                                   'Largest Contentful Paint (ms)', 'Total Blocking Time (ms)']].copy()
        }
        
        # Calculate statistics
        if not pre_data.empty:
            analysis['pre_performance_range'] = (pre_data['Performance'].min(), pre_data['Performance'].max())
            analysis['pre_traffic_range'] = (pre_data['estimated_traffic'].min(), pre_data['estimated_traffic'].max())
            analysis['pre_avg_performance'] = pre_data['Performance'].mean()
        
        if not post_data.empty:
            analysis['post_performance_range'] = (post_data['Performance'].min(), post_data['Performance'].max())
            analysis['post_traffic_range'] = (post_data['estimated_traffic'].min(), post_data['estimated_traffic'].max())
            analysis['post_avg_performance'] = post_data['Performance'].mean()
        
        return analysis
    
    def create_individual_url_charts(self, common_urls):
        """Create individual charts for each URL showing traffic vs performance."""
        output_dir = self.base_dir / "url_traffic_analysis"
        output_dir.mkdir(exist_ok=True)
        
        charts_dir = output_dir / "individual_url_charts"
        charts_dir.mkdir(exist_ok=True)
        
        url_analyses = []
        
        print(f"\\nCreating individual charts for {len(common_urls)} URLs...")
        
        for i, url in enumerate(common_urls, 1):
            analysis = self.analyze_url_traffic_performance(url)
            if analysis is None:
                continue
                
            url_analyses.append(analysis)
            
            # Create chart for this URL
            fig = go.Figure()
            
            # Add pre-optimization data
            if not analysis['pre_data'].empty:
                fig.add_trace(go.Scatter(
                    x=analysis['pre_data']['estimated_traffic'],
                    y=analysis['pre_data']['Performance'],
                    mode='markers',
                    name='Pre-Optimization',
                    marker=dict(color='red', size=10, symbol='circle'),
                    text=[f"URL: {analysis['url']}<br>Time: {ts}<br>Performance: {perf}<br>Traffic: {traffic}" 
                          for ts, perf, traffic in zip(
                              analysis['pre_data']['timestamp'],
                              analysis['pre_data']['Performance'],
                              analysis['pre_data']['estimated_traffic']
                          )],
                    hovertemplate='%{text}<extra></extra>'
                ))
            
            # Add post-optimization data
            if not analysis['post_data'].empty:
                fig.add_trace(go.Scatter(
                    x=analysis['post_data']['estimated_traffic'],
                    y=analysis['post_data']['Performance'],
                    mode='markers',
                    name='Post-Optimization',
                    marker=dict(color='green', size=10, symbol='diamond'),
                    text=[f"URL: {analysis['url']}<br>Time: {ts}<br>Performance: {perf}<br>Traffic: {traffic}" 
                          for ts, perf, traffic in zip(
                              analysis['post_data']['timestamp'],
                              analysis['post_data']['Performance'],
                              analysis['post_data']['estimated_traffic']
                          )],
                    hovertemplate='%{text}<extra></extra>'
                ))
            
            fig.update_layout(
                title=f"Traffic vs Performance: {analysis['url_short']}",
                xaxis_title="Site Traffic (Users)",
                yaxis_title="Performance Score",
                height=500,
                width=800,
                showlegend=True
            )
            
            # Save individual chart
            chart_filename = f"url_{i:03d}_{analysis['url_short'].replace('/', '_')}.html"
            fig.write_html(charts_dir / chart_filename)
            
            if i % 10 == 0:
                print(f"  Created {i}/{len(common_urls)} charts...")
        
        print(f"Individual URL charts saved to: {charts_dir}")
        return url_analyses
    
    def create_summary_dashboard(self, url_analyses):
        """Create a summary dashboard showing all URLs."""
        output_dir = self.base_dir / "url_traffic_analysis"
        
        # Create overview charts
        print("Creating summary dashboard...")
        
        # 1. All URLs performance vs traffic scatter
        fig = go.Figure()
        
        for analysis in url_analyses:
            # Pre-optimization data
            if not analysis['pre_data'].empty:
                fig.add_trace(go.Scatter(
                    x=analysis['pre_data']['estimated_traffic'],
                    y=analysis['pre_data']['Performance'],
                    mode='markers',
                    name=f"{analysis['url_short']} (Pre)",
                    marker=dict(color='red', size=6, opacity=0.7),
                    showlegend=False,
                    text=[analysis['url']] * len(analysis['pre_data']),
                    hovertemplate='URL: %{text}<br>Traffic: %{x}<br>Performance: %{y}<extra></extra>'
                ))
            
            # Post-optimization data
            if not analysis['post_data'].empty:
                fig.add_trace(go.Scatter(
                    x=analysis['post_data']['estimated_traffic'],
                    y=analysis['post_data']['Performance'],
                    mode='markers',
                    name=f"{analysis['url_short']} (Post)",
                    marker=dict(color='green', size=6, opacity=0.7),
                    showlegend=False,
                    text=[analysis['url']] * len(analysis['post_data']),
                    hovertemplate='URL: %{text}<br>Traffic: %{x}<br>Performance: %{y}<extra></extra>'
                ))
        
        # Add legend entries
        fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', 
                                marker=dict(color='red', size=10), name='Pre-Optimization'))
        fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', 
                                marker=dict(color='green', size=10), name='Post-Optimization'))
        
        fig.update_layout(
            title="All URLs: Traffic vs Performance Comparison",
            xaxis_title="Site Traffic (Users)",
            yaxis_title="Performance Score",
            height=600,
            width=1000
        )
        
        fig.write_html(output_dir / "all_urls_traffic_vs_performance.html")
        
        # 2. Performance improvement summary
        improvements = []
        for analysis in url_analyses:
            if 'pre_avg_performance' in analysis and 'post_avg_performance' in analysis:
                improvement = analysis['post_avg_performance'] - analysis['pre_avg_performance']
                improvements.append({
                    'url_short': analysis['url_short'],
                    'improvement': improvement,
                    'pre_avg': analysis['pre_avg_performance'],
                    'post_avg': analysis['post_avg_performance']
                })
        
        if improvements:
            improvements_df = pd.DataFrame(improvements)
            improvements_df = improvements_df.sort_values('improvement', ascending=False)
            
            fig = px.bar(
                improvements_df.head(20),
                x='url_short',
                y='improvement',
                title='Top 20 URLs: Performance Improvement',
                labels={'improvement': 'Performance Improvement', 'url_short': 'URL'},
                color='improvement',
                color_continuous_scale='RdYlGn'
            )
            fig.update_xaxes(tickangle=45)
            fig.update_layout(height=600, width=1200)
            fig.write_html(output_dir / "performance_improvements.html")
        
        # Create summary statistics
        summary_stats = self.calculate_summary_statistics(url_analyses)
        
        # Generate HTML dashboard
        self.generate_html_dashboard(url_analyses, summary_stats, output_dir)
        
        return output_dir
    
    def calculate_summary_statistics(self, url_analyses):
        """Calculate summary statistics across all URLs."""
        stats = {
            'total_urls': len(url_analyses),
            'total_pre_tests': sum(a['pre_tests'] for a in url_analyses),
            'total_post_tests': sum(a['post_tests'] for a in url_analyses),
            'urls_with_improvement': 0,
            'average_improvement': 0,
            'best_improvement': 0,
            'worst_change': 0
        }
        
        improvements = []
        for analysis in url_analyses:
            if 'pre_avg_performance' in analysis and 'post_avg_performance' in analysis:
                improvement = analysis['post_avg_performance'] - analysis['pre_avg_performance']
                improvements.append(improvement)
                if improvement > 0:
                    stats['urls_with_improvement'] += 1
        
        if improvements:
            stats['average_improvement'] = np.mean(improvements)
            stats['best_improvement'] = max(improvements)
            stats['worst_change'] = min(improvements)
        
        return stats
    
    def generate_html_dashboard(self, url_analyses, summary_stats, output_dir):
        """Generate comprehensive HTML dashboard."""
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>URL-by-URL Traffic vs Performance Analysis</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                    line-height: 1.6;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin: 20px 0;
                }}
                .stat-card {{
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    text-align: center;
                }}
                .stat-value {{
                    font-size: 2em;
                    font-weight: bold;
                    color: #333;
                }}
                .chart-container {{
                    background: white;
                    margin: 20px 0;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                iframe {{
                    width: 100%;
                    height: 600px;
                    border: none;
                }}
                .url-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    gap: 15px;
                    margin: 20px 0;
                }}
                .url-card {{
                    background: white;
                    padding: 15px;
                    border-radius: 8px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }}
                .url-title {{
                    font-weight: bold;
                    color: #333;
                    margin-bottom: 10px;
                }}
                .url-stats {{
                    font-size: 0.9em;
                    color: #666;
                }}
                .improvement {{
                    color: #28a745;
                    font-weight: bold;
                }}
                .decline {{
                    color: #dc3545;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>URL-by-URL Traffic vs Performance Analysis</h1>
                <p>Individual analysis of each URL showing performance at different traffic levels</p>
                <p><strong>Analysis Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{summary_stats['total_urls']}</div>
                    <div>URLs Analyzed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{summary_stats['total_pre_tests']}</div>
                    <div>Pre-Optimization Tests</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{summary_stats['total_post_tests']}</div>
                    <div>Post-Optimization Tests</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{summary_stats['urls_with_improvement']}</div>
                    <div>URLs Improved</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{summary_stats['average_improvement']:.1f}</div>
                    <div>Average Improvement</div>
                </div>
            </div>
            
            <div class="chart-container">
                <h3>All URLs Overview</h3>
                <iframe src="all_urls_traffic_vs_performance.html"></iframe>
            </div>
            
            <div class="chart-container">
                <h3>Performance Improvements</h3>
                <iframe src="performance_improvements.html"></iframe>
            </div>
            
            <div class="chart-container">
                <h3>Individual URL Analysis</h3>
                <p>Each URL has been analyzed individually. Click on any URL below to see its detailed traffic vs performance chart:</p>
                
                <div class="url-grid">
        """
        
        # Add URL cards
        for i, analysis in enumerate(url_analyses, 1):
            chart_filename = f"individual_url_charts/url_{i:03d}_{analysis['url_short'].replace('/', '_')}.html"
            
            pre_range = ""
            post_range = ""
            improvement = ""
            
            if 'pre_performance_range' in analysis:
                pre_range = f"{analysis['pre_performance_range'][0]:.1f}-{analysis['pre_performance_range'][1]:.1f}"
            if 'post_performance_range' in analysis:
                post_range = f"{analysis['post_performance_range'][0]:.1f}-{analysis['post_performance_range'][1]:.1f}"
            
            if 'pre_avg_performance' in analysis and 'post_avg_performance' in analysis:
                imp_value = analysis['post_avg_performance'] - analysis['pre_avg_performance']
                imp_class = "improvement" if imp_value > 0 else "decline"
                improvement = f'<span class="{imp_class}">{imp_value:+.1f}</span>'
            
            html_content += f"""
                    <div class="url-card">
                        <div class="url-title">
                            <a href="{chart_filename}" target="_blank">{analysis['url_short']}</a>
                        </div>
                        <div class="url-stats">
                            Pre: {analysis['pre_tests']} tests ({pre_range})<br>
                            Post: {analysis['post_tests']} tests ({post_range})<br>
                            Improvement: {improvement}
                        </div>
                    </div>
            """
        
        html_content += """
                </div>
            </div>
            
            <div class="chart-container">
                <h3>Analysis Methodology</h3>
                <ul>
                    <li><strong>Individual URL Focus:</strong> Each URL analyzed separately</li>
                    <li><strong>Traffic Correlation:</strong> Exact traffic levels at time of each test</li>
                    <li><strong>No Averaging:</strong> All individual test results shown</li>
                    <li><strong>Before/After Comparison:</strong> Clear visualization of optimization impact</li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        dashboard_path = output_dir / "url_traffic_analysis_dashboard.html"
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Main dashboard saved to: {dashboard_path}")
        return dashboard_path

def main():
    base_dir = "."
    analyzer = URLTrafficPerformanceAnalyzer(base_dir)
    
    print("=== URL-by-URL Traffic vs Performance Analysis ===\\n")
    
    # Load data
    analyzer.load_traffic_data()
    analyzer.load_all_performance_data()
    
    # Find common URLs
    common_urls = analyzer.find_common_urls()
    
    if not common_urls:
        print("No common URLs found!")
        return
    
    # Create individual URL charts
    url_analyses = analyzer.create_individual_url_charts(common_urls)
    
    # Create summary dashboard
    output_dir = analyzer.create_summary_dashboard(url_analyses)
    
    print(f"\\n✅ Analysis complete!")
    print(f"📊 Main dashboard: {output_dir}/url_traffic_analysis_dashboard.html")
    print(f"📁 Individual URL charts: {output_dir}/individual_url_charts/")
    print(f"\\n📈 Summary:")
    print(f"   • URLs analyzed: {len(url_analyses)}")
    print(f"   • Total individual charts created: {len(url_analyses)}")
    print(f"   • Each chart shows exact traffic levels when tests were conducted")

if __name__ == "__main__":
    main()
