#!/usr/bin/env python3
"""
Post-Optimization Scatter Plot
Creates a scatter plot showing only post-optimization data with:
- X-axis: Traffic levels
- Y-axis: Performance scores
- All URLs combined in one visualization
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import sys

# Import the analyzer class
sys.path.append('.')
from url_by_url_traffic_analysis import URLTrafficPerformanceAnalyzer

def create_post_optimization_scatter():
    """Create scatter plot for post-optimization data only."""
    base_dir = "."
    analyzer = URLTrafficPerformanceAnalyzer(base_dir)
    
    print("Loading data for post-optimization scatter plot...")
    
    # Load data
    analyzer.load_traffic_data()
    analyzer.load_all_performance_data()
    
    # Get only post-optimization data
    post_data = analyzer.all_data[analyzer.all_data['optimization_status'] == 'post'].copy()
    
    if post_data.empty:
        print("No post-optimization data found!")
        return
    
    print(f"Found {len(post_data)} post-optimization test results")
    print(f"Traffic range: {post_data['estimated_traffic'].min()} to {post_data['estimated_traffic'].max()}")
    print(f"Performance range: {post_data['Performance'].min()} to {post_data['Performance'].max()}")
    print(f"Number of unique URLs: {post_data['URL'].nunique()}")
    
    # Create scatter plot
    fig = go.Figure()
    
    # Get unique URLs and assign different colors
    unique_urls = post_data['URL'].unique()
    colors = px.colors.qualitative.Set3 + px.colors.qualitative.Pastel + px.colors.qualitative.Set1
    
    # Add scatter points and lines for each URL with different colors
    for i, url in enumerate(unique_urls):
        url_data = post_data[post_data['URL'] == url].copy()
        url_short = url.split('/')[-1][:50] if '/' in url else url[:50]
        
        # Sort by traffic (x-axis) to connect points properly
        url_data = url_data.sort_values('estimated_traffic')
        
        fig.add_trace(go.Scatter(
            x=url_data['estimated_traffic'],
            y=url_data['Performance'],
            mode='markers+lines',
            name=url_short,
            line=dict(
                color=colors[i % len(colors)],
                width=2,
                dash='solid'
            ),
            marker=dict(
                size=8,
                color=colors[i % len(colors)],
                opacity=0.8,
                line=dict(width=1, color='DarkSlateGrey')
            ),
            text=[f"URL: {url}<br>Time: {ts}<br>Performance: {perf}<br>Traffic: {traffic}" 
                  for ts, perf, traffic in zip(
                      url_data['timestamp'],
                      url_data['Performance'],
                      url_data['estimated_traffic']
                  )],
            hovertemplate='%{text}<extra></extra>',
            showlegend=True,
            visible=True
        ))
    
    # Update layout
    fig.update_layout(
        title={
            'text': "Post-Optimization: Traffic vs Performance Scatter Plot<br><sub>All URLs - Each Color Represents a Different URL (Connected by Lines)<br>Use dropdown to select individual URLs • Click legend items to show/hide • Double-click legend to isolate</sub>",
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="Site Traffic (Users)",
        yaxis_title="Performance Score",
        height=700,
        width=1200,
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="Black",
            borderwidth=1,
            itemclick="toggle",
            itemdoubleclick="toggleothers"
        ),
        margin=dict(r=300),  # Make room for legend
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                buttons=list([
                    dict(
                        args=[{"visible": [True] * len(unique_urls)}],
                        label="Show All URLs",
                        method="restyle"
                    ),
                    dict(
                        args=[{"visible": [False] * len(unique_urls)}],
                        label="Hide All URLs", 
                        method="restyle"
                    ),
                    dict(
                        args=[{"mode": ["markers+lines"] * len(unique_urls)}],
                        label="Lines + Markers",
                        method="restyle"
                    ),
                    dict(
                        args=[{"mode": ["markers"] * len(unique_urls)}],
                        label="Markers Only",
                        method="restyle"
                    )
                ]),
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.01,
                xanchor="left",
                y=1.02,
                yanchor="top"
            ),
            # Dropdown for selecting individual URLs
            dict(
                type="dropdown",
                direction="down",
                buttons=list([
                    dict(
                        args=[{"visible": [True] * len(unique_urls)}],
                        label="All URLs",
                        method="restyle"
                    )
                ] + [
                    dict(
                        args=[{"visible": [i == j for j in range(len(unique_urls))]}],
                        label=f"Only: {url.split('/')[-1][:40] if '/' in url else url[:40]}",
                        method="restyle"
                    ) for i, url in enumerate(unique_urls)
                ]),
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.01,
                xanchor="left",
                y=0.95,
                yanchor="top"
            ),
        ]
    )
    
    # Add grid
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    
    # Save the chart
    output_dir = Path(base_dir) / "url_traffic_analysis"
    output_dir.mkdir(exist_ok=True)
    
    chart_path = output_dir / "post_optimization_scatter.html"
    fig.write_html(chart_path)
    
    print(f"\n✅ Post-optimization scatter plot created!")
    print(f"📊 Chart saved to: {chart_path}")
    print(f"💡 Easy URL selection options:")
    print(f"   • Use DROPDOWN menu to instantly select any single URL")
    print(f"   • Click legend items to manually show/hide URLs")
    print(f"   • Double-click legend items to isolate one URL")
    print(f"   • Use buttons for show all/hide all operations")
    
    # Create a version without legend for cleaner view
    fig_no_legend = go.Figure()
    
    # Sort post_data by URL and traffic for proper line connections
    post_data_sorted = post_data.sort_values(['URL', 'estimated_traffic'])
    
    # Group by URL and add each as a separate trace for line connections
    for i, url in enumerate(unique_urls):
        url_data = post_data_sorted[post_data_sorted['URL'] == url].copy()
        url_short = url.split('/')[-1][:30] if '/' in url else url[:30]
        
        fig_no_legend.add_trace(go.Scatter(
            x=url_data['estimated_traffic'],
            y=url_data['Performance'],
            mode='markers+lines',
            name=url_short,
            line=dict(
                color=colors[i % len(colors)],
                width=1.5,
                dash='solid'
            ),
            marker=dict(
                size=6,
                color=url_data['Performance'],
                colorscale='Viridis',
                opacity=0.8,
                line=dict(width=1, color='DarkSlateGrey'),
                colorbar=dict(title="Performance Score") if i == 0 else None,
                showscale=True if i == 0 else False
            ),
            text=[f"URL: {url}<br>Time: {ts}<br>Performance: {perf}<br>Traffic: {traffic}" 
                  for ts, perf, traffic in zip(
                      url_data['timestamp'],
                      url_data['Performance'],
                      url_data['estimated_traffic']
                  )],
            hovertemplate='%{text}<extra></extra>',
            showlegend=False
        ))
    
    fig_no_legend.update_layout(
        title={
            'text': "Post-Optimization: Traffic vs Performance Scatter Plot<br><sub>Connected Lines Show Performance Trends Across Traffic Levels</sub>",
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="Site Traffic (Users)",
        yaxis_title="Performance Score",
        height=700,
        width=1000,
        showlegend=False,
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                buttons=list([
                    dict(
                        args=[{"visible": [True] * len(unique_urls)}],
                        label="Show All",
                        method="restyle"
                    ),
                    dict(
                        args=[{"visible": [False] * len(unique_urls)}],
                        label="Hide All",
                        method="restyle"
                    ),
                    dict(
                        args=[{"mode": ["markers+lines"] * len(unique_urls)}],
                        label="Lines + Markers",
                        method="restyle"
                    ),
                    dict(
                        args=[{"mode": ["markers"] * len(unique_urls)}],
                        label="Markers Only",
                        method="restyle"
                    )
                ]),
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.01,
                xanchor="left",
                y=1.02,
                yanchor="top"
            ),
        ]
    )
    
    # Add grid
    fig_no_legend.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    fig_no_legend.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    
    # Save the cleaner version
    chart_path_clean = output_dir / "post_optimization_scatter_clean.html"
    fig_no_legend.write_html(chart_path_clean)
    
    print(f"📊 Clean version saved to: {chart_path_clean}")
    
    # Print summary statistics
    print(f"\n📈 Summary Statistics:")
    print(f"   • Total post-optimization tests: {len(post_data)}")
    print(f"   • Unique URLs: {len(unique_urls)}")
    print(f"   • Traffic range: {post_data['estimated_traffic'].min()}-{post_data['estimated_traffic'].max()} users")
    print(f"   • Performance range: {post_data['Performance'].min()}-{post_data['Performance'].max()}")
    print(f"   • Average performance: {post_data['Performance'].mean():.1f}")
    print(f"   • Tests per URL: {len(post_data) / len(unique_urls):.1f} average")
    
    return chart_path, chart_path_clean

if __name__ == "__main__":
    create_post_optimization_scatter()
