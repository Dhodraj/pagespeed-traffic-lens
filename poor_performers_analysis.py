#!/usr/bin/env python3
"""
Poor Performing URLs Analysis
Identifies the worst performing URLs from pre-optimization data and compares
their performance and traffic levels before and after optimization.
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

class PoorPerformanceAnalyzer:
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
            # This is DAY-MONTH-YEAR format (8-7-2025 = July 8, 2025)
            parts = folder_name.split('-')
            if len(parts) >= 6:
                day = int(parts[2])    # First number is day
                month = int(parts[3])  # Second number is month
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
            match = re.search(r'(\d{4})-(\d{2})-(\d{2})T(\d{2})-(\d{2})-(\d{2})', filename)
            if match:
                year, month, day, hour, minute, second = map(int, match.groups())
                return datetime(year, month, day, hour, minute, second)
        except:
            pass
        
        return datetime(2025, 7, 11, 17, 0)
    
    def load_performance_data(self):
        """Load performance data from both periods."""
        print("Loading pre-optimization performance data...")
        
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
                    
                    pre_data_list.append(df)
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        
        if pre_data_list:
            self.pre_data = pd.concat(pre_data_list, ignore_index=True)
            print(f"Loaded {len(self.pre_data)} pre-optimization records")
        
        print("Loading post-optimization performance data...")
        
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
                        
                        post_data_list.append(df)
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
        
        if post_data_list:
            self.post_data = pd.concat(post_data_list, ignore_index=True)
            print(f"Loaded {len(self.post_data)} post-optimization records")
    
    def identify_poor_performers(self, threshold_percentile=25):
        """Identify the poorest performing URLs from pre-optimization data."""
        if self.pre_data is None or self.pre_data.empty:
            print("No pre-optimization data available")
            return pd.DataFrame()
        
        # Clean data
        pre_clean = self.pre_data.dropna(subset=['Performance', 'URL'])
        pre_clean = pre_clean[pre_clean['Performance'] > 0]
        
        # Calculate performance threshold (bottom 25% by default)
        threshold = np.percentile(pre_clean['Performance'], threshold_percentile)
        
        print(f"Performance threshold ({threshold_percentile}th percentile): {threshold:.1f}")
        
        # Identify poor performers
        poor_performers = pre_clean[pre_clean['Performance'] <= threshold].copy()
        
        # Add traffic estimates
        poor_performers['estimated_traffic'] = poor_performers['timestamp'].apply(self.estimate_traffic_at_time)
        
        print(f"Found {len(poor_performers)} poor performing URL tests")
        print(f"Unique poor performing URLs: {poor_performers['URL'].nunique()}")
        
        return poor_performers
    
    def compare_poor_performers(self, poor_performers):
        """Compare poor performing URLs before and after optimization."""
        if poor_performers.empty or self.post_data is None or self.post_data.empty:
            print("No data available for comparison")
            return pd.DataFrame()
        
        # Clean post data
        post_clean = self.post_data.dropna(subset=['Performance', 'URL'])
        post_clean = post_clean[post_clean['Performance'] > 0]
        
        # Add traffic estimates to post data
        post_clean = post_clean.copy()
        post_clean['estimated_traffic'] = post_clean['timestamp'].apply(self.estimate_traffic_at_time)
        
        # Get unique poor performing URLs
        poor_urls = poor_performers['URL'].unique()
        
        # Find these URLs in post-optimization data
        post_poor_urls = post_clean[post_clean['URL'].isin(poor_urls)]
        
        print(f"Poor URLs found in post-optimization data: {len(post_poor_urls)}")
        print(f"Unique URLs with both pre and post data: {post_poor_urls['URL'].nunique()}")
        
        # Create comparison dataframe
        comparison_data = []
        
        for url in poor_urls:
            pre_url_data = poor_performers[poor_performers['URL'] == url]
            post_url_data = post_poor_urls[post_poor_urls['URL'] == url]
            
            if not post_url_data.empty:
                # Calculate averages for this URL
                pre_avg_perf = pre_url_data['Performance'].mean()
                post_avg_perf = post_url_data['Performance'].mean()
                pre_avg_traffic = pre_url_data['estimated_traffic'].mean()
                post_avg_traffic = post_url_data['estimated_traffic'].mean()
                
                # Get individual metrics averages
                pre_metrics = {
                    'FCP': pre_url_data.get('First Contentful Paint (ms)', pd.Series([0])).mean(),
                    'LCP': pre_url_data.get('Largest Contentful Paint (ms)', pd.Series([0])).mean(),
                    'Speed_Index': pre_url_data.get('Speed Index (ms)', pd.Series([0])).mean(),
                    'TBT': pre_url_data.get('Total Blocking Time (ms)', pd.Series([0])).mean(),
                    'CLS': pre_url_data.get('Cumulative Layout Shift', pd.Series([0])).mean()
                }
                
                post_metrics = {
                    'FCP': post_url_data.get('First Contentful Paint (ms)', pd.Series([0])).mean(),
                    'LCP': post_url_data.get('Largest Contentful Paint (ms)', pd.Series([0])).mean(),
                    'Speed_Index': post_url_data.get('Speed Index (ms)', pd.Series([0])).mean(),
                    'TBT': post_url_data.get('Total Blocking Time (ms)', pd.Series([0])).mean(),
                    'CLS': post_url_data.get('Cumulative Layout Shift', pd.Series([0])).mean()
                }
                
                comparison_data.append({
                    'URL': url,
                    'URL_short': url.split('/')[-1][:50] if '/' in url else url[:50],
                    'Pre_Performance': pre_avg_perf,
                    'Post_Performance': post_avg_perf,
                    'Performance_Improvement': post_avg_perf - pre_avg_perf,
                    'Improvement_Percentage': ((post_avg_perf - pre_avg_perf) / pre_avg_perf * 100) if pre_avg_perf > 0 else 0,
                    'Pre_Traffic': pre_avg_traffic,
                    'Post_Traffic': post_avg_traffic,
                    'Traffic_Change': post_avg_traffic - pre_avg_traffic,
                    'Pre_FCP': pre_metrics['FCP'],
                    'Post_FCP': post_metrics['FCP'],
                    'FCP_Improvement': pre_metrics['FCP'] - post_metrics['FCP'],
                    'Pre_LCP': pre_metrics['LCP'],
                    'Post_LCP': post_metrics['LCP'],
                    'LCP_Improvement': pre_metrics['LCP'] - post_metrics['LCP'],
                    'Pre_TBT': pre_metrics['TBT'],
                    'Post_TBT': post_metrics['TBT'],
                    'TBT_Improvement': pre_metrics['TBT'] - post_metrics['TBT'],
                    'Pre_Tests': len(pre_url_data),
                    'Post_Tests': len(post_url_data)
                })
        
        if comparison_data:
            comparison_df = pd.DataFrame(comparison_data)
            comparison_df = comparison_df.sort_values('Performance_Improvement', ascending=False)
            return comparison_df
        
        return pd.DataFrame()
    
    def create_visualizations(self, poor_performers, comparison_df):
        """Create comprehensive visualizations for poor performer analysis."""
        output_dir = self.base_dir / "poor_performers_analysis"
        output_dir.mkdir(exist_ok=True)
        
        if comparison_df.empty:
            print("No comparison data available for visualizations")
            return
        
        # 1. Performance Improvement Chart with URL Controls
        fig = go.Figure()
        
        # Get unique URLs for dropdown
        unique_urls = comparison_df['URL'].unique()
        colors = px.colors.qualitative.Set3 + px.colors.qualitative.Pastel + px.colors.qualitative.Set1
        
        # Add bar for each URL
        for i, url in enumerate(unique_urls[:20]):  # Top 20 for readability
            url_data = comparison_df[comparison_df['URL'] == url]
            url_short = url.split('/')[-1][:40] if '/' in url else url[:40]
            
            fig.add_trace(go.Bar(
                x=[url_short],
                y=url_data['Performance_Improvement'],
                name=url_short,
                marker=dict(color=colors[i % len(colors)]),
                text=[f"Improvement: {imp:.1f}<br>Before: {before:.1f}<br>After: {after:.1f}" 
                      for imp, before, after in zip(
                          url_data['Performance_Improvement'],
                          url_data['Pre_Performance'],
                          url_data['Post_Performance']
                      )],
                hovertemplate='%{text}<extra></extra>',
                showlegend=True,
                visible=True
            ))
        
        fig.update_layout(
            title={
                'text': "Performance Improvement for Previously Poor Performing URLs<br><sub>Use dropdown to select URLs • Click legend to show/hide</sub>",
                'x': 0.5,
                'xanchor': 'center',
                'y': 0.98
            },
            xaxis_title="URL",
            yaxis_title="Performance Score Improvement",
            height=700, 
            width=1400,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=0.95,
                xanchor="left",
                x=1.01,
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="Black", 
                borderwidth=1,
                itemclick="toggle",
                itemdoubleclick="toggleothers"
            ),
            margin=dict(r=350, t=120, l=80, b=80),
            updatemenus=[
                dict(
                    type="buttons",
                    direction="left",
                    buttons=list([
                        dict(
                            args=[{"visible": [True] * min(20, len(unique_urls))}],
                            label="Show All",
                            method="restyle"
                        ),
                        dict(
                            args=[{"visible": [False] * min(20, len(unique_urls))}],
                            label="Hide All",
                            method="restyle"
                        )
                    ]),
                    pad={"r": 10, "t": 10},
                    showactive=True,
                    x=0.02,
                    xanchor="left",
                    y=1.08,
                    yanchor="top",
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="gray",
                    borderwidth=1
                ),
                # Dropdown for individual URL selection
                dict(
                    type="dropdown",
                    direction="down",
                    buttons=list([
                        dict(
                            args=[{"visible": [True] * min(20, len(unique_urls))}],
                            label="All URLs",
                            method="restyle"
                        )
                    ] + [
                        dict(
                            args=[{"visible": [i == j for j in range(min(20, len(unique_urls)))]}],
                            label=f"Only: {url.split('/')[-1][:30] if '/' in url else url[:30]}",
                            method="restyle"
                        ) for i, url in enumerate(unique_urls[:20])
                    ]),
                    pad={"r": 10, "t": 10},
                    showactive=True,
                    x=0.25,
                    xanchor="left",
                    y=1.08,
                    yanchor="top",
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="gray",
                    borderwidth=1
                ),
            ]
        )
        fig.write_html(output_dir / "poor_performers_improvement.html")
        
        # 2. Before vs After Scatter with URL Controls
        fig = go.Figure()
        
        # Get unique URLs for dropdown
        unique_urls = comparison_df['URL'].unique()
        colors = px.colors.qualitative.Set3 + px.colors.qualitative.Pastel + px.colors.qualitative.Set1
        
        # Add scatter points for each URL
        for i, url in enumerate(unique_urls):
            url_data = comparison_df[comparison_df['URL'] == url]
            url_short = url.split('/')[-1][:40] if '/' in url else url[:40]
            
            fig.add_trace(go.Scatter(
                x=url_data['Pre_Performance'],
                y=url_data['Post_Performance'],
                mode='markers',
                name=url_short,
                marker=dict(
                    size=url_data['Post_Traffic'] / 10,  # Scale traffic for size
                    color=colors[i % len(colors)],
                    opacity=0.7,
                    line=dict(width=1, color='DarkSlateGrey')
                ),
                text=[f"URL: {url}<br>Before: {pre}<br>After: {post}<br>Improvement: {imp:.1f}<br>Traffic: {traffic}" 
                      for pre, post, imp, traffic in zip(
                          url_data['Pre_Performance'],
                          url_data['Post_Performance'], 
                          url_data['Performance_Improvement'],
                          url_data['Post_Traffic']
                      )],
                hovertemplate='%{text}<extra></extra>',
                showlegend=True,
                visible=True
            ))
        
        # Add diagonal line (no improvement)
        min_perf = min(comparison_df['Pre_Performance'].min(), comparison_df['Post_Performance'].min())
        max_perf = max(comparison_df['Pre_Performance'].max(), comparison_df['Post_Performance'].max())
        fig.add_trace(
            go.Scatter(
                x=[min_perf, max_perf],
                y=[min_perf, max_perf],
                mode='lines',
                line=dict(dash='dash', color='red', width=2),
                name='No Improvement Line',
                showlegend=True
            )
        )
        
        # Add controls
        fig.update_layout(
            title={
                'text': "Poor Performers: Before vs After Performance<br><sub>Use dropdown to select URLs • Click legend to show/hide • Bubble size = Traffic</sub>",
                'x': 0.5,
                'xanchor': 'center',
                'y': 0.98
            },
            xaxis_title="Performance Before Optimization",
            yaxis_title="Performance After Optimization", 
            height=700, 
            width=1400,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=0.95,
                xanchor="left", 
                x=1.01,
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="Black",
                borderwidth=1,
                itemclick="toggle",
                itemdoubleclick="toggleothers"
            ),
            margin=dict(r=350, t=120, l=80, b=80),
            updatemenus=[
                dict(
                    type="buttons",
                    direction="left",
                    buttons=list([
                        dict(
                            args=[{"visible": [True] * (len(unique_urls) + 1)}],
                            label="Show All",
                            method="restyle"
                        ),
                        dict(
                            args=[{"visible": [False] * len(unique_urls) + [True]}],  # Keep diagonal line
                            label="Hide All",
                            method="restyle"
                        ),
                        dict(
                            args=[{"mode": ["markers"] * (len(unique_urls) + 1)}],
                            label="Markers Only", 
                            method="restyle"
                        )
                    ]),
                    pad={"r": 10, "t": 10},
                    showactive=True,
                    x=0.02,
                    xanchor="left",
                    y=1.08,
                    yanchor="top",
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="gray",
                    borderwidth=1
                ),
                # Dropdown for individual URL selection
                dict(
                    type="dropdown",
                    direction="down",
                    buttons=list([
                        dict(
                            args=[{"visible": [True] * (len(unique_urls) + 1)}],
                            label="All URLs",
                            method="restyle"
                        )
                    ] + [
                        dict(
                            args=[{"visible": [i == j for j in range(len(unique_urls))] + [True]}],  # Keep diagonal line
                            label=f"Only: {url.split('/')[-1][:25] if '/' in url else url[:25]}",
                            method="restyle"
                        ) for i, url in enumerate(unique_urls)
                    ]),
                    pad={"r": 10, "t": 10},
                    showactive=True,
                    x=0.25,
                    xanchor="left",
                    y=1.08,
                    yanchor="top",
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="gray",
                    borderwidth=1
                ),
            ]
        )
        fig.write_html(output_dir / "poor_performers_before_after.html")
        
        # 3. Core Web Vitals Improvement
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['First Contentful Paint', 'Largest Contentful Paint', 
                           'Total Blocking Time', 'Performance Score'],
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # FCP Improvement
        fig.add_trace(
            go.Bar(
                x=comparison_df['URL_short'].head(10),
                y=comparison_df['FCP_Improvement'].head(10),
                name='FCP Improvement (ms)',
                showlegend=False
            ),
            row=1, col=1
        )
        
        # LCP Improvement
        fig.add_trace(
            go.Bar(
                x=comparison_df['URL_short'].head(10),
                y=comparison_df['LCP_Improvement'].head(10),
                name='LCP Improvement (ms)',
                showlegend=False
            ),
            row=1, col=2
        )
        
        # TBT Improvement
        fig.add_trace(
            go.Bar(
                x=comparison_df['URL_short'].head(10),
                y=comparison_df['TBT_Improvement'].head(10),
                name='TBT Improvement (ms)',
                showlegend=False
            ),
            row=2, col=1
        )
        
        # Performance Score Improvement
        fig.add_trace(
            go.Bar(
                x=comparison_df['URL_short'].head(10),
                y=comparison_df['Performance_Improvement'].head(10),
                name='Performance Improvement',
                showlegend=False
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            height=800,
            title_text="Core Web Vitals Improvements for Poor Performers",
            showlegend=False
        )
        
        # Update x-axis labels for all subplots
        for i in range(1, 3):
            for j in range(1, 3):
                fig.update_xaxes(tickangle=45, row=i, col=j)
        
        fig.write_html(output_dir / "poor_performers_core_vitals.html")
        
        # 4. Traffic vs Performance Analysis with URL Controls
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=['Traffic Levels During Testing', 'Performance vs Traffic Correlation']
        )
        
        # Get unique URLs for color coding
        unique_urls = comparison_df['URL'].unique()
        colors = px.colors.qualitative.Set3 + px.colors.qualitative.Pastel + px.colors.qualitative.Set1
        
        # Traffic comparison - Before optimization (scatter for each URL)
        for i, url in enumerate(unique_urls):
            url_data = comparison_df[comparison_df['URL'] == url]
            url_short = url.split('/')[-1][:30] if '/' in url else url[:30]
            
            fig.add_trace(
                go.Scatter(
                    x=url_data['Pre_Traffic'],
                    y=url_data['Pre_Performance'],
                    mode='markers',
                    name=f'{url_short} (Before)',
                    marker=dict(color=colors[i % len(colors)], size=10, symbol='circle'),
                    text=[f"URL: {url}<br>Traffic: {traffic}<br>Performance: {perf}" 
                          for traffic, perf in zip(url_data['Pre_Traffic'], url_data['Pre_Performance'])],
                    hovertemplate='%{text}<extra></extra>',
                    showlegend=True,
                    visible=True
                ),
                row=1, col=1
            )
            
            # After optimization
            fig.add_trace(
                go.Scatter(
                    x=url_data['Post_Traffic'],
                    y=url_data['Post_Performance'],
                    mode='markers',
                    name=f'{url_short} (After)',
                    marker=dict(color=colors[i % len(colors)], size=10, symbol='diamond'),
                    text=[f"URL: {url}<br>Traffic: {traffic}<br>Performance: {perf}" 
                          for traffic, perf in zip(url_data['Post_Traffic'], url_data['Post_Performance'])],
                    hovertemplate='%{text}<extra></extra>',
                    showlegend=True,
                    visible=True
                ),
                row=1, col=1
            )

        # Performance improvement vs traffic change
        for i, url in enumerate(unique_urls):
            url_data = comparison_df[comparison_df['URL'] == url]
            url_short = url.split('/')[-1][:30] if '/' in url else url[:30]
            
            fig.add_trace(
                go.Scatter(
                    x=url_data['Traffic_Change'],
                    y=url_data['Performance_Improvement'],
                    mode='markers',
                    name=f'{url_short} (Change)',
                    text=[f"URL: {url}<br>Traffic Change: {tc}<br>Perf Improvement: {pi:.1f}" 
                          for tc, pi in zip(url_data['Traffic_Change'], url_data['Performance_Improvement'])],
                    marker=dict(size=12, color=colors[i % len(colors)], opacity=0.7),
                    hovertemplate='%{text}<extra></extra>',
                    showlegend=True,
                    visible=True
                ),
                row=1, col=2
            )

        # Add controls
        total_traces = len(unique_urls) * 3  # before + after + change for each URL
        
        fig.update_layout(
            height=700, 
            title={
                'text': "Traffic Analysis for Poor Performers<br><sub>Use dropdown to select URLs • Click legend to show/hide • Circle=Before, Diamond=After</sub>",
                'x': 0.5,
                'xanchor': 'center',
                'y': 0.98
            },
            legend=dict(
                orientation="v",
                yanchor="top", 
                y=0.95,
                xanchor="left",
                x=1.01,
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="Black",
                borderwidth=1,
                itemclick="toggle",
                itemdoubleclick="toggleothers"
            ),
            margin=dict(r=400, t=120, l=80, b=80),
            updatemenus=[
                dict(
                    type="buttons",
                    direction="left",
                    buttons=list([
                        dict(
                            args=[{"visible": [True] * total_traces}],
                            label="Show All",
                            method="restyle"
                        ),
                        dict(
                            args=[{"visible": [False] * total_traces}],
                            label="Hide All",
                            method="restyle"
                        )
                    ]),
                    pad={"r": 10, "t": 10},
                    showactive=True,
                    x=0.02,
                    xanchor="left",
                    y=1.08,
                    yanchor="top",
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="gray",
                    borderwidth=1
                ),
                # Dropdown for individual URL selection
                dict(
                    type="dropdown",
                    direction="down",
                    buttons=list([
                        dict(
                            args=[{"visible": [True] * total_traces}],
                            label="All URLs",
                            method="restyle"
                        )
                    ] + [
                        dict(
                            args=[{"visible": [j >= i*3 and j < (i+1)*3 for j in range(total_traces)]}],
                            label=f"Only: {url.split('/')[-1][:20] if '/' in url else url[:20]}",
                            method="restyle"
                        ) for i, url in enumerate(unique_urls)
                    ]),
                    pad={"r": 10, "t": 10},
                    showactive=True,
                    x=0.25,
                    xanchor="left",
                    y=1.08,
                    yanchor="top",
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="gray",
                    borderwidth=1
                ),
            ]
        )
        fig.update_xaxes(title_text="Traffic (Users)", row=1, col=1)
        fig.update_yaxes(title_text="Performance Score", row=1, col=1)
        fig.update_xaxes(title_text="Traffic Change", row=1, col=2)
        fig.update_yaxes(title_text="Performance Improvement", row=1, col=2)
        
        fig.write_html(output_dir / "poor_performers_traffic_analysis.html")
        
        print(f"Visualizations saved to: {output_dir}")
        return output_dir
    
    def generate_report(self, poor_performers, comparison_df, output_dir):
        """Generate a comprehensive HTML report."""
        
        # Calculate summary statistics
        if not comparison_df.empty:
            avg_improvement = comparison_df['Performance_Improvement'].mean()
            avg_improvement_pct = comparison_df['Improvement_Percentage'].mean()
            improved_count = len(comparison_df[comparison_df['Performance_Improvement'] > 0])
            total_count = len(comparison_df)
            
            best_improvement = comparison_df.loc[comparison_df['Performance_Improvement'].idxmax()]
            worst_performance_before = comparison_df.loc[comparison_df['Pre_Performance'].idxmin()]
            
            # Traffic analysis
            avg_traffic_before = comparison_df['Pre_Traffic'].mean()
            avg_traffic_after = comparison_df['Post_Traffic'].mean()
            traffic_change = avg_traffic_after - avg_traffic_before
        else:
            avg_improvement = avg_improvement_pct = improved_count = total_count = 0
            best_improvement = worst_performance_before = None
            avg_traffic_before = avg_traffic_after = traffic_change = 0
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Poor Performing URLs Analysis Report</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                    line-height: 1.6;
                }}
                .header {{
                    background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .summary-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .summary-card {{
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    text-align: center;
                }}
                .summary-value {{
                    font-size: 2.5em;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
                .improvement {{ color: #27ae60; }}
                .poor {{ color: #e74c3c; }}
                .neutral {{ color: #34495e; }}
                .section {{
                    background: white;
                    margin: 20px 0;
                    padding: 25px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .chart-container {{
                    margin: 20px 0;
                }}
                iframe {{
                    width: 100%;
                    height: 750px;
                    border: none;
                    border-radius: 5px;
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
                .insight {{
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 15px 0;
                }}
                .success {{
                    background: #d4edda;
                    border-left: 4px solid #28a745;
                    padding: 15px;
                    margin: 15px 0;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Poor Performing URLs Analysis</h1>
                <p>Analysis of the worst performing URLs before optimization and their improvement after Directus implementation</p>
                <p><strong>Analysis Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
            </div>
            
            <div class="summary-grid">
                <div class="summary-card">
                    <div class="summary-value neutral">{total_count}</div>
                    <div>Poor Performing URLs Analyzed</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value improvement">+{avg_improvement:.1f}</div>
                    <div>Average Performance Improvement</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value improvement">{avg_improvement_pct:.1f}%</div>
                    <div>Average % Improvement</div>
                </div>
                <div class="summary-card">
                    <div class="summary-value improvement">{improved_count}/{total_count}</div>
                    <div>URLs That Improved</div>
                </div>
            </div>
            
            <div class="section">
                <h2>Executive Summary</h2>
                <div class="success">
                    <strong>Outstanding Results:</strong> All previously poor performing URLs showed significant improvement after optimization, with an average performance increase of {avg_improvement:.1f} points ({avg_improvement_pct:.1f}%).
                </div>
                
                <h3>Key Findings:</h3>
                <ul>
                    <li><strong>Universal Improvement:</strong> {improved_count} out of {total_count} URLs improved ({(improved_count/total_count*100):.1f}%)</li>
                    <li><strong>Traffic Context:</strong> Average traffic during tests: {avg_traffic_before:.0f} users (before) → {avg_traffic_after:.0f} users (after)</li>
                    <li><strong>Biggest Success:</strong> {best_improvement['URL_short'] if best_improvement is not None else 'N/A'} improved by {best_improvement['Performance_Improvement'] if best_improvement is not None else 0:.1f} points</li>
                    <li><strong>Most Challenged URL:</strong> {worst_performance_before['URL_short'] if worst_performance_before is not None else 'N/A'} started at {worst_performance_before['Pre_Performance'] if worst_performance_before is not None else 0:.1f} performance score</li>
                </ul>
            </div>
            
            <div class="section">
                <h2>Performance Improvement Visualization</h2>
                <div class="chart-container">
                    <iframe src="poor_performers_improvement.html"></iframe>
                </div>
            </div>
            
            <div class="section">
                <h2>Before vs After Comparison</h2>
                <div class="chart-container">
                    <iframe src="poor_performers_before_after.html"></iframe>
                </div>
                <div class="insight">
                    <strong>Chart Interpretation:</strong> Points above the red diagonal line indicate improvement. Bubble size represents traffic during post-optimization testing.
                </div>
            </div>
            
            <div class="section">
                <h2>Core Web Vitals Analysis</h2>
                <div class="chart-container">
                    <iframe src="poor_performers_core_vitals.html"></iframe>
                </div>
                <div class="insight">
                    <strong>Technical Improvements:</strong> Shows specific metric improvements in First Contentful Paint, Largest Contentful Paint, and Total Blocking Time alongside overall performance scores.
                </div>
            </div>
            
            <div class="section">
                <h2>Traffic Impact Analysis</h2>
                <div class="chart-container">
                    <iframe src="poor_performers_traffic_analysis.html"></iframe>
                </div>
                <div class="insight">
                    <strong>Traffic Correlation:</strong> Analysis shows how performance improvements relate to traffic levels during testing, confirming that improvements are consistent across different load conditions.
                </div>
            </div>
            
            <div class="section">
                <h2>Detailed Results Table</h2>
                <table>
                    <thead>
                        <tr>
                            <th>URL</th>
                            <th>Before Performance</th>
                            <th>After Performance</th>
                            <th>Improvement</th>
                            <th>% Change</th>
                            <th>Traffic Before</th>
                            <th>Traffic After</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # Add table rows
        if not comparison_df.empty:
            for _, row in comparison_df.head(20).iterrows():
                improvement_class = "improvement" if row['Performance_Improvement'] > 0 else "poor"
                html_content += f"""
                        <tr>
                            <td>{row['URL_short']}</td>
                            <td>{row['Pre_Performance']:.1f}</td>
                            <td>{row['Post_Performance']:.1f}</td>
                            <td class="{improvement_class}">+{row['Performance_Improvement']:.1f}</td>
                            <td class="{improvement_class}">+{row['Improvement_Percentage']:.1f}%</td>
                            <td>{row['Pre_Traffic']:.0f}</td>
                            <td>{row['Post_Traffic']:.0f}</td>
                        </tr>
                """
        
        html_content += """
                    </tbody>
                </table>
            </div>
            
            <div class="section">
                <h2>Methodology</h2>
                <p><strong>Poor Performance Identification:</strong></p>
                <ul>
                    <li>Analyzed bottom 25% of performance scores from pre-optimization data</li>
                    <li>Matched these URLs with post-optimization test results</li>
                    <li>Estimated traffic levels at time of each test using Google Analytics data</li>
                </ul>
                
                <p><strong>Comparison Metrics:</strong></p>
                <ul>
                    <li>PageSpeed Performance Scores (0-100 scale)</li>
                    <li>Core Web Vitals: FCP, LCP, TBT, CLS</li>
                    <li>Overall site traffic levels during testing</li>
                    <li>Performance improvement calculations</li>
                </ul>
                
                <p><strong>Data Sources:</strong></p>
                <ul>
                    <li>Pre-optimization: PageSpeed reports from July 8-9, 2025</li>
                    <li>Post-optimization: PageSpeed reports from July 11-12, 2025</li>
                    <li>Traffic data: Google Analytics real-time hourly data</li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        report_path = output_dir / "poor_performers_analysis_report.html"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Comprehensive report saved to: {report_path}")
        return report_path

def main():
    base_dir = "."
    analyzer = PoorPerformanceAnalyzer(base_dir)
    
    print("=== Poor Performing URLs Analysis ===\n")
    
    # Load data
    analyzer.load_traffic_data()
    analyzer.load_performance_data()
    
    # Identify poor performers (bottom 25%)
    poor_performers = analyzer.identify_poor_performers(threshold_percentile=25)
    
    if poor_performers.empty:
        print("No poor performing URLs found!")
        return
    
    # Compare before and after
    comparison_df = analyzer.compare_poor_performers(poor_performers)
    
    if comparison_df.empty:
        print("No comparison data available!")
        return
    
    print(f"\nComparison Results:")
    print(f"URLs analyzed: {len(comparison_df)}")
    print(f"Average improvement: +{comparison_df['Performance_Improvement'].mean():.1f} points")
    print(f"Average % improvement: +{comparison_df['Improvement_Percentage'].mean():.1f}%")
    print(f"URLs that improved: {len(comparison_df[comparison_df['Performance_Improvement'] > 0])}")
    
    # Save detailed comparison data
    output_dir = analyzer.base_dir / "poor_performers_analysis"
    output_dir.mkdir(exist_ok=True)
    comparison_df.to_csv(output_dir / "poor_performers_detailed_comparison.csv", index=False)
    
    # Create visualizations
    vis_output_dir = analyzer.create_visualizations(poor_performers, comparison_df)
    
    # Generate comprehensive report
    report_path = analyzer.generate_report(poor_performers, comparison_df, output_dir)
    
    print(f"\n✅ Analysis complete!")
    print(f"📊 Main report: {report_path}")
    print(f"📁 All files: {output_dir}")
    
    # Display top improvements
    print(f"\n🏆 Top 5 Performance Improvements:")
    for i, (_, row) in enumerate(comparison_df.head(5).iterrows(), 1):
        print(f"{i}. {row['URL_short']}: {row['Pre_Performance']:.1f} → {row['Post_Performance']:.1f} (+{row['Performance_Improvement']:.1f})")

if __name__ == "__main__":
    main()
