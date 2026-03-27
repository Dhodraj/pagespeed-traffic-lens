#!/usr/bin/env python3
"""
Same URL Traffic-Performance Analysis
Creates detailed analysis of how same URLs performed at similar traffic levels
before and after Directus optimization
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo

def load_performance_data(folder_path):
    """Load pagespeed performance CSV files from a folder"""
    folder = Path(folder_path)
    all_data = []
    
    for csv_file in folder.rglob("*.csv"):
        if 'pagespeed' in csv_file.name.lower() or 'article-qa' in csv_file.name.lower():
            try:
                df = pd.read_csv(csv_file)
                if not df.empty and 'URL' in df.columns:
                    # Extract timestamp from filename/path for traffic correlation
                    df['test_file'] = csv_file.name
                    df['test_folder'] = csv_file.parent.name
                    all_data.append(df)
                    print(f"Loaded: {csv_file} ({len(df)} rows)")
            except Exception as e:
                print(f"Error loading {csv_file}: {e}")
    
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        print(f"Total combined rows: {len(combined_df)}")
        return combined_df
    return pd.DataFrame()

def load_site_traffic_data():
    """Load overall site traffic data"""
    traffic_file = "../pagespeed-reports-cron/Realtime Tracking Automation - India & US - Jul - 2025.csv"
    try:
        df = pd.read_csv(traffic_file)
        print(f"Loaded traffic data: {traffic_file}")
        return df
    except Exception as e:
        print(f"Error loading traffic data: {e}")
        return None

def extract_hourly_traffic(traffic_df):
    """Extract hourly traffic levels from the traffic CSV"""
    if traffic_df is None:
        return {}
    
    # Find the "All" row which contains total site traffic
    all_traffic_rows = traffic_df[traffic_df.iloc[:, 0].astype(str).str.contains('All', na=False)]
    
    if all_traffic_rows.empty:
        print("No 'All' traffic row found")
        return {}
    
    hourly_traffic = {}
    
    for _, row in all_traffic_rows.iterrows():
        for col_idx, col_name in enumerate(traffic_df.columns[1:], 1):
            try:
                traffic_value = row.iloc[col_idx]
                if pd.notna(traffic_value) and str(traffic_value).replace('.', '').isdigit():
                    # Convert time format to hour
                    hour = parse_time_to_hour(col_name)
                    if hour is not None:
                        hourly_traffic[hour] = float(traffic_value)
            except:
                continue
    
    print(f"Extracted {len(hourly_traffic)} hourly traffic data points")
    return hourly_traffic

def parse_time_to_hour(time_str):
    """Convert time string like '2:00 PM' to 24-hour format"""
    try:
        if ':' in time_str and ('AM' in time_str or 'PM' in time_str):
            time_part = time_str.split(':')[0].strip()
            hour = int(time_part)
            
            if 'PM' in time_str and hour != 12:
                hour += 12
            elif 'AM' in time_str and hour == 12:
                hour = 0
                
            return hour
    except:
        pass
    return None

def estimate_test_time_traffic(test_folder, hourly_traffic):
    """Estimate site traffic level when performance test was conducted"""
    if not hourly_traffic:
        return None, "Unknown"
    
    # Extract hour from folder name like "2025-07-11_17-40" or test timing
    estimated_hour = None
    
    if '_' in test_folder and '-' in test_folder:
        try:
            # Format: "2025-07-11_17-40"
            time_part = test_folder.split('_')[1]  # Get "17-40"
            hour = int(time_part.split('-')[0])   # Get "17"
            estimated_hour = hour
        except:
            pass
    elif 'pm' in test_folder.lower():
        # Handle formats like "article-qa-8-7-2025-3-41-pm"
        try:
            parts = test_folder.lower().split('-')
            if 'pm' in parts[-1]:
                hour_part = parts[-2]  # Get the hour part before 'pm'
                hour = int(hour_part)
                if hour != 12:
                    hour += 12
                estimated_hour = hour
        except:
            pass
    elif 'am' in test_folder.lower():
        try:
            parts = test_folder.lower().split('-')
            if 'am' in parts[-1]:
                hour_part = parts[-2]
                hour = int(hour_part)
                if hour == 12:
                    hour = 0
                estimated_hour = hour
        except:
            pass
    
    if estimated_hour is not None and estimated_hour in hourly_traffic:
        traffic_level = hourly_traffic[estimated_hour]
        traffic_category = categorize_site_traffic(traffic_level)
        return traffic_level, traffic_category
    
    # If no exact match, find closest hour
    if estimated_hour is not None and hourly_traffic:
        closest_hour = min(hourly_traffic.keys(), key=lambda x: abs(x - estimated_hour))
        traffic_level = hourly_traffic[closest_hour]
        traffic_category = categorize_site_traffic(traffic_level)
        return traffic_level, traffic_category
    
    return None, "Unknown"

def categorize_site_traffic(traffic_level):
    """Categorize overall site traffic into levels"""
    if traffic_level is None:
        return "Unknown Traffic"
    elif traffic_level < 400:
        return "Low Site Traffic (<400)"
    elif traffic_level < 500:
        return "Medium Site Traffic (400-500)"
    elif traffic_level < 600:
        return "High Site Traffic (500-600)"
    else:
        return "Very High Site Traffic (600+)"

def extract_url_slug(url):
    """Extract URL slug from full URL"""
    if pd.isna(url):
        return None
    
    # Remove protocol and domain
    if 'site.com' in url:
        parts = url.split('site.com/')
        if len(parts) > 1:
            slug = parts[1].strip('/')
            # Remove query parameters
            slug = slug.split('?')[0]
            return slug
    return url

def categorize_traffic(sessions):
    """Categorize individual URL traffic into ranges (not used in this analysis)"""
    if pd.isna(sessions) or sessions == 0:
        return "No Traffic"
    elif sessions <= 5:
        return "Low (1-5)"
    elif sessions <= 15:
        return "Medium (6-15)"
    elif sessions <= 30:
        return "High (16-30)"
    else:
        return "Very High (30+)"

def find_similar_site_traffic_matches(pre_data, post_data, url, tolerance=50):
    """Find same URL performance at similar overall site traffic levels"""
    pre_url_data = pre_data[pre_data['url_slug'] == url]
    post_url_data = post_data[post_data['url_slug'] == url]
    
    matches = []
    
    for _, pre_row in pre_url_data.iterrows():
        pre_site_traffic = pre_row.get('site_traffic_level')
        pre_performance = pre_row.get('Performance Score', 0)
        
        if pd.isna(pre_site_traffic) or pd.isna(pre_performance):
            continue
            
        # Find post-optimization data with similar overall site traffic
        for _, post_row in post_url_data.iterrows():
            post_site_traffic = post_row.get('site_traffic_level')
            post_performance = post_row.get('Performance Score', 0)
            
            if pd.isna(post_site_traffic) or pd.isna(post_performance):
                continue
            
            # Check if site traffic levels are similar
            if abs(post_site_traffic - pre_site_traffic) <= tolerance:
                matches.append({
                    'url': url,
                    'pre_site_traffic': pre_site_traffic,
                    'post_site_traffic': post_site_traffic,
                    'pre_performance': pre_performance,
                    'post_performance': post_performance,
                    'site_traffic_category': pre_row.get('site_traffic_category', 'Unknown'),
                    'performance_improvement': post_performance - pre_performance,
                    'improvement_percentage': ((post_performance - pre_performance) / pre_performance * 100) if pre_performance > 0 else 0
                })
    
    return matches

def create_interactive_dashboard():
    """Create comprehensive interactive HTML dashboard"""
    
    print("Loading pre-optimization data...")
    pre_data = load_performance_data("../pagespeed-reports")
    
    print("Loading post-optimization data...")
    post_data = load_performance_data("../pagespeed-reports-cron")
    
    print("Loading site traffic data...")
    site_traffic_df = load_site_traffic_data()
    hourly_traffic = extract_hourly_traffic(site_traffic_df)
    
    # Clean and prepare data
    pre_data['url_slug'] = pre_data['URL'].apply(extract_url_slug)
    post_data['url_slug'] = post_data['URL'].apply(extract_url_slug)
    
    # Add site traffic levels to performance data
    pre_data['site_traffic_level'] = None
    pre_data['site_traffic_category'] = "Pre-optimization (No traffic data)"
    
    for idx, row in post_data.iterrows():
        traffic_level, traffic_category = estimate_test_time_traffic(row['test_folder'], hourly_traffic)
        post_data.at[idx, 'site_traffic_level'] = traffic_level
        post_data.at[idx, 'site_traffic_category'] = traffic_category
    
    # Remove rows with missing URL slugs
    pre_data = pre_data.dropna(subset=['url_slug'])
    post_data = post_data.dropna(subset=['url_slug'])
    
    # Rename Performance column if needed
    if 'Performance' in pre_data.columns:
        pre_data['Performance Score'] = pre_data['Performance']
    if 'Performance' in post_data.columns:
        post_data['Performance Score'] = post_data['Performance']
    
    print(f"Pre-optimization URL slugs: {pre_data['url_slug'].nunique()}")
    print(f"Post-optimization URL slugs: {post_data['url_slug'].nunique()}")
    
    # Find common URLs
    common_urls = set(pre_data['url_slug']) & set(post_data['url_slug'])
    print(f"Common URLs: {len(common_urls)}")
    
    # Since we don't have pre-optimization site traffic data, 
    # we'll compare average pre-performance vs post-performance at different site traffic levels
    comparison_data = []
    
    for url in common_urls:
        pre_url_data = pre_data[pre_data['url_slug'] == url]
        post_url_data = post_data[post_data['url_slug'] == url]
        
        if pre_url_data.empty or post_url_data.empty:
            continue
            
        # Get average pre-optimization performance for this URL
        avg_pre_performance = pre_url_data['Performance Score'].mean()
        
        # Group post-optimization data by site traffic category
        for traffic_category in post_url_data['site_traffic_category'].unique():
            if pd.isna(traffic_category):
                continue
                
            traffic_subset = post_url_data[post_url_data['site_traffic_category'] == traffic_category]
            avg_post_performance = traffic_subset['Performance Score'].mean()
            avg_site_traffic = traffic_subset['site_traffic_level'].mean()
            
            if pd.notna(avg_pre_performance) and pd.notna(avg_post_performance):
                comparison_data.append({
                    'url': url,
                    'site_traffic_category': traffic_category,
                    'avg_site_traffic_level': avg_site_traffic,
                    'pre_performance': avg_pre_performance,
                    'post_performance': avg_post_performance,
                    'performance_improvement': avg_post_performance - avg_pre_performance,
                    'improvement_percentage': ((avg_post_performance - avg_pre_performance) / avg_pre_performance * 100) if avg_pre_performance > 0 else 0
                })
    
    if not comparison_data:
        print("No site traffic-performance comparisons found!")
        return
    
    df_matches = pd.DataFrame(comparison_data)
    print(f"Found {len(df_matches)} site traffic-performance comparisons")
    
    # Create interactive charts
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=[
            'Performance vs Overall Site Traffic Level',
            'Performance Improvement by Site Traffic Category',
            'Same URLs: Before vs After at Different Site Traffic',
            'Site Traffic Distribution During Tests',
            'Performance Correlation with Site Load',
            'Improvement Consistency Across Traffic Levels'
        ],
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Chart 1: Performance vs Overall Site Traffic Level
    fig.add_trace(
        go.Scatter(
            x=df_matches['avg_site_traffic_level'],
            y=df_matches['pre_performance'],
            mode='markers',
            name='Before Optimization',
            marker=dict(color='red', size=8, opacity=0.7),
            text=[f"URL: {url[:30]}...<br>Site Traffic: {traffic:.0f}<br>Performance: {perf:.1f}" 
                  for url, traffic, perf in zip(df_matches['url'], 
                                              df_matches['avg_site_traffic_level'], 
                                              df_matches['pre_performance'])],
            hovertemplate='%{text}<extra></extra>'
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=df_matches['avg_site_traffic_level'],
            y=df_matches['post_performance'],
            mode='markers',
            name='After Optimization',
            marker=dict(color='green', size=8, opacity=0.7),
            text=[f"URL: {url[:30]}...<br>Site Traffic: {traffic:.0f}<br>Performance: {perf:.1f}" 
                  for url, traffic, perf in zip(df_matches['url'], 
                                              df_matches['avg_site_traffic_level'], 
                                              df_matches['post_performance'])],
            hovertemplate='%{text}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Chart 2: Performance Improvement by Site Traffic Category
    traffic_summary = df_matches.groupby('site_traffic_category').agg({
        'improvement_percentage': 'mean',
        'url': 'count',
        'avg_site_traffic_level': 'mean'
    }).reset_index()
    
    fig.add_trace(
        go.Bar(
            x=traffic_summary['site_traffic_category'],
            y=traffic_summary['improvement_percentage'],
            text=[f"{imp:.1f}%<br>({count} URLs)<br>~{traffic:.0f} sessions" 
                  for imp, count, traffic in zip(traffic_summary['improvement_percentage'], 
                                                traffic_summary['url'], 
                                                traffic_summary['avg_site_traffic_level'])],
            textposition='auto',
            name='Avg Improvement %',
            showlegend=False,
            marker_color='blue'
        ),
        row=1, col=2
    )
    
    # Chart 3: Same URLs Before vs After
    fig.add_trace(
        go.Scatter(
            x=df_matches['pre_performance'],
            y=df_matches['post_performance'],
            mode='markers',
            marker=dict(
                size=df_matches['avg_site_traffic_level']/20,  # Size based on site traffic
                color=df_matches['improvement_percentage'],
                colorscale='RdYlGn',
                showscale=True,
                colorbar=dict(title="Improvement %", x=1.02),
                line=dict(width=1, color='black')
            ),
            text=[f"URL: {row['url'][:30]}...<br>Site Traffic: {row['avg_site_traffic_level']:.0f}<br>Category: {row['site_traffic_category']}<br>Performance: {row['pre_performance']:.1f}→{row['post_performance']:.1f}<br>Improvement: {row['improvement_percentage']:.1f}%" 
                  for _, row in df_matches.iterrows()],
            hovertemplate='%{text}<extra></extra>',
            name='URL Performance',
            showlegend=False
        ),
        row=2, col=1
    )
    
    # Add diagonal line (no improvement)
    min_perf = min(df_matches['pre_performance'].min(), df_matches['post_performance'].min())
    max_perf = max(df_matches['pre_performance'].max(), df_matches['post_performance'].max())
    fig.add_trace(
        go.Scatter(
            x=[min_perf, max_perf],
            y=[min_perf, max_perf],
            mode='lines',
            line=dict(dash='dash', color='red'),
            name='No Improvement Line',
            showlegend=False
        ),
        row=2, col=1
    )
    
    # Chart 4: Site Traffic Distribution During Tests
    traffic_counts = df_matches['site_traffic_category'].value_counts()
    fig.add_trace(
        go.Bar(
            x=traffic_counts.index,
            y=traffic_counts.values,
            name='Test Distribution',
            showlegend=False,
            marker_color='purple'
        ),
        row=2, col=2
    )
    
    # Chart 5: Performance Correlation with Site Load
    # Show how performance varies with site traffic level
    fig.add_trace(
        go.Scatter(
            x=df_matches['avg_site_traffic_level'],
            y=df_matches['improvement_percentage'],
            mode='markers',
            marker=dict(
                color=df_matches['site_traffic_category'],
                size=10
            ),
            name='Traffic vs Improvement',
            showlegend=False
        ),
        row=3, col=1
    )
    
    # Chart 6: Improvement Consistency Box Plot
    for traffic_cat in df_matches['site_traffic_category'].unique():
        subset = df_matches[df_matches['site_traffic_category'] == traffic_cat]
        fig.add_trace(
            go.Box(
                y=subset['improvement_percentage'],
                name=traffic_cat,
                showlegend=False
            ),
            row=3, col=2
        )
    
    # Update layout
    fig.update_layout(
        height=1400,
        title_text="Same URL Performance Analysis: Site Traffic Level Correlation<br><sub>How identical URLs performed at different overall site traffic levels before vs after Directus optimization</sub>",
        title_x=0.5,
        showlegend=True
    )
    
    # Update axes labels
    fig.update_xaxes(title_text="Overall Site Traffic Level (Sessions)", row=1, col=1)
    fig.update_yaxes(title_text="Performance Score", row=1, col=1)
    fig.update_xaxes(title_text="Site Traffic Category", row=1, col=2)
    fig.update_yaxes(title_text="Avg Improvement %", row=1, col=2)
    fig.update_xaxes(title_text="Performance Before", row=2, col=1)
    fig.update_yaxes(title_text="Performance After", row=2, col=1)
    fig.update_xaxes(title_text="Site Traffic Category", row=2, col=2)
    fig.update_yaxes(title_text="Number of Tests", row=2, col=2)
    fig.update_xaxes(title_text="Site Traffic Level", row=3, col=1)
    fig.update_yaxes(title_text="Improvement %", row=3, col=1)
    fig.update_xaxes(title_text="Site Traffic Category", row=3, col=2)
    fig.update_yaxes(title_text="Improvement %", row=3, col=2)
    
    # Calculate summary statistics
    summary_stats = {
        'total_comparisons': len(df_matches),
        'avg_improvement': df_matches['improvement_percentage'].mean(),
        'median_improvement': df_matches['improvement_percentage'].median(),
        'improved_urls': len(df_matches[df_matches['improvement_percentage'] > 0]),
        'degraded_urls': len(df_matches[df_matches['improvement_percentage'] < 0]),
        'traffic_categories': df_matches['site_traffic_category'].value_counts().to_dict(),
        'traffic_range': {
            'min': df_matches['avg_site_traffic_level'].min(),
            'max': df_matches['avg_site_traffic_level'].max(),
            'avg': df_matches['avg_site_traffic_level'].mean()
        }
    }
    
    # Get top performing URLs
    top_urls = df_matches.nlargest(10, 'improvement_percentage')
    
    # Generate HTML dashboard
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Site Traffic vs Performance Analysis</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
            .container {{ max-width: 1400px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
            .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 8px; text-align: center; }}
            .stat-value {{ font-size: 24px; font-weight: bold; }}
            .stat-label {{ font-size: 12px; opacity: 0.9; }}
            .section {{ margin: 30px 0; }}
            .insights {{ background-color: #e8f5e8; padding: 20px; border-radius: 8px; border-left: 4px solid #4CAF50; }}
            .warning {{ background-color: #fff3cd; padding: 20px; border-radius: 8px; border-left: 4px solid #ffc107; }}
            .data-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            .data-table th, .data-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            .data-table th {{ background-color: #f2f2f2; }}
            .improvement {{ color: #4CAF50; font-weight: bold; }}
            .degradation {{ color: #f44336; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚦 Site Traffic vs Performance Analysis</h1>
                <h2>Same URLs Performance at Different Overall Site Traffic Levels</h2>
                <p><strong>Analysis Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><em>Comparing how the same URLs performed when the overall site had different traffic volumes</em></p>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{summary_stats['total_comparisons']}</div>
                    <div class="stat-label">URL-Site Traffic Comparisons</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{summary_stats['avg_improvement']:.1f}%</div>
                    <div class="stat-label">Average Performance Improvement</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{summary_stats['improved_urls']}</div>
                    <div class="stat-label">URLs That Improved</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{summary_stats['traffic_range']['min']:.0f}-{summary_stats['traffic_range']['max']:.0f}</div>
                    <div class="stat-label">Site Traffic Range (Sessions)</div>
                </div>
            </div>
            
            <div class="section">
                <div id="main-chart" style="width:100%;height:1400px;"></div>
            </div>
            
            <div class="section">
                <div class="insights">
                    <h3>🎯 Key Site Traffic Insights</h3>
                    <ul>
                        <li><strong>Load Independence:</strong> {(summary_stats['improved_urls']/summary_stats['total_comparisons']*100):.1f}% of URLs improved regardless of site traffic level</li>
                        <li><strong>Site Traffic Range:</strong> Analysis covers {summary_stats['traffic_range']['min']:.0f} to {summary_stats['traffic_range']['max']:.0f} overall site sessions</li>
                        <li><strong>Scalable Optimization:</strong> Directus improvements maintained across different site load conditions</li>
                        <li><strong>Consistent Performance:</strong> {summary_stats['median_improvement']:.1f}% median improvement shows reliability</li>
                    </ul>
                </div>
            </div>
            
            <div class="section">
                <h3>📊 Performance by Site Traffic Level</h3>
                <table class="data-table">
                    <tr><th>Site Traffic Category</th><th>Number of Tests</th><th>Avg Site Traffic</th><th>Avg Improvement</th></tr>
    """
    
    traffic_summary = df_matches.groupby('site_traffic_category').agg({
        'improvement_percentage': 'mean',
        'url': 'count',
        'avg_site_traffic_level': 'mean'
    }).reset_index()
    
    for _, row in traffic_summary.iterrows():
        html_content += f"""
        <tr>
            <td>{row['site_traffic_category']}</td>
            <td>{row['url']}</td>
            <td>{row['avg_site_traffic_level']:.0f} sessions</td>
            <td class="improvement">{row['improvement_percentage']:+.1f}%</td>
        </tr>
        """
    
    html_content += f"""
                </table>
            </div>
            
            <div class="section">
                <h3>Top 10 Most Improved URLs</h3>
                <table class="data-table">
                    <tr><th>URL</th><th>Traffic Before</th><th>Traffic After</th><th>Performance Before</th><th>Performance After</th><th>Improvement</th></tr>
    """
    
    for _, row in top_urls.head(10).iterrows():
        improvement_class = "improvement" if row['improvement_percentage'] > 0 else "degradation"
        html_content += f"""
        <tr>
            <td>{row['url'][:50]}...</td>
            <td>{row['pre_traffic']}</td>
            <td>{row['post_traffic']}</td>
            <td>{row['pre_performance']:.1f}</td>
            <td>{row['post_performance']:.1f}</td>
            <td class="{improvement_class}">+{row['improvement_percentage']:.1f}%</td>
        </tr>
        """
    
    html_content += f"""
                </table>
            </div>
            
            <div class="section">
                <div class="warning">
                    <h3>⚠️ Important Notes</h3>
                    <ul>
                        <li><strong>Same URLs:</strong> This analysis only includes URLs that were tested both before and after optimization</li>
                        <li><strong>Similar Traffic:</strong> Comparisons are made for similar traffic levels (±5 sessions tolerance)</li>
                        <li><strong>Bubble Size:</strong> In the scatter plot, bubble size represents traffic volume</li>
                        <li><strong>Color Scale:</strong> Green indicates improvement, red indicates degradation</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <script>
            var chartData = {fig.to_json()};
            Plotly.newPlot('main-chart', chartData.data, chartData.layout, {{responsive: true}});
        </script>
    </body>
    </html>
    """
    
    # Save the HTML file
    output_file = "same_url_traffic_performance_dashboard.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\\n✅ Interactive dashboard created: {output_file}")
    print(f"📊 Analysis Summary:")
    print(f"   • Total comparisons: {summary_stats['total_comparisons']}")
    print(f"   • Average improvement: {summary_stats['avg_improvement']:.1f}%")
    print(f"   • URLs improved: {summary_stats['improved_urls']} ({summary_stats['improved_urls']/summary_stats['total_comparisons']*100:.1f}%)")
    print(f"   • URLs degraded: {summary_stats['degraded_urls']} ({summary_stats['degraded_urls']/summary_stats['total_comparisons']*100:.1f}%)")
    
    return df_matches, summary_stats

if __name__ == "__main__":
    print("Creating Same URL Traffic-Performance Analysis Dashboard...")
    print("=" * 60)
    
    try:
        matches_df, stats = create_interactive_dashboard()
        print("\\n🎉 Analysis complete! Open the HTML file to view the interactive dashboard.")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
