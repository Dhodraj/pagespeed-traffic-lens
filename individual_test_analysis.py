#!/usr/bin/env python3
"""
Individual Test Analysis - No Averaging
Shows every individual performance test result without averaging,
comparing exact performance and traffic levels for each test instance.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
from datetime import datetime
import re

class IndividualTestAnalyzer:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.pre_optimization_dir = self.base_dir / "pagespeed-reports"
        self.post_optimization_dir = self.base_dir / "pagespeed-reports-cron"
        self.traffic_file = self.post_optimization_dir / "Realtime Tracking Automation - India & US - Jul - 2025.csv"
        
        self.traffic_data = None
        self.pre_data = None
        self.post_data = None
        
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
        
        return datetime(2025, 7, 8, 15, 0)
    
    def extract_timestamp_from_filename(self, filename):
        """Extract timestamp from filenames."""
        try:
            # Pattern: pagespeed-report-2025-07-11T12-10-47-363Z.csv
            match = re.search(r'(\\d{4})-(\\d{2})-(\\d{2})T(\\d{2})-(\\d{2})-(\\d{2})', filename)
            if match:
                year, month, day, hour, minute, second = map(int, match.groups())
                return datetime(year, month, day, hour, minute, second)
        except:
            pass
        
        return datetime(2025, 7, 11, 17, 0)
    
    def load_all_performance_data(self):
        """Load ALL individual performance tests without any averaging."""
        print("Loading ALL individual performance test data...")
        
        # Load pre-optimization data
        pre_files = list(self.pre_optimization_dir.glob("*/article-qa.csv"))
        pre_files.extend(list(self.pre_optimization_dir.glob("*/pagespeed-report-*.csv")))
        
        pre_data_list = []
        for file_path in pre_files:
            try:
                df = pd.read_csv(file_path)
                if 'URL' in df.columns and 'Performance' in df.columns:
                    folder_name = file_path.parent.name
                    timestamp = self.extract_timestamp_from_folder(folder_name)
                    
                    df['timestamp'] = timestamp
                    df['optimization_status'] = 'pre'
                    df['source_file'] = str(file_path)
                    df['test_id'] = f"pre_{folder_name}_{df.index}"
                    
                    pre_data_list.append(df)
                    print(f"Pre-optimization: {file_path.name} - {len(df)} individual tests")
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        
        if pre_data_list:
            self.pre_data = pd.concat(pre_data_list, ignore_index=True)
            print(f"Total pre-optimization individual tests: {len(self.pre_data)}")
        
        # Load post-optimization data
        post_folders = [d for d in self.post_optimization_dir.iterdir() 
                       if d.is_dir() and d.name.startswith('2025-')]
        
        post_data_list = []
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
                        df['test_id'] = f"post_{file_path.stem}_{df.index}"
                        
                        post_data_list.append(df)
                        print(f"Post-optimization: {file_path.name} - {len(df)} individual tests")
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
        
        if post_data_list:
            self.post_data = pd.concat(post_data_list, ignore_index=True)
            print(f"Total post-optimization individual tests: {len(self.post_data)}")
    
    def analyze_individual_tests(self):
        """Analyze every individual test without averaging."""
        # Combine all data
        all_data = []
        if self.pre_data is not None and not self.pre_data.empty:
            all_data.append(self.pre_data)
        if self.post_data is not None and not self.post_data.empty:
            all_data.append(self.post_data)
        
        if not all_data:
            print("No performance data available!")
            return pd.DataFrame()
        
        combined_data = pd.concat(all_data, ignore_index=True)
        
        # Clean data
        combined_data = combined_data.dropna(subset=['Performance', 'URL'])
        combined_data = combined_data[combined_data['Performance'] > 0]
        
        # Add traffic estimates for each individual test
        combined_data['estimated_traffic'] = combined_data['timestamp'].apply(self.estimate_traffic_at_time)
        
        print(f"\\nIndividual Test Analysis Summary:")
        print(f"Total individual tests: {len(combined_data)}")
        print(f"Pre-optimization tests: {len(combined_data[combined_data['optimization_status'] == 'pre'])}")
        print(f"Post-optimization tests: {len(combined_data[combined_data['optimization_status'] == 'post'])}")
        print(f"Unique URLs tested: {combined_data['URL'].nunique()}")
        
        return combined_data
    
    def identify_individual_poor_performers(self, combined_data, threshold_percentile=25):
        """Identify individual poor performing tests (not URL averages)."""
        pre_data = combined_data[combined_data['optimization_status'] == 'pre']
        
        if pre_data.empty:
            print("No pre-optimization data available")
            return pd.DataFrame(), 0
        
        # Calculate threshold based on individual test scores
        threshold = np.percentile(pre_data['Performance'], threshold_percentile)
        print(f"\\nIndividual test performance threshold ({threshold_percentile}th percentile): {threshold:.1f}")
        
        # Find all individual tests below threshold
        poor_individual_tests = pre_data[pre_data['Performance'] <= threshold].copy()
        
        print(f"Individual poor performing tests: {len(poor_individual_tests)}")
        print(f"URLs represented in poor tests: {poor_individual_tests['URL'].nunique()}")
        
        return poor_individual_tests, threshold
    
    def compare_individual_poor_performers(self, poor_tests, combined_data, threshold):
        """Compare individual poor performing tests with post-optimization data."""
        post_data = combined_data[combined_data['optimization_status'] == 'post']
        
        # Get URLs that had poor individual tests
        poor_urls = poor_tests['URL'].unique()
        print(f"\\nURLs with poor individual tests: {len(poor_urls)}")
        
        # Find these URLs in post-optimization data
        post_poor_urls = post_data[post_data['URL'].isin(poor_urls)]
        print(f"Individual post-optimization tests for these URLs: {len(post_poor_urls)}")
        
        # Create comparison showing individual test variations
        comparison_results = []
        
        for url in poor_urls:
            url_poor_tests = poor_tests[poor_tests['URL'] == url]
            url_post_tests = post_poor_urls[post_poor_urls['URL'] == url]
            
            if not url_post_tests.empty:
                # Add individual test comparisons
                for _, poor_test in url_poor_tests.iterrows():
                    for _, post_test in url_post_tests.iterrows():
                        comparison_results.append({
                            'URL': url,
                            'URL_short': url.split('/')[-1][:50] if '/' in url else url[:50],
                            'Poor_Test_Performance': poor_test['Performance'],
                            'Poor_Test_Traffic': poor_test['estimated_traffic'],
                            'Poor_Test_Timestamp': poor_test['timestamp'],
                            'Poor_Test_FCP': poor_test.get('First Contentful Paint (ms)', 0),
                            'Poor_Test_LCP': poor_test.get('Largest Contentful Paint (ms)', 0),
                            'Poor_Test_TBT': poor_test.get('Total Blocking Time (ms)', 0),
                            'Post_Test_Performance': post_test['Performance'],
                            'Post_Test_Traffic': post_test['estimated_traffic'],
                            'Post_Test_Timestamp': post_test['timestamp'],
                            'Post_Test_FCP': post_test.get('First Contentful Paint (ms)', 0),
                            'Post_Test_LCP': post_test.get('Largest Contentful Paint (ms)', 0),
                            'Post_Test_TBT': post_test.get('Total Blocking Time (ms)', 0),
                            'Performance_Improvement': post_test['Performance'] - poor_test['Performance'],
                            'Traffic_Similarity': abs(post_test['estimated_traffic'] - poor_test['estimated_traffic']),
                            'FCP_Change': poor_test.get('First Contentful Paint (ms)', 0) - post_test.get('First Contentful Paint (ms)', 0),
                            'LCP_Change': poor_test.get('Largest Contentful Paint (ms)', 0) - post_test.get('Largest Contentful Paint (ms)', 0),
                            'TBT_Change': poor_test.get('Total Blocking Time (ms)', 0) - post_test.get('Total Blocking Time (ms)', 0)
                        })
        
        if comparison_results:
            comparison_df = pd.DataFrame(comparison_results)
            print(f"Individual test comparisons created: {len(comparison_df)}")
            return comparison_df
        
        return pd.DataFrame()
    
    def create_individual_analysis_report(self, poor_tests, comparison_df, combined_data, threshold):
        """Create detailed report showing individual test variations."""
        output_dir = self.base_dir / "individual_test_analysis"
        output_dir.mkdir(exist_ok=True)
        
        # Save raw data
        poor_tests.to_csv(output_dir / "individual_poor_tests.csv", index=False)
        if not comparison_df.empty:
            comparison_df.to_csv(output_dir / "individual_test_comparisons.csv", index=False)
        combined_data.to_csv(output_dir / "all_individual_tests.csv", index=False)
        
        # Create visualizations
        if not comparison_df.empty:
            # 1. Individual test scatter plot
            fig = px.scatter(
                comparison_df,
                x='Poor_Test_Performance',
                y='Post_Test_Performance',
                color='Traffic_Similarity',
                size='Performance_Improvement',
                hover_data=['URL_short', 'Poor_Test_Traffic', 'Post_Test_Traffic'],
                title='Individual Test Comparison: Every Poor Test vs Post-Optimization Tests',
                labels={
                    'Poor_Test_Performance': 'Poor Test Performance Score',
                    'Post_Test_Performance': 'Post-Optimization Test Performance Score',
                    'Traffic_Similarity': 'Traffic Difference',
                    'Performance_Improvement': 'Performance Improvement'
                }
            )
            
            # Add diagonal line
            min_perf = min(comparison_df['Poor_Test_Performance'].min(), comparison_df['Post_Test_Performance'].min())
            max_perf = max(comparison_df['Poor_Test_Performance'].max(), comparison_df['Post_Test_Performance'].max())
            fig.add_trace(
                go.Scatter(
                    x=[min_perf, max_perf],
                    y=[min_perf, max_perf],
                    mode='lines',
                    line=dict(dash='dash', color='red'),
                    name='No Improvement Line'
                )
            )
            
            fig.update_layout(height=600, width=1000)
            fig.write_html(output_dir / "individual_tests_comparison.html")
            
            # 2. Performance distribution by optimization status
            fig = px.histogram(
                combined_data,
                x='Performance',
                color='optimization_status',
                nbins=30,
                title='Performance Score Distribution: Individual Tests',
                labels={'Performance': 'Performance Score', 'count': 'Number of Individual Tests'},
                barmode='overlay',
                opacity=0.7
            )
            fig.add_vline(x=threshold, line_dash="dash", line_color="red", 
                         annotation_text=f"Poor Performance Threshold: {threshold}")
            fig.update_layout(height=500, width=800)
            fig.write_html(output_dir / "performance_distribution_individual.html")
        
        # Generate HTML report
        if not comparison_df.empty:
            improvements = comparison_df['Performance_Improvement']
            avg_improvement = improvements.mean()
            median_improvement = improvements.median()
            min_improvement = improvements.min()
            max_improvement = improvements.max()
            improved_count = len(improvements[improvements > 0])
            total_comparisons = len(improvements)
        else:
            avg_improvement = median_improvement = min_improvement = max_improvement = 0
            improved_count = total_comparisons = 0
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Individual Test Analysis - No Averaging</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                    line-height: 1.6;
                }}
                .header {{
                    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .alert {{
                    background: #fff3cd;
                    border: 1px solid #ffeaa7;
                    border-radius: 5px;
                    padding: 15px;
                    margin: 20px 0;
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
                    color: #2c3e50;
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
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th, td {{
                    padding: 10px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #f8f9fa;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Individual Test Analysis</h1>
                <h2>No Averaging - Raw Individual Performance Test Results</h2>
                <p><strong>Analysis Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
            </div>
            
            <div class="alert">
                <strong>⚠️ Important:</strong> This analysis shows <strong>individual test results</strong> without any averaging. 
                Each data point represents a single PageSpeed test run at a specific time with specific traffic conditions.
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{len(combined_data)}</div>
                    <div>Total Individual Tests</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(poor_tests)}</div>
                    <div>Poor Individual Tests (≤{threshold:.1f})</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{total_comparisons:,}</div>
                    <div>Individual Test Comparisons</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{improved_count}</div>
                    <div>Comparisons Showing Improvement</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{avg_improvement:.1f}</div>
                    <div>Average Improvement</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{max_improvement:.1f}</div>
                    <div>Best Individual Improvement</div>
                </div>
            </div>
            
            <div class="chart-container">
                <h3>Individual Test Performance Distribution</h3>
                <iframe src="performance_distribution_individual.html"></iframe>
            </div>
            
            <div class="chart-container">
                <h3>Individual Test Comparisons</h3>
                <iframe src="individual_tests_comparison.html"></iframe>
            </div>
            
            <div class="chart-container">
                <h3>Raw Data Analysis</h3>
                <p><strong>Pre-Optimization Individual Tests:</strong></p>
                <ul>
                    <li>Total tests: {len(combined_data[combined_data['optimization_status'] == 'pre'])}</li>
                    <li>Performance range: {combined_data[combined_data['optimization_status'] == 'pre']['Performance'].min():.1f} - {combined_data[combined_data['optimization_status'] == 'pre']['Performance'].max():.1f}</li>
                    <li>Average: {combined_data[combined_data['optimization_status'] == 'pre']['Performance'].mean():.1f}</li>
                </ul>
                
                <p><strong>Post-Optimization Individual Tests:</strong></p>
                <ul>
                    <li>Total tests: {len(combined_data[combined_data['optimization_status'] == 'post'])}</li>
                    <li>Performance range: {combined_data[combined_data['optimization_status'] == 'post']['Performance'].min():.1f} - {combined_data[combined_data['optimization_status'] == 'post']['Performance'].max():.1f}</li>
                    <li>Average: {combined_data[combined_data['optimization_status'] == 'post']['Performance'].mean():.1f}</li>
                </ul>
            </div>
            
            <div class="chart-container">
                <h3>Data Files Generated</h3>
                <ul>
                    <li><strong>all_individual_tests.csv</strong> - Every single test result with timestamps and traffic</li>
                    <li><strong>individual_poor_tests.csv</strong> - All individual tests scoring ≤{threshold:.1f}</li>
                    <li><strong>individual_test_comparisons.csv</strong> - Detailed comparisons between poor and post-optimization tests</li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        report_path = output_dir / "individual_test_analysis_report.html"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\\nIndividual test analysis report saved to: {report_path}")
        return report_path, output_dir

def main():
    base_dir = "."
    analyzer = IndividualTestAnalyzer(base_dir)
    
    print("=== INDIVIDUAL TEST ANALYSIS (NO AVERAGING) ===\\n")
    
    # Load data
    analyzer.load_traffic_data()
    analyzer.load_all_performance_data()
    
    # Analyze individual tests
    combined_data = analyzer.analyze_individual_tests()
    
    if combined_data.empty:
        print("No data available for analysis!")
        return
    
    # Identify poor individual tests
    poor_tests, threshold = analyzer.identify_individual_poor_performers(combined_data)
    
    if poor_tests.empty:
        print("No poor performing individual tests found!")
        return
    
    # Compare individual tests
    comparison_df = analyzer.compare_individual_poor_performers(poor_tests, combined_data, threshold)
    
    # Generate report
    report_path, output_dir = analyzer.create_individual_analysis_report(
        poor_tests, comparison_df, combined_data, threshold
    )
    
    print(f"\\n✅ Individual test analysis complete!")
    print(f"📊 Report: {report_path}")
    print(f"📁 Data files: {output_dir}")
    
    if not comparison_df.empty:
        print(f"\\n📈 Individual Test Results Summary:")
        print(f"   • Total individual test comparisons: {len(comparison_df):,}")
        print(f"   • Tests showing improvement: {len(comparison_df[comparison_df['Performance_Improvement'] > 0])}")
        print(f"   • Average improvement: {comparison_df['Performance_Improvement'].mean():.1f} points")
        print(f"   • Best improvement: {comparison_df['Performance_Improvement'].max():.1f} points")
        print(f"   • Worst result: {comparison_df['Performance_Improvement'].min():.1f} points")

if __name__ == "__main__":
    main()
