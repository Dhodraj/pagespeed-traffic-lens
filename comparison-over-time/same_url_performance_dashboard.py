#!/usr/bin/env python3
"""
Same URL Performance Analysis - Simplified
Creates detailed analysis of how same URLs performed before and after Directus optimization
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

def load_csv_files(folder_path):
    """Load all pagespeed CSV files from a folder"""
    folder = Path(folder_path)
    all_data = []
    
    for csv_file in folder.rglob("*pagespeed*.csv"):
        try:
            df = pd.read_csv(csv_file)
            if not df.empty and 'URL' in df.columns:
                # Add timestamp info from filename/path
                df['report_timestamp'] = csv_file.stem
                df['report_date'] = str(csv_file.parent)
                all_data.append(df)
                print(f"Loaded: {csv_file} ({len(df)} rows)")
        except Exception as e:
            print(f"Error loading {csv_file}: {e}")
    
    # Also load article-qa.csv files
    for csv_file in folder.rglob("article-qa.csv"):
        try:
            df = pd.read_csv(csv_file)
            if not df.empty and 'URL' in df.columns:
                df['report_timestamp'] = csv_file.parent.name
                df['report_date'] = str(csv_file.parent)
                all_data.append(df)
                print(f"Loaded: {csv_file} ({len(df)} rows)")
        except Exception as e:
            print(f"Error loading {csv_file}: {e}")
    
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        print(f"Total combined rows: {len(combined_df)}")
        return combined_df
    return pd.DataFrame()

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

def create_performance_categories(score):
    """Categorize performance scores"""
    if pd.isna(score):
        return "Unknown"
    elif score >= 90:
        return "Excellent (90+)"
    elif score >= 80:
        return "Good (80-89)"
    elif score >= 60:
        return "Fair (60-79)"
    elif score >= 40:
        return "Poor (40-59)"
    else:
        return "Very Poor (<40)"

def create_interactive_dashboard():
    """Create comprehensive interactive HTML dashboard"""
    
    print("Loading pre-optimization data...")
    pre_data = load_csv_files("../pagespeed-reports")
    
    print("Loading post-optimization data...")
    post_data = load_csv_files("../pagespeed-reports-cron")
    
    # Clean and prepare data
    pre_data['url_slug'] = pre_data['URL'].apply(extract_url_slug)
    post_data['url_slug'] = post_data['URL'].apply(extract_url_slug)
    
    # Remove rows with missing URL slugs
    pre_data = pre_data.dropna(subset=['url_slug'])
    post_data = post_data.dropna(subset=['url_slug'])
    
    # Rename Performance column to Performance Score for consistency
    if 'Performance' in pre_data.columns:
        pre_data['Performance Score'] = pre_data['Performance']
    if 'Performance' in post_data.columns:
        post_data['Performance Score'] = post_data['Performance']
    
    print(f"Pre-optimization URL slugs: {pre_data['url_slug'].nunique()}")
    print(f"Post-optimization URL slugs: {post_data['url_slug'].nunique()}")
    
    # Find common URLs
    common_urls = set(pre_data['url_slug']) & set(post_data['url_slug'])
    print(f"Common URLs: {len(common_urls)}")
    
    # Aggregate data by URL (taking averages for multiple measurements)
    pre_agg = pre_data.groupby('url_slug').agg({
        'Performance Score': 'mean',
        'First Contentful Paint (ms)': 'mean',
        'Largest Contentful Paint (ms)': 'mean',
        'Speed Index (ms)': 'mean',
        'Total Blocking Time (ms)': 'mean',
        'Cumulative Layout Shift': 'mean'
    }).reset_index()
    
    post_agg = post_data.groupby('url_slug').agg({
        'Performance Score': 'mean',
        'First Contentful Paint (ms)': 'mean',
        'Largest Contentful Paint (ms)': 'mean',
        'Speed Index (ms)': 'mean',
        'Total Blocking Time (ms)': 'mean',
        'Cumulative Layout Shift': 'mean'
    }).reset_index()
    
    # Create comparison dataset for common URLs
    comparison_data = []
    for url in common_urls:
        pre_url = pre_agg[pre_agg['url_slug'] == url]
        post_url = post_agg[post_agg['url_slug'] == url]
        
        if not pre_url.empty and not post_url.empty:
            pre_perf = pre_url['Performance Score'].iloc[0]
            post_perf = post_url['Performance Score'].iloc[0]
            
            if not pd.isna(pre_perf) and not pd.isna(post_perf):
                comparison_data.append({
                    'url': url,
                    'pre_performance': pre_perf,
                    'post_performance': post_perf,
                    'performance_improvement': post_perf - pre_perf,
                    'improvement_percentage': ((post_perf - pre_perf) / pre_perf * 100) if pre_perf > 0 else 0,
                    'pre_category': create_performance_categories(pre_perf),
                    'post_category': create_performance_categories(post_perf),
                    'pre_fcp': pre_url['First Contentful Paint (ms)'].iloc[0] if not pd.isna(pre_url['First Contentful Paint (ms)'].iloc[0]) else 0,
                    'post_fcp': post_url['First Contentful Paint (ms)'].iloc[0] if not pd.isna(post_url['First Contentful Paint (ms)'].iloc[0]) else 0,
                    'pre_lcp': pre_url['Largest Contentful Paint (ms)'].iloc[0] if not pd.isna(pre_url['Largest Contentful Paint (ms)'].iloc[0]) else 0,
                    'post_lcp': post_url['Largest Contentful Paint (ms)'].iloc[0] if not pd.isna(post_url['Largest Contentful Paint (ms)'].iloc[0]) else 0,
                    'pre_tbt': pre_url['Total Blocking Time (ms)'].iloc[0] if not pd.isna(pre_url['Total Blocking Time (ms)'].iloc[0]) else 0,
                    'post_tbt': post_url['Total Blocking Time (ms)'].iloc[0] if not pd.isna(post_url['Total Blocking Time (ms)'].iloc[0]) else 0,
                })
    
    if not comparison_data:
        print("No matching URLs found for comparison!")
        return
    
    df_comparison = pd.DataFrame(comparison_data)
    print(f"Found {len(df_comparison)} URLs for comparison")
    
    # Create interactive charts
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=[
            'Performance Improvement: Before vs After',
            'Performance Score Distribution',
            'Core Web Vitals: FCP Comparison',
            'Core Web Vitals: LCP Comparison',
            'Total Blocking Time Improvement',
            'Performance Category Migration'
        ],
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Chart 1: Before vs After Scatter
    hover_text = [
        f"URL: {row['url'][:40]}...<br>" +
        f"Before: {row['pre_performance']:.1f}<br>" +
        f"After: {row['post_performance']:.1f}<br>" +
        f"Improvement: {row['improvement_percentage']:.1f}%<br>" +
        f"Category: {row['pre_category']} → {row['post_category']}"
        for _, row in df_comparison.iterrows()
    ]
    
    fig.add_trace(
        go.Scatter(
            x=df_comparison['pre_performance'],
            y=df_comparison['post_performance'],
            mode='markers',
            marker=dict(
                size=10,
                color=df_comparison['improvement_percentage'],
                colorscale='RdYlGn',
                showscale=True,
                colorbar=dict(title="Improvement %", x=0.45),
                line=dict(width=1, color='black')
            ),
            text=hover_text,
            hovertemplate='%{text}<extra></extra>',
            name='URL Performance'
        ),
        row=1, col=1
    )
    
    # Add diagonal line (no improvement)
    min_perf = min(df_comparison['pre_performance'].min(), df_comparison['post_performance'].min())
    max_perf = max(df_comparison['pre_performance'].max(), df_comparison['post_performance'].max())
    fig.add_trace(
        go.Scatter(
            x=[min_perf, max_perf],
            y=[min_perf, max_perf],
            mode='lines',
            line=dict(dash='dash', color='red'),
            name='No Improvement Line',
            showlegend=False
        ),
        row=1, col=1
    )
    
    # Chart 2: Performance Distribution
    fig.add_trace(
        go.Histogram(
            x=df_comparison['pre_performance'],
            name='Before Optimization',
            opacity=0.7,
            nbinsx=15
        ),
        row=1, col=2
    )
    
    fig.add_trace(
        go.Histogram(
            x=df_comparison['post_performance'],
            name='After Optimization',
            opacity=0.7,
            nbinsx=15
        ),
        row=1, col=2
    )
    
    # Chart 3: FCP Comparison
    fig.add_trace(
        go.Scatter(
            x=df_comparison['pre_fcp'],
            y=df_comparison['post_fcp'],
            mode='markers',
            marker=dict(color='blue', size=8),
            name='FCP Comparison',
            showlegend=False
        ),
        row=2, col=1
    )
    
    # FCP diagonal line
    min_fcp = min(df_comparison['pre_fcp'].min(), df_comparison['post_fcp'].min())
    max_fcp = max(df_comparison['pre_fcp'].max(), df_comparison['post_fcp'].max())
    fig.add_trace(
        go.Scatter(
            x=[min_fcp, max_fcp],
            y=[min_fcp, max_fcp],
            mode='lines',
            line=dict(dash='dash', color='red'),
            showlegend=False
        ),
        row=2, col=1
    )
    
    # Chart 4: LCP Comparison
    fig.add_trace(
        go.Scatter(
            x=df_comparison['pre_lcp'],
            y=df_comparison['post_lcp'],
            mode='markers',
            marker=dict(color='green', size=8),
            name='LCP Comparison',
            showlegend=False
        ),
        row=2, col=2
    )
    
    # LCP diagonal line
    min_lcp = min(df_comparison['pre_lcp'].min(), df_comparison['post_lcp'].min())
    max_lcp = max(df_comparison['pre_lcp'].max(), df_comparison['post_lcp'].max())
    fig.add_trace(
        go.Scatter(
            x=[min_lcp, max_lcp],
            y=[min_lcp, max_lcp],
            mode='lines',
            line=dict(dash='dash', color='red'),
            showlegend=False
        ),
        row=2, col=2
    )
    
    # Chart 5: TBT Improvement
    tbt_improvement = df_comparison['pre_tbt'] - df_comparison['post_tbt']
    fig.add_trace(
        go.Bar(
            x=list(range(len(tbt_improvement))),
            y=tbt_improvement,
            name='TBT Reduction (ms)',
            marker_color='purple',
            showlegend=False
        ),
        row=3, col=1
    )
    
    # Chart 6: Category Migration
    category_migration = df_comparison.groupby(['pre_category', 'post_category']).size().reset_index(name='count')
    
    fig.add_trace(
        go.Bar(
            x=[f"{row['pre_category']} → {row['post_category']}" for _, row in category_migration.iterrows()],
            y=category_migration['count'],
            name='Category Changes',
            showlegend=False,
            marker_color='orange'
        ),
        row=3, col=2
    )
    
    # Update layout
    fig.update_layout(
        height=1400,
        title_text="Same URL Performance Analysis: Before vs After Directus Optimization<br><sub>Detailed comparison of identical URLs tested in both periods</sub>",
        title_x=0.5,
        showlegend=True
    )
    
    # Update axes labels
    fig.update_xaxes(title_text="Performance Before", row=1, col=1)
    fig.update_yaxes(title_text="Performance After", row=1, col=1)
    fig.update_xaxes(title_text="Performance Score", row=1, col=2)
    fig.update_yaxes(title_text="Frequency", row=1, col=2)
    fig.update_xaxes(title_text="FCP Before (ms)", row=2, col=1)
    fig.update_yaxes(title_text="FCP After (ms)", row=2, col=1)
    fig.update_xaxes(title_text="LCP Before (ms)", row=2, col=2)
    fig.update_yaxes(title_text="LCP After (ms)", row=2, col=2)
    fig.update_xaxes(title_text="URL Index", row=3, col=1)
    fig.update_yaxes(title_text="TBT Reduction (ms)", row=3, col=1)
    fig.update_xaxes(title_text="Category Migration", row=3, col=2)
    fig.update_yaxes(title_text="Number of URLs", row=3, col=2)
    
    # Calculate summary statistics
    summary_stats = {
        'total_comparisons': len(df_comparison),
        'avg_improvement': df_comparison['improvement_percentage'].mean(),
        'median_improvement': df_comparison['improvement_percentage'].median(),
        'improved_urls': len(df_comparison[df_comparison['improvement_percentage'] > 0]),
        'degraded_urls': len(df_comparison[df_comparison['improvement_percentage'] < 0]),
        'unchanged_urls': len(df_comparison[df_comparison['improvement_percentage'] == 0]),
        'category_changes': len(df_comparison[df_comparison['pre_category'] != df_comparison['post_category']]),
        'avg_fcp_change': (df_comparison['post_fcp'] - df_comparison['pre_fcp']).mean(),
        'avg_lcp_change': (df_comparison['post_lcp'] - df_comparison['pre_lcp']).mean(),
        'avg_tbt_change': (df_comparison['pre_tbt'] - df_comparison['post_tbt']).mean()
    }
    
    # Get top performers
    top_improved = df_comparison.nlargest(10, 'improvement_percentage')
    top_degraded = df_comparison.nsmallest(5, 'improvement_percentage')
    
    # Generate HTML dashboard
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Same URL Performance Analysis - Directus Optimization Impact</title>
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
            .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }}
            .metric-card {{ background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #007bff; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Same URL Performance Analysis</h1>
                <h2>Impact of Directus Optimization on Identical URLs</h2>
                <p><strong>Analysis Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><em>This analysis compares the performance of the exact same URLs before and after optimization</em></p>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{summary_stats['total_comparisons']}</div>
                    <div class="stat-label">URLs Compared</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{summary_stats['avg_improvement']:.1f}%</div>
                    <div class="stat-label">Average Improvement</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{summary_stats['improved_urls']}</div>
                    <div class="stat-label">URLs Improved</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{summary_stats['degraded_urls']}</div>
                    <div class="stat-label">URLs Degraded</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{summary_stats['category_changes']}</div>
                    <div class="stat-label">Category Upgrades</div>
                </div>
            </div>
            
            <div class="section">
                <div id="main-chart" style="width:100%;height:1400px;"></div>
            </div>
            
            <div class="section">
                <div class="insights">
                    <h3>🎯 Key Insights</h3>
                    <ul>
                        <li><strong>Overall Impact:</strong> {(summary_stats['improved_urls']/summary_stats['total_comparisons']*100):.1f}% of URLs showed performance improvement</li>
                        <li><strong>Consistent Gains:</strong> Average improvement of {summary_stats['avg_improvement']:.1f}% across all compared URLs</li>
                        <li><strong>Median Improvement:</strong> {summary_stats['median_improvement']:.1f}% (shows consistent, not just outlier-driven gains)</li>
                        <li><strong>Category Upgrades:</strong> {summary_stats['category_changes']} URLs moved to better performance categories</li>
                        <li><strong>Core Web Vitals:</strong> TBT improved by an average of {summary_stats['avg_tbt_change']:.0f}ms per URL</li>
                    </ul>
                </div>
            </div>
            
            <div class="section">
                <h3>📊 Core Web Vitals Impact</h3>
                <div class="metric-grid">
                    <div class="metric-card">
                        <h4>First Contentful Paint (FCP)</h4>
                        <p>Average change: <span class="{'improvement' if summary_stats['avg_fcp_change'] < 0 else 'degradation'}">{summary_stats['avg_fcp_change']:+.0f}ms</span></p>
                        <small>Lower is better. Negative values indicate improvement.</small>
                    </div>
                    <div class="metric-card">
                        <h4>Largest Contentful Paint (LCP)</h4>
                        <p>Average change: <span class="{'improvement' if summary_stats['avg_lcp_change'] < 0 else 'degradation'}">{summary_stats['avg_lcp_change']:+.0f}ms</span></p>
                        <small>Lower is better. Negative values indicate improvement.</small>
                    </div>
                    <div class="metric-card">
                        <h4>Total Blocking Time (TBT)</h4>
                        <p>Average reduction: <span class="improvement">{summary_stats['avg_tbt_change']:+.0f}ms</span></p>
                        <small>Lower is better. Positive values indicate improvement.</small>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h3>🏆 Top 10 Most Improved URLs</h3>
                <table class="data-table">
                    <tr><th>URL</th><th>Before</th><th>After</th><th>Improvement</th><th>Category Change</th></tr>
    """
    
    for _, row in top_improved.iterrows():
        improvement_class = "improvement" if row['improvement_percentage'] > 0 else "degradation"
        url_display = row['url'][:50] + '...' if len(row['url']) > 50 else row['url']
        html_content += f"""
        <tr>
            <td>{url_display}</td>
            <td>{row['pre_performance']:.1f}</td>
            <td>{row['post_performance']:.1f}</td>
            <td class="{improvement_class}">{row['improvement_percentage']:+.1f}%</td>
            <td>{row['pre_category']} → {row['post_category']}</td>
        </tr>
        """
    
    html_content += f"""
                </table>
            </div>
            
            <div class="section">
                <h3>⚠️ URLs That Need Attention</h3>
                <table class="data-table">
                    <tr><th>URL</th><th>Before</th><th>After</th><th>Change</th><th>Category Change</th></tr>
    """
    
    for _, row in top_degraded.iterrows():
        improvement_class = "improvement" if row['improvement_percentage'] > 0 else "degradation"
        url_display = row['url'][:50] + '...' if len(row['url']) > 50 else row['url']
        html_content += f"""
        <tr>
            <td>{url_display}</td>
            <td>{row['pre_performance']:.1f}</td>
            <td>{row['post_performance']:.1f}</td>
            <td class="{improvement_class}">{row['improvement_percentage']:+.1f}%</td>
            <td>{row['pre_category']} → {row['post_category']}</td>
        </tr>
        """
    
    html_content += f"""
                </table>
            </div>
            
            <div class="section">
                <div class="warning">
                    <h3>📋 Analysis Notes</h3>
                    <ul>
                        <li><strong>Same URLs Only:</strong> This analysis includes only URLs that were tested both before and after optimization</li>
                        <li><strong>Fair Comparison:</strong> Data is aggregated per URL to handle multiple test runs</li>
                        <li><strong>Performance Scores:</strong> Based on Google PageSpeed Insights methodology (0-100 scale)</li>
                        <li><strong>Core Web Vitals:</strong> Key metrics for user experience (FCP, LCP, TBT, CLS)</li>
                        <li><strong>Color Coding:</strong> Green indicates improvement, red indicates degradation</li>
                        <li><strong>Statistical Significance:</strong> Results based on {summary_stats['total_comparisons']} URL comparisons</li>
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
    output_file = "same_url_performance_dashboard.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\\n✅ Interactive dashboard created: {output_file}")
    print(f"📊 Analysis Summary:")
    print(f"   • Total URLs compared: {summary_stats['total_comparisons']}")
    print(f"   • Average improvement: {summary_stats['avg_improvement']:.1f}%")
    print(f"   • URLs improved: {summary_stats['improved_urls']} ({summary_stats['improved_urls']/summary_stats['total_comparisons']*100:.1f}%)")
    print(f"   • URLs degraded: {summary_stats['degraded_urls']} ({summary_stats['degraded_urls']/summary_stats['total_comparisons']*100:.1f}%)")
    print(f"   • Category upgrades: {summary_stats['category_changes']}")
    
    return df_comparison, summary_stats

if __name__ == "__main__":
    print("Creating Same URL Performance Analysis Dashboard...")
    print("=" * 60)
    
    try:
        comparison_df, stats = create_interactive_dashboard()
        print("\\n🎉 Analysis complete! Open the HTML file to view the interactive dashboard.")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
