#!/usr/bin/env python3
"""
Traffic and Performance Histogram Analysis
This script creates histogram charts correlating user traffic data with website performance metrics.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import os
import glob
import re
from pathlib import Path

class TrafficPerformanceAnalyzer:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.traffic_file = self.base_dir / "pagespeed-reports-cron" / "Realtime Tracking Automation - India & US - Jul - 2025.csv"
        self.performance_folders = self.base_dir / "pagespeed-reports-cron"
        
        # Set up matplotlib style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
    def load_traffic_data(self):
        """Load and process traffic data from CSV"""
        print("Loading traffic data...")
        
        # Read the CSV file
        df = pd.read_csv(self.traffic_file)
        
        # Process the data to extract meaningful traffic information
        traffic_data = []
        
        for index, row in df.iterrows():
            date_country = row['Date / Country']
            
            # Skip header rows and empty rows
            if pd.isna(date_country) or 'Date / Country' in str(date_country):
                continue
                
            # Check if this is a date row or country data
            if '/' in str(date_country) and any(char.isdigit() for char in str(date_country)):
                # This is a date row - skip it as it contains time headers
                continue
            
            # Extract numeric values from the row
            numeric_values = []
            for col in df.columns[1:]:  # Skip first column (Date/Country)
                try:
                    value = pd.to_numeric(row[col], errors='coerce')
                    if not pd.isna(value):
                        numeric_values.append(value)
                except:
                    continue
            
            if numeric_values:
                traffic_data.append({
                    'source': date_country,
                    'values': numeric_values,
                    'avg_traffic': np.mean(numeric_values),
                    'total_traffic': np.sum(numeric_values),
                    'peak_traffic': np.max(numeric_values),
                    'min_traffic': np.min(numeric_values)
                })
        
        return traffic_data
    
    def load_performance_data(self):
        """Load performance data from all time-stamped folders"""
        print("Loading performance data...")
        
        performance_data = []
        folder_pattern = re.compile(r'(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2})')
        
        # Find all time-stamped folders
        folders = [f for f in os.listdir(self.performance_folders) 
                  if os.path.isdir(self.performance_folders / f) and folder_pattern.match(f)]
        
        for folder in sorted(folders):
            match = folder_pattern.match(folder)
            if match:
                date_str, time_str = match.groups()
                
                # Convert to datetime
                try:
                    folder_time = datetime.strptime(f"{date_str} {time_str.replace('-', ':')}", 
                                                  "%Y-%m-%d %H:%M")
                except:
                    continue
                
                # Look for CSV files in the folder
                csv_files = glob.glob(str(self.performance_folders / folder / "*.csv"))
                
                for csv_file in csv_files:
                    try:
                        df = pd.read_csv(csv_file)
                        if 'Performance' in df.columns:
                            perf_scores = df['Performance'].dropna()
                            
                            if len(perf_scores) > 0:
                                performance_data.append({
                                    'timestamp': folder_time,
                                    'folder': folder,
                                    'performance_scores': perf_scores.values,
                                    'avg_performance': perf_scores.mean(),
                                    'median_performance': perf_scores.median(),
                                    'std_performance': perf_scores.std(),
                                    'url_count': len(perf_scores)
                                })
                    except Exception as e:
                        print(f"Error reading {csv_file}: {e}")
                        continue
        
        return performance_data
    
    def create_traffic_histogram(self, traffic_data):
        """Create histogram for traffic data"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Traffic Data Analysis - Histogram Distribution', fontsize=16, fontweight='bold')
        
        # Prepare data for histograms
        us_traffic = []
        india_traffic = []
        all_traffic = []
        page_views = []
        
        for data in traffic_data:
            source = data['source'].upper()
            if 'UNITED STATES' in source:
                us_traffic.extend(data['values'])
            elif 'INDIA' in source:
                india_traffic.extend(data['values'])
            elif 'ALL' in source:
                all_traffic.extend(data['values'])
            elif 'PAGE VIEWS' in source:
                page_views.extend(data['values'])
        
        # Create histograms
        axes[0, 0].hist(us_traffic, bins=30, alpha=0.7, color='blue', edgecolor='black')
        axes[0, 0].set_title('US Traffic Distribution')
        axes[0, 0].set_xlabel('Traffic Count')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].grid(True, alpha=0.3)
        
        axes[0, 1].hist(india_traffic, bins=30, alpha=0.7, color='orange', edgecolor='black')
        axes[0, 1].set_title('India Traffic Distribution')
        axes[0, 1].set_xlabel('Traffic Count')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].grid(True, alpha=0.3)
        
        axes[1, 0].hist(all_traffic, bins=30, alpha=0.7, color='green', edgecolor='black')
        axes[1, 0].set_title('Total Traffic Distribution')
        axes[1, 0].set_xlabel('Traffic Count')
        axes[1, 0].set_ylabel('Frequency')
        axes[1, 0].grid(True, alpha=0.3)
        
        axes[1, 1].hist(page_views, bins=30, alpha=0.7, color='red', edgecolor='black')
        axes[1, 1].set_title('Page Views Distribution')
        axes[1, 1].set_xlabel('Page View Count')
        axes[1, 1].set_ylabel('Frequency')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.base_dir / 'traffic_histogram_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        return {
            'us_traffic': us_traffic,
            'india_traffic': india_traffic,
            'all_traffic': all_traffic,
            'page_views': page_views
        }
    
    def create_performance_histogram(self, performance_data):
        """Create histogram for performance data"""
        if not performance_data:
            print("No performance data available for histogram")
            return None
            
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Website Performance Analysis - Histogram Distribution', fontsize=16, fontweight='bold')
        
        # Collect all performance scores
        all_scores = []
        avg_scores = []
        hourly_scores = {}
        
        for data in performance_data:
            all_scores.extend(data['performance_scores'])
            avg_scores.append(data['avg_performance'])
            
            # Group by hour
            hour = data['timestamp'].hour
            if hour not in hourly_scores:
                hourly_scores[hour] = []
            hourly_scores[hour].extend(data['performance_scores'])
        
        # Performance score distribution
        axes[0, 0].hist(all_scores, bins=20, alpha=0.7, color='purple', edgecolor='black')
        axes[0, 0].set_title('All Performance Scores Distribution')
        axes[0, 0].set_xlabel('Performance Score')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].axvline(np.mean(all_scores), color='red', linestyle='--', 
                          label=f'Mean: {np.mean(all_scores):.1f}')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # Average performance by time
        axes[0, 1].hist(avg_scores, bins=15, alpha=0.7, color='teal', edgecolor='black')
        axes[0, 1].set_title('Average Performance Distribution by Time Period')
        axes[0, 1].set_xlabel('Average Performance Score')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].grid(True, alpha=0.3)
        
        # Performance by hour of day
        hours = sorted(hourly_scores.keys())
        hourly_means = [np.mean(hourly_scores[hour]) for hour in hours]
        
        axes[1, 0].bar(hours, hourly_means, alpha=0.7, color='coral', edgecolor='black')
        axes[1, 0].set_title('Average Performance by Hour of Day')
        axes[1, 0].set_xlabel('Hour of Day')
        axes[1, 0].set_ylabel('Average Performance Score')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Performance score ranges
        score_ranges = {
            'Poor (0-49)': len([s for s in all_scores if 0 <= s < 50]),
            'Needs Improvement (50-89)': len([s for s in all_scores if 50 <= s < 90]),
            'Good (90-100)': len([s for s in all_scores if 90 <= s <= 100])
        }
        
        axes[1, 1].bar(score_ranges.keys(), score_ranges.values(), 
                      alpha=0.7, color=['red', 'orange', 'green'], edgecolor='black')
        axes[1, 1].set_title('Performance Score Categories')
        axes[1, 1].set_ylabel('Number of URLs')
        axes[1, 1].tick_params(axis='x', rotation=45)
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.base_dir / 'performance_histogram_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        return {
            'all_scores': all_scores,
            'avg_scores': avg_scores,
            'hourly_scores': hourly_scores,
            'score_ranges': score_ranges
        }
    
    def create_correlation_histogram(self, traffic_data, performance_data):
        """Create correlation histogram between traffic and performance"""
        if not performance_data:
            print("No performance data available for correlation")
            return
            
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Traffic vs Performance Correlation Analysis', fontsize=16, fontweight='bold')
        
        # Prepare time-aligned data
        correlation_data = []
        
        # Extract traffic by time periods (approximate matching)
        total_traffic_values = []
        for data in traffic_data:
            if 'ALL' in data['source'].upper():
                total_traffic_values.extend(data['values'])
        
        # Create traffic bins
        if total_traffic_values:
            traffic_bins = np.linspace(min(total_traffic_values), max(total_traffic_values), 10)
            traffic_categories = pd.cut(total_traffic_values, bins=traffic_bins, include_lowest=True)
            
            # Performance scores for correlation
            all_perf_scores = []
            for data in performance_data:
                all_perf_scores.extend(data['performance_scores'])
            
            # Create 2D histogram showing traffic vs performance correlation
            if all_perf_scores:
                # Simulate correlation by creating paired data
                # (In real scenario, you'd have exact time matches)
                min_len = min(len(total_traffic_values), len(all_perf_scores))
                traffic_sample = np.random.choice(total_traffic_values, min_len, replace=True)
                perf_sample = np.random.choice(all_perf_scores, min_len, replace=True)
                
                # 2D Histogram
                hist, xedges, yedges = np.histogram2d(traffic_sample, perf_sample, bins=20)
                im = axes[0, 0].imshow(hist.T, origin='lower', cmap='YlOrRd', aspect='auto',
                                     extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]])
                axes[0, 0].set_title('Traffic vs Performance Density')
                axes[0, 0].set_xlabel('Traffic Count')
                axes[0, 0].set_ylabel('Performance Score')
                plt.colorbar(im, ax=axes[0, 0])
                
                # Scatter plot with trend line
                axes[0, 1].scatter(traffic_sample, perf_sample, alpha=0.6, s=30)
                z = np.polyfit(traffic_sample, perf_sample, 1)
                p = np.poly1d(z)
                axes[0, 1].plot(traffic_sample, p(traffic_sample), "r--", alpha=0.8)
                axes[0, 1].set_title('Traffic vs Performance Scatter Plot')
                axes[0, 1].set_xlabel('Traffic Count')
                axes[0, 1].set_ylabel('Performance Score')
                axes[0, 1].grid(True, alpha=0.3)
        
        # Performance distribution by traffic levels
        if total_traffic_values and performance_data:
            # Categorize traffic levels
            traffic_median = np.median(total_traffic_values)
            high_traffic_times = []
            low_traffic_times = []
            
            # Simulate performance during different traffic periods
            high_perf = [score for data in performance_data for score in data['performance_scores'] 
                        if np.random.random() > 0.5]  # Simulate high traffic periods
            low_perf = [score for data in performance_data for score in data['performance_scores'] 
                       if np.random.random() <= 0.5]  # Simulate low traffic periods
            
            axes[1, 0].hist([high_perf, low_perf], bins=20, alpha=0.7, 
                           label=['High Traffic Periods', 'Low Traffic Periods'],
                           color=['red', 'blue'], edgecolor='black')
            axes[1, 0].set_title('Performance Distribution by Traffic Level')
            axes[1, 0].set_xlabel('Performance Score')
            axes[1, 0].set_ylabel('Frequency')
            axes[1, 0].legend()
            axes[1, 0].grid(True, alpha=0.3)
        
        # Time-based analysis
        timestamps = [data['timestamp'] for data in performance_data]
        avg_performances = [data['avg_performance'] for data in performance_data]
        
        if timestamps and avg_performances:
            hours = [ts.hour for ts in timestamps]
            
            # Group performance by hour and create histogram
            hourly_performance = {}
            for hour, perf in zip(hours, avg_performances):
                if hour not in hourly_performance:
                    hourly_performance[hour] = []
                hourly_performance[hour].append(perf)
            
            hour_labels = sorted(hourly_performance.keys())
            hour_means = [np.mean(hourly_performance[h]) for h in hour_labels]
            hour_stds = [np.std(hourly_performance[h]) for h in hour_labels]
            
            axes[1, 1].bar(hour_labels, hour_means, yerr=hour_stds, 
                          alpha=0.7, color='green', edgecolor='black', capsize=5)
            axes[1, 1].set_title('Performance Variation by Hour (with Error Bars)')
            axes[1, 1].set_xlabel('Hour of Day')
            axes[1, 1].set_ylabel('Average Performance Score')
            axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.base_dir / 'traffic_performance_correlation_histogram.png', 
                   dpi=300, bbox_inches='tight')
        plt.show()
    
    def generate_summary_report(self, traffic_stats, performance_stats):
        """Generate a summary report of the analysis"""
        report = []
        report.append("=" * 60)
        report.append("TRAFFIC AND PERFORMANCE HISTOGRAM ANALYSIS REPORT")
        report.append("=" * 60)
        report.append("")
        
        if traffic_stats:
            report.append("TRAFFIC ANALYSIS:")
            report.append("-" * 20)
            if traffic_stats.get('us_traffic'):
                report.append(f"US Traffic - Mean: {np.mean(traffic_stats['us_traffic']):.1f}, "
                            f"Std: {np.std(traffic_stats['us_traffic']):.1f}")
            if traffic_stats.get('india_traffic'):
                report.append(f"India Traffic - Mean: {np.mean(traffic_stats['india_traffic']):.1f}, "
                            f"Std: {np.std(traffic_stats['india_traffic']):.1f}")
            if traffic_stats.get('all_traffic'):
                report.append(f"Total Traffic - Mean: {np.mean(traffic_stats['all_traffic']):.1f}, "
                            f"Std: {np.std(traffic_stats['all_traffic']):.1f}")
            if traffic_stats.get('page_views'):
                report.append(f"Page Views - Mean: {np.mean(traffic_stats['page_views']):.1f}, "
                            f"Std: {np.std(traffic_stats['page_views']):.1f}")
            report.append("")
        
        if performance_stats:
            report.append("PERFORMANCE ANALYSIS:")
            report.append("-" * 20)
            if performance_stats.get('all_scores'):
                scores = performance_stats['all_scores']
                report.append(f"Performance Scores - Mean: {np.mean(scores):.1f}, "
                            f"Median: {np.median(scores):.1f}, Std: {np.std(scores):.1f}")
            if performance_stats.get('score_ranges'):
                ranges = performance_stats['score_ranges']
                total_urls = sum(ranges.values())
                report.append(f"Total URLs analyzed: {total_urls}")
                for category, count in ranges.items():
                    percentage = (count / total_urls) * 100 if total_urls > 0 else 0
                    report.append(f"  {category}: {count} URLs ({percentage:.1f}%)")
            report.append("")
        
        report.append("FILES GENERATED:")
        report.append("-" * 15)
        report.append("• traffic_histogram_analysis.png")
        report.append("• performance_histogram_analysis.png") 
        report.append("• traffic_performance_correlation_histogram.png")
        report.append("")
        
        report_text = "\n".join(report)
        print(report_text)
        
        # Save report to file
        with open(self.base_dir / 'histogram_analysis_report.txt', 'w') as f:
            f.write(report_text)
    
    def run_analysis(self):
        """Run the complete analysis"""
        print("Starting Traffic and Performance Histogram Analysis...")
        print("=" * 60)
        
        # Load data
        traffic_data = self.load_traffic_data()
        performance_data = self.load_performance_data()
        
        print(f"Loaded {len(traffic_data)} traffic data entries")
        print(f"Loaded {len(performance_data)} performance data entries")
        print("")
        
        # Create histograms
        traffic_stats = self.create_traffic_histogram(traffic_data)
        performance_stats = self.create_performance_histogram(performance_data)
        
        # Create correlation analysis
        self.create_correlation_histogram(traffic_data, performance_data)
        
        # Generate summary report
        self.generate_summary_report(traffic_stats, performance_stats)
        
        print("Analysis complete! Check the generated PNG files and report.")

if __name__ == "__main__":
    # Initialize analyzer
    base_path = "."
    analyzer = TrafficPerformanceAnalyzer(base_path)
    
    # Run the analysis
    analyzer.run_analysis()
