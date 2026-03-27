import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime, timedelta
import os
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

def extract_all_urls_data():
    """Extract performance data for all 60 URLs from all JSON files"""
    data_dir = "pagespeed-reports"
    all_urls_data = []
    
    # Map folder names to timestamps
    folder_mapping = {
        "article-qa-8-7-2025-3-41-pm": "2025-07-08 15:41:00",
        "article-qa-8-7-2025-5-39-pm": "2025-07-08 17:39:00", 
        "article-qa-8-7-2025-8-31-pm": "2025-07-08 20:31:00",
        "article-qa-9-7-2025-10-56-am": "2025-07-09 10:56:00",
        "article-qa-9-7-2025-2-52-pm": "2025-07-09 14:52:00"
    }
    
    for folder, timestamp in folder_mapping.items():
        folder_path = os.path.join(data_dir, folder)
        if os.path.exists(folder_path):
            # Look for JSON files in the folder
            json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
            if json_files:
                json_file = json_files[0]
                json_path = os.path.join(folder_path, json_file)
                
                try:
                    with open(json_path, 'r') as f:
                        data = json.load(f)
                    
                    # Extract individual URL results
                    results = data.get('results', [])
                    for result in results:
                        url_data = {
                            'measurement_time': timestamp,
                            'url': result.get('url', ''),
                            'performance_score': result.get('performance', 0),
                            'accessibility': result.get('accessibility', 0),
                            'best_practices': result.get('bestPractices', 0),
                            'seo': result.get('seo', 0),
                            'fcp': result.get('firstContentfulPaint', 0),
                            'lcp': result.get('largestContentfulPaint', 0),
                            'speed_index': result.get('speedIndex', 0),
                            'ttfb': result.get('ttfb', 0),
                            'cls': result.get('cumulativeLayoutShift', 0),
                            'folder': folder
                        }
                        all_urls_data.append(url_data)
                        
                except Exception as e:
                    print(f"Error loading {json_path}: {e}")
    
    return pd.DataFrame(all_urls_data)

def get_traffic_for_time(target_time):
    """Get traffic data for a specific time"""
    try:
        excel_path = "pagespeed-reports/ga_user_traffics/Realtime Automation Tracking Top 7 Country.xlsx"
        traffic_df = pd.read_excel(excel_path, sheet_name='Jul - 2025')
        
        # Parse target time
        target_dt = pd.to_datetime(target_time)
        
        # Extract date from first cell
        date_str = str(traffic_df.iloc[0, 0])
        base_date = pd.to_datetime(date_str.split()[0])
        
        # If target is July 9, but our traffic data is July 8, adjust
        if target_dt.date() != base_date.date():
            # Use approximate traffic data (could be improved with more data)
            target_hour = target_dt.hour
        else:
            target_hour = target_dt.hour
        
        # Find closest time column
        best_col = None
        best_diff = float('inf')
        
        for col_idx in range(1, len(traffic_df.columns)):
            if col_idx < len(traffic_df.columns):
                try:
                    time_str = str(traffic_df.iloc[0, col_idx])
                    if time_str != 'nan' and ':' in time_str:
                        time_parts = time_str.split(':')
                        if len(time_parts) >= 2:
                            hour = int(time_parts[0])
                            minute = int(time_parts[1])
                            
                            # Calculate difference from target hour
                            time_diff = abs(hour - target_hour)
                            if time_diff < best_diff:
                                best_diff = time_diff
                                best_col = col_idx
                except:
                    continue
        
        if best_col is not None:
            # Extract traffic data for the best matching time
            us_traffic = traffic_df.iloc[1, best_col] if pd.notna(traffic_df.iloc[1, best_col]) else 0
            india_traffic = traffic_df.iloc[2, best_col] if pd.notna(traffic_df.iloc[2, best_col]) else 0
            total_traffic = traffic_df.iloc[8, best_col] if pd.notna(traffic_df.iloc[8, best_col]) else 0
            page_views = traffic_df.iloc[9, best_col] if pd.notna(traffic_df.iloc[9, best_col]) else 0
            
            # Convert to numeric
            try:
                us_traffic = float(us_traffic) if us_traffic not in ['All', 'Page Views'] else 0
                india_traffic = float(india_traffic) if india_traffic not in ['All', 'Page Views'] else 0
                total_traffic = float(total_traffic) if total_traffic not in ['All', 'Page Views'] else 0
                page_views = float(page_views) if page_views not in ['All', 'Page Views'] else 0
            except (ValueError, TypeError):
                us_traffic = india_traffic = total_traffic = page_views = 0
            
            return {
                'total_traffic': total_traffic,
                'us_traffic': us_traffic,
                'india_traffic': india_traffic,
                'page_views': page_views
            }
    
    except Exception as e:
        print(f"Error getting traffic data for {target_time}: {e}")
    
    return {'total_traffic': 0, 'us_traffic': 0, 'india_traffic': 0, 'page_views': 0}

def create_url_performance_traffic_analysis():
    """Create analysis showing performance vs traffic for all URLs"""
    
    # Get all URLs data
    print("Extracting data for all 60 URLs...")
    urls_df = extract_all_urls_data()
    
    print(f"Total URL measurements: {len(urls_df)}")
    print(f"Unique URLs: {urls_df['url'].nunique()}")
    print(f"Time periods: {urls_df['measurement_time'].nunique()}")
    
    # Add traffic data for each measurement
    print("Adding traffic data...")
    traffic_data = []
    
    for _, row in urls_df.iterrows():
        traffic_info = get_traffic_for_time(row['measurement_time'])
        traffic_data.append(traffic_info)
    
    # Combine with URL data
    for i, traffic_info in enumerate(traffic_data):
        for key, value in traffic_info.items():
            urls_df.loc[i, key] = value
    
    # Create visualizations
    print("Creating visualizations...")
    
    # Create a simple single chart focused on the key question
    fig = go.Figure()
    
    # Simple scatter plot: Performance vs Traffic
    fig.add_trace(
        go.Scatter(
            x=urls_df['total_traffic'],
            y=urls_df['performance_score'],
            mode='markers',
            text=urls_df['url'].str.replace('https://www.example.com/qa/specialities/', '').str.replace('https://www.example.com/', ''),
            hovertemplate='<b>%{text}</b><br>' +
                          'Performance Score: %{y}<br>' +
                          'Traffic: %{x}<br>' +
                          '<extra></extra>',
            marker=dict(
                size=12,
                color=urls_df['performance_score'],
                colorscale='RdYlGn',
                colorbar=dict(
                    title="Performance Score",
                    x=1.02,
                    xanchor="left",
                    len=0.8
                ),
                line=dict(width=1, color='black'),
                opacity=0.8
            ),
            name='URLs'
        )
    )
    
    # Add trend line to show correlation
    if urls_df['total_traffic'].sum() > 0:
        z = np.polyfit(urls_df['total_traffic'], urls_df['performance_score'], 1)
        p = np.poly1d(z)
        
        fig.add_trace(
            go.Scatter(
                x=urls_df['total_traffic'],
                y=p(urls_df['total_traffic']),
                mode='lines',
                name='Trend Line',
                line=dict(color='red', width=3, dash='dash'),
                hoverinfo='skip'
            )
        )
    
    # Update layout for clarity
    fig.update_layout(
        title=dict(
            text='Does Traffic Affect Performance?<br><sub>Each dot is one URL - Green = Good Performance, Red = Poor Performance</sub>',
            x=0.5,
            font=dict(size=18)
        ),
        xaxis_title="Website Traffic (Users)",
        yaxis_title="Performance Score (0-100)",
        height=700,
        width=1200,
        showlegend=True,
        template='plotly_white',
        font=dict(size=12),
        legend=dict(
            x=0.02,
            y=0.98,
            xanchor="left",
            yanchor="top",
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="black",
            borderwidth=1
        ),
        margin=dict(l=80, r=150, t=100, b=80)
    )
    
    
    # Save interactive chart
    fig.write_html("simple_performance_traffic_analysis.html")
    print("Simple interactive chart saved as 'simple_performance_traffic_analysis.html'")
    
    # Create an even simpler static chart for quick understanding
    create_ultra_simple_chart(urls_df)
    
    return urls_df

def create_simple_matplotlib_chart(urls_df):
    """Create a simple matplotlib chart showing performance vs traffic"""
    
    plt.figure(figsize=(15, 10))
    
    # Create subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    # Plot 1: Performance vs Traffic scatter
    scatter = ax1.scatter(urls_df['total_traffic'], urls_df['performance_score'], 
                         c=urls_df['lcp'], cmap='RdYlBu_r', s=50, alpha=0.7, edgecolors='black')
    ax1.set_xlabel('Total Traffic')
    ax1.set_ylabel('Performance Score')
    ax1.set_title('Performance Score vs Traffic (All 60 URLs)')
    ax1.grid(True, alpha=0.3)
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax1)
    cbar.set_label('LCP (ms)')
    
    # Plot 2: Performance distribution by time
    measurement_times = urls_df['measurement_time'].unique()
    perf_by_time = [urls_df[urls_df['measurement_time'] == time]['performance_score'].values 
                    for time in measurement_times]
    
    ax2.boxplot(perf_by_time, labels=[time.split()[1][:5] for time in measurement_times])
    ax2.set_xlabel('Time Period')
    ax2.set_ylabel('Performance Score')
    ax2.set_title('Performance Distribution by Time')
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Top 10 best URLs
    top_10_best = urls_df.nlargest(10, 'performance_score')
    url_names = [url.split('/')[-1][:20] + '...' for url in top_10_best['url']]
    
    ax3.barh(range(len(url_names)), top_10_best['performance_score'], color='green', alpha=0.7)
    ax3.set_yticks(range(len(url_names)))
    ax3.set_yticklabels(url_names, fontsize=8)
    ax3.set_xlabel('Performance Score')
    ax3.set_title('Top 10 Best Performing URLs')
    ax3.grid(True, alpha=0.3, axis='x')
    
    # Plot 4: Top 10 worst URLs
    top_10_worst = urls_df.nsmallest(10, 'performance_score')
    url_names_worst = [url.split('/')[-1][:20] + '...' for url in top_10_worst['url']]
    
    ax4.barh(range(len(url_names_worst)), top_10_worst['performance_score'], color='red', alpha=0.7)
    ax4.set_yticks(range(len(url_names_worst)))
    ax4.set_yticklabels(url_names_worst, fontsize=8)
    ax4.set_xlabel('Performance Score')
    ax4.set_title('Top 10 Worst Performing URLs')
    ax4.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    plt.savefig('url_performance_analysis.png', dpi=300, bbox_inches='tight')
    print("Static chart saved as 'url_performance_analysis.png'")
    
    # Create correlation summary
    if urls_df['total_traffic'].sum() > 0:
        correlation = urls_df['performance_score'].corr(urls_df['total_traffic'])
        
        plt.figure(figsize=(10, 6))
        plt.scatter(urls_df['total_traffic'], urls_df['performance_score'], alpha=0.6)
        plt.xlabel('Total Traffic')
        plt.ylabel('Performance Score')
        plt.title(f'Performance vs Traffic Correlation\nCorrelation Coefficient: {correlation:.3f}')
        plt.grid(True, alpha=0.3)
        
        # Add trend line
        z = np.polyfit(urls_df['total_traffic'], urls_df['performance_score'], 1)
        p = np.poly1d(z)
        plt.plot(urls_df['total_traffic'], p(urls_df['total_traffic']), "r--", alpha=0.8)
        
        plt.tight_layout()
        plt.savefig('performance_traffic_correlation.png', dpi=300, bbox_inches='tight')
        print("Correlation chart saved as 'performance_traffic_correlation.png'")

def create_ultra_simple_chart(urls_df):
    """Create the simplest possible chart to understand traffic vs performance"""
    
    plt.figure(figsize=(12, 8))
    
    # Create a simple scatter plot
    scatter = plt.scatter(urls_df['total_traffic'], urls_df['performance_score'], 
                         c=urls_df['performance_score'], cmap='RdYlGn', 
                         s=100, alpha=0.7, edgecolors='black')
    
    # Add trend line
    if urls_df['total_traffic'].sum() > 0:
        z = np.polyfit(urls_df['total_traffic'], urls_df['performance_score'], 1)
        p = np.poly1d(z)
        plt.plot(urls_df['total_traffic'], p(urls_df['total_traffic']), 
                "r--", linewidth=3, alpha=0.8, label='Trend Line')
        
        # Calculate correlation
        correlation = urls_df['performance_score'].corr(urls_df['total_traffic'])
        
        # Add correlation text
        if correlation > 0.3:
            corr_text = f"Strong POSITIVE correlation ({correlation:.2f})\nHigher traffic = Better performance"
            text_color = "green"
        elif correlation < -0.3:
            corr_text = f"Strong NEGATIVE correlation ({correlation:.2f})\nHigher traffic = Worse performance"
            text_color = "red"
        else:
            corr_text = f"WEAK correlation ({correlation:.2f})\nTraffic doesn't significantly affect performance"
            text_color = "orange"
        
        plt.text(0.02, 0.98, corr_text, transform=plt.gca().transAxes, 
                fontsize=14, verticalalignment='top', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='white', 
                         edgecolor=text_color, linewidth=2),
                color=text_color)
    
    plt.xlabel('Website Traffic (Users)', fontsize=14)
    plt.ylabel('Performance Score (0-100)', fontsize=14)
    plt.title('Does Traffic Affect Performance?\nEach dot is one URL measured at different times', 
              fontsize=16, fontweight='bold')
    plt.grid(True, alpha=0.3)
    
    # Add colorbar
    cbar = plt.colorbar(scatter)
    cbar.set_label('Performance Score', fontsize=12)
    
    # Add explanation
    plt.figtext(0.5, 0.02, 
                '🟢 Green dots = Good Performance  🔴 Red dots = Poor Performance  📈 Red line = Overall trend',
                ha='center', fontsize=12, style='italic')
    
    plt.tight_layout()
    plt.savefig('simple_traffic_performance_chart.png', dpi=300, bbox_inches='tight')
    print("Ultra-simple chart saved as 'simple_traffic_performance_chart.png'")
    
    # Print simple summary
    print("\n" + "="*50)
    print("📊 SIMPLE ANSWER: Does Traffic Affect Performance?")
    print("="*50)
    
    if urls_df['total_traffic'].sum() > 0:
        correlation = urls_df['performance_score'].corr(urls_df['total_traffic'])
        
        if correlation > 0.3:
            print("✅ YES - Higher traffic leads to BETTER performance")
            print(f"   Correlation: {correlation:.2f} (Strong positive)")
        elif correlation < -0.3:
            print("❌ YES - Higher traffic leads to WORSE performance")
            print(f"   Correlation: {correlation:.2f} (Strong negative)")
        else:
            print("➡️  NO - Traffic doesn't significantly affect performance")
            print(f"   Correlation: {correlation:.2f} (Weak)")
    
    print(f"\n📈 Performance ranges from {urls_df['performance_score'].min()} to {urls_df['performance_score'].max()}")
    print(f"👥 Traffic ranges from {urls_df['total_traffic'].min():.0f} to {urls_df['total_traffic'].max():.0f} users")
    print("="*50)

if __name__ == "__main__":
    print("Creating SIMPLE chart to understand: Does Traffic Affect Performance?")
    print("="*60)
    
    urls_data = create_url_performance_traffic_analysis()
    
    print(f"\n🎯 SIMPLE SUMMARY:")
    print(f"   📊 Total URLs analyzed: {len(urls_data)}")
    print(f"   📈 Average Performance: {urls_data['performance_score'].mean():.1f}/100")
    print(f"   👥 Average Traffic: {urls_data['total_traffic'].mean():.0f} users")
    
    print(f"\n📁 Files created:")
    print("   1. simple_performance_traffic_analysis.html - Interactive chart")
    print("   2. simple_traffic_performance_chart.png - Static chart")
    print("\n✅ Open the HTML file to explore individual URLs!")
