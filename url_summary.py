import pandas as pd
import json
import os

def create_simple_url_summary():
    """Create a simple summary table for all URLs"""
    
    # Extract all URL data
    data_dir = "pagespeed-reports"
    all_data = []
    
    folder_mapping = {
        "article-qa-8-7-2025-3-41-pm": "2025-07-08 15:41:00",
        "article-qa-8-7-2025-5-39-pm": "2025-07-08 17:39:00", 
        "article-qa-8-7-2025-8-31-pm": "2025-07-08 20:31:00",
        "article-qa-9-7-2025-10-56-am": "2025-07-09 10:56:00",
        "article-qa-9-7-2025-2-52-pm": "2025-07-09 14:52:00"
    }
    
    # Get traffic data
    traffic_values = {
        "2025-07-08 15:41:00": 341,
        "2025-07-08 17:39:00": 449,
        "2025-07-08 20:31:00": 361,
        "2025-07-09 10:56:00": 503,
        "2025-07-09 14:52:00": 440
    }
    
    for folder, timestamp in folder_mapping.items():
        folder_path = os.path.join(data_dir, folder)
        if os.path.exists(folder_path):
            json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
            if json_files:
                json_path = os.path.join(folder_path, json_files[0])
                try:
                    with open(json_path, 'r') as f:
                        data = json.load(f)
                    
                    results = data.get('results', [])
                    for result in results:
                        url_name = result.get('url', '').split('/')[-1]
                        all_data.append({
                            'url_name': url_name,
                            'full_url': result.get('url', ''),
                            'time': timestamp,
                            'performance_score': result.get('performance', 0),
                            'lcp': result.get('largestContentfulPaint', 0),
                            'fcp': result.get('firstContentfulPaint', 0),
                            'traffic': traffic_values.get(timestamp, 0)
                        })
                except Exception as e:
                    print(f"Error: {e}")
    
    df = pd.DataFrame(all_data)
    
    # Get unique URLs with their average performance
    url_summary = df.groupby('url_name').agg({
        'performance_score': ['mean', 'min', 'max', 'std'],
        'lcp': 'mean',
        'fcp': 'mean',
        'traffic': 'mean'
    }).round(1)
    
    # Flatten column names
    url_summary.columns = ['avg_performance', 'min_performance', 'max_performance', 'std_performance', 'avg_lcp', 'avg_fcp', 'avg_traffic']
    url_summary = url_summary.reset_index()
    
    # Sort by average performance
    url_summary = url_summary.sort_values('avg_performance', ascending=False)
    
    # Save to CSV
    url_summary.to_csv('url_performance_summary.csv', index=False)
    
    # Create a readable summary
    print("=== URL PERFORMANCE SUMMARY ===")
    print(f"Total unique URLs: {len(url_summary)}")
    print(f"Average performance across all URLs: {url_summary['avg_performance'].mean():.1f}")
    print(f"Best performing URL: {url_summary.iloc[0]['url_name']} (Score: {url_summary.iloc[0]['avg_performance']:.1f})")
    print(f"Worst performing URL: {url_summary.iloc[-1]['url_name']} (Score: {url_summary.iloc[-1]['avg_performance']:.1f})")
    
    print("\n=== TOP 10 BEST PERFORMING URLs ===")
    for i, row in url_summary.head(10).iterrows():
        print(f"{row['avg_performance']:.1f} | {row['avg_traffic']:.0f} traffic | {row['url_name'][:50]}")
    
    print("\n=== TOP 10 WORST PERFORMING URLs ===")
    for i, row in url_summary.tail(10).iterrows():
        print(f"{row['avg_performance']:.1f} | {row['avg_traffic']:.0f} traffic | {row['url_name'][:50]}")
    
    # Performance vs Traffic Analysis
    correlation = url_summary['avg_performance'].corr(url_summary['avg_traffic'])
    print(f"\n=== CORRELATION ANALYSIS ===")
    print(f"Performance vs Traffic Correlation: {correlation:.3f}")
    
    if correlation > 0.3:
        print("Strong POSITIVE correlation: Higher traffic = Better performance")
    elif correlation < -0.3:
        print("Strong NEGATIVE correlation: Higher traffic = Worse performance")
    else:
        print("WEAK correlation: Traffic and performance not strongly related")
    
    # Key insights
    print(f"\n=== KEY INSIGHTS ===")
    print(f"• URLs with performance > 80: {len(url_summary[url_summary['avg_performance'] > 80])}")
    print(f"• URLs with performance < 40: {len(url_summary[url_summary['avg_performance'] < 40])}")
    print(f"• Average LCP across all URLs: {url_summary['avg_lcp'].mean():.0f}ms")
    print(f"• Average FCP across all URLs: {url_summary['avg_fcp'].mean():.0f}ms")
    
    # URLs that need immediate attention
    critical_urls = url_summary[url_summary['avg_performance'] < 40]
    print(f"\n=== CRITICAL URLS NEEDING ATTENTION ({len(critical_urls)} URLs) ===")
    for i, row in critical_urls.iterrows():
        print(f"⚠️  {row['avg_performance']:.1f} | {row['url_name'][:60]}")
    
    return url_summary

if __name__ == "__main__":
    summary_df = create_simple_url_summary()
    print(f"\n📊 Summary saved to 'url_performance_summary.csv'")
    print("✅ Analysis complete!")
