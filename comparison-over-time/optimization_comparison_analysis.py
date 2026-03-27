#!/usr/bin/env python3
"""
Pre vs Post Optimization Comparison Analysis
Comparing performance data before and after Directus instance optimization.
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
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class OptimizationComparisonAnalyzer:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.pre_opt_folder = self.base_dir / "pagespeed-reports"
        self.post_opt_folder = self.base_dir / "pagespeed-reports-cron" 
        self.output_folder = self.base_dir / "comparison-over-time"
        
        # Ensure output folder exists
        self.output_folder.mkdir(exist_ok=True)
        
        # Set up plotting style
        plt.style.use('default')
        sns.set_palette("Set2")
        plt.rcParams['figure.facecolor'] = 'white'
        
    def load_pre_optimization_data(self):
        """Load performance data from before optimization"""
        print("Loading pre-optimization data...")
        
        pre_data = []
        
        # Find all CSV files in subdirectories
        csv_files = glob.glob(str(self.pre_opt_folder / "*" / "*.csv"))
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                if 'Performance' in df.columns:
                    # Extract timestamp from folder name
                    folder_name = Path(csv_file).parent.name
                    timestamp_match = re.search(r'(\d+-\d+-\d+)-(\d+-\d+)-(\w+)', folder_name)
                    
                    if timestamp_match:
                        date_part = timestamp_match.group(1)
                        time_part = timestamp_match.group(2).replace('-', ':')
                        period = timestamp_match.group(3)
                        
                        # Convert to 24hr format
                        if period.lower() == 'pm' and not time_part.startswith('12'):
                            hour = int(time_part.split(':')[0]) + 12
                            time_part = f"{hour}:{time_part.split(':')[1]}"
                        
                        try:
                            timestamp = datetime.strptime(f"{date_part} {time_part}", "%d-%m-%Y %H:%M")
                        except:
                            timestamp = datetime.now()  # fallback
                    else:
                        timestamp = datetime.now()
                    
                    # Store performance data
                    for _, row in df.iterrows():
                        if pd.notna(row['Performance']):
                            pre_data.append({
                                'timestamp': timestamp,
                                'performance': row['Performance'],
                                'accessibility': row.get('Accessibility', 0),
                                'best_practices': row.get('Best Practices', 0),
                                'seo': row.get('SEO', 0),
                                'fcp': row.get('First Contentful Paint (ms)', 0),
                                'lcp': row.get('Largest Contentful Paint (ms)', 0),
                                'speed_index': row.get('Speed Index (ms)', 0),
                                'tbt': row.get('Total Blocking Time (ms)', 0),
                                'cls': row.get('Cumulative Layout Shift', 0),
                                'url': row.get('URL', ''),
                                'source': 'pre_optimization'
                            })
            except Exception as e:
                print(f"Error reading {csv_file}: {e}")
                continue
        
        return pd.DataFrame(pre_data)
    
    def load_post_optimization_data(self):
        """Load performance data from after optimization"""
        print("Loading post-optimization data...")
        
        post_data = []
        
        # Load traffic data for context
        traffic_file = self.post_opt_folder / "Realtime Tracking Automation - India & US - Jul - 2025.csv"
        traffic_summary = {}
        
        if traffic_file.exists():
            try:
                traffic_df = pd.read_csv(traffic_file)
                # Extract total traffic values
                for index, row in traffic_df.iterrows():
                    date_country = str(row['Date / Country']).strip()
                    if date_country.upper() == 'ALL':
                        for col in traffic_df.columns[1:]:
                            try:
                                val = pd.to_numeric(row[col], errors='coerce')
                                if not pd.isna(val):
                                    traffic_summary[col] = val
                            except:
                                continue
                        break
            except Exception as e:
                print(f"Error reading traffic file: {e}")
        
        # Find time-stamped folders
        folder_pattern = re.compile(r'(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2})')
        folders = [f for f in os.listdir(self.post_opt_folder) 
                  if os.path.isdir(self.post_opt_folder / f) and folder_pattern.match(f)]
        
        for folder in sorted(folders):
            match = folder_pattern.match(folder)
            if match:
                date_str, time_str = match.groups()
                
                try:
                    timestamp = datetime.strptime(f"{date_str} {time_str.replace('-', ':')}", 
                                                "%Y-%m-%d %H:%M")
                except:
                    continue
                
                # Estimate traffic for this time period
                hour = timestamp.hour
                if 6 <= hour < 12:
                    traffic_multiplier = 1.1
                elif 12 <= hour < 18:
                    traffic_multiplier = 1.3
                elif 18 <= hour < 24:
                    traffic_multiplier = 1.0
                else:
                    traffic_multiplier = 0.7
                
                base_traffic = np.mean(list(traffic_summary.values())) if traffic_summary else 500
                estimated_traffic = base_traffic * traffic_multiplier
                
                csv_files = glob.glob(str(self.post_opt_folder / folder / "*.csv"))
                
                for csv_file in csv_files:
                    try:
                        df = pd.read_csv(csv_file)
                        if 'Performance' in df.columns:
                            for _, row in df.iterrows():
                                if pd.notna(row['Performance']):
                                    post_data.append({
                                        'timestamp': timestamp,
                                        'performance': row['Performance'],
                                        'accessibility': row.get('Accessibility', 0),
                                        'best_practices': row.get('Best Practices', 0),
                                        'seo': row.get('SEO', 0),
                                        'fcp': row.get('First Contentful Paint (ms)', 0),
                                        'lcp': row.get('Largest Contentful Paint (ms)', 0),
                                        'speed_index': row.get('Speed Index (ms)', 0),
                                        'tbt': row.get('Total Blocking Time (ms)', 0),
                                        'cls': row.get('Cumulative Layout Shift', 0),
                                        'url': row.get('URL', ''),
                                        'traffic': estimated_traffic,
                                        'source': 'post_optimization'
                                    })
                    except Exception as e:
                        continue
        
        return pd.DataFrame(post_data)
    
    def create_performance_comparison_charts(self, pre_data, post_data):
        """Create comprehensive performance comparison charts"""
        
        # Chart 1: Overall Performance Comparison
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Performance Comparison: Before vs After Optimization', 
                     fontsize=18, fontweight='bold', y=0.98)
        
        # Performance score comparison with small bucket sizes
        ax1.hist([pre_data['performance'], post_data['performance']], 
                bins=20, alpha=0.7, label=['Before Optimization', 'After Optimization'],
                color=['red', 'green'], edgecolor='black')
        
        ax1.axvline(pre_data['performance'].mean(), color='red', linestyle='--', linewidth=2,
                   label=f'Before Mean: {pre_data["performance"].mean():.1f}')
        ax1.axvline(post_data['performance'].mean(), color='green', linestyle='--', linewidth=2,
                   label=f'After Mean: {post_data["performance"].mean():.1f}')
        
        ax1.set_title('Performance Score Distribution (20 bins)', fontweight='bold')
        ax1.set_xlabel('Performance Score')
        ax1.set_ylabel('Frequency')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Box plot comparison
        ax2.boxplot([pre_data['performance'], post_data['performance']], 
                   tick_labels=['Before\nOptimization', 'After\nOptimization'],
                   patch_artist=True,
                   boxprops=dict(facecolor='lightblue', alpha=0.7),
                   medianprops=dict(color='red', linewidth=2))
        
        ax2.set_title('Performance Score Comparison', fontweight='bold')
        ax2.set_ylabel('Performance Score')
        ax2.grid(True, alpha=0.3)
        
        # Statistical significance test
        stat, p_value = stats.mannwhitneyu(pre_data['performance'], post_data['performance'], 
                                         alternative='two-sided')
        
        improvement = post_data['performance'].mean() - pre_data['performance'].mean()
        
        stats_text = f'Statistical Test:\np-value: {p_value:.4f}\n'
        stats_text += f'Improvement: {improvement:.1f} points\n'
        if p_value < 0.05:
            stats_text += 'Significant difference!'
        else:
            stats_text += 'No significant difference'
        
        ax2.text(0.02, 0.98, stats_text, transform=ax2.transAxes, 
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
                verticalalignment='top')
        
        # Performance categories comparison
        categories = ['Poor\n(0-49)', 'Needs Improvement\n(50-89)', 'Good\n(90-100)']
        
        pre_poor = len(pre_data[pre_data['performance'] < 50])
        pre_needs = len(pre_data[(pre_data['performance'] >= 50) & (pre_data['performance'] < 90)])
        pre_good = len(pre_data[pre_data['performance'] >= 90])
        
        post_poor = len(post_data[post_data['performance'] < 50])
        post_needs = len(post_data[(post_data['performance'] >= 50) & (post_data['performance'] < 90)])
        post_good = len(post_data[post_data['performance'] >= 90])
        
        pre_total = len(pre_data)
        post_total = len(post_data)
        
        pre_percentages = [pre_poor/pre_total*100, pre_needs/pre_total*100, pre_good/pre_total*100]
        post_percentages = [post_poor/post_total*100, post_needs/post_total*100, post_good/post_total*100]
        
        x = np.arange(len(categories))
        width = 0.35
        
        bars1 = ax3.bar(x - width/2, pre_percentages, width, label='Before', 
                       color=['darkred', 'orange', 'lightgreen'], alpha=0.7)
        bars2 = ax3.bar(x + width/2, post_percentages, width, label='After',
                       color=['red', 'gold', 'green'], alpha=0.7)
        
        ax3.set_title('Performance Categories Comparison', fontweight='bold')
        ax3.set_ylabel('Percentage of URLs')
        ax3.set_xticks(x)
        ax3.set_xticklabels(categories)
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Add percentage labels
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                        f'{height:.1f}%', ha='center', va='bottom', fontsize=8)
        
        # Time series comparison if timestamps are available
        if 'timestamp' in pre_data.columns and 'timestamp' in post_data.columns:
            pre_daily = pre_data.groupby(pre_data['timestamp'].dt.date)['performance'].mean()
            post_daily = post_data.groupby(post_data['timestamp'].dt.date)['performance'].mean()
            
            ax4.plot(pre_daily.index, pre_daily.values, 'ro-', label='Before Optimization', 
                    markersize=6, linewidth=2)
            ax4.plot(post_daily.index, post_daily.values, 'go-', label='After Optimization',
                    markersize=6, linewidth=2)
            
            ax4.set_title('Performance Trend Over Time', fontweight='bold')
            ax4.set_xlabel('Date')
            ax4.set_ylabel('Average Performance Score')
            ax4.legend()
            ax4.grid(True, alpha=0.3)
            plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        plt.savefig(self.output_folder / 'performance_comparison_overview.png', 
                   dpi=300, bbox_inches='tight')
        plt.show()
    
    def create_detailed_metrics_comparison(self, pre_data, post_data):
        """Create detailed Core Web Vitals comparison with varying bucket sizes"""
        
        # Chart 2: Core Web Vitals Detailed Analysis
        fig, axes = plt.subplots(3, 2, figsize=(16, 18))
        fig.suptitle('Core Web Vitals: Detailed Comparison Analysis', 
                     fontsize=18, fontweight='bold', y=0.98)
        
        metrics = [
            ('fcp', 'First Contentful Paint (ms)', 15),
            ('lcp', 'Largest Contentful Paint (ms)', 12),
            ('speed_index', 'Speed Index (ms)', 10),
            ('tbt', 'Total Blocking Time (ms)', 20),
            ('cls', 'Cumulative Layout Shift', 25),
            ('performance', 'Overall Performance Score', 30)
        ]
        
        for idx, (metric, title, bins) in enumerate(metrics):
            row = idx // 2
            col = idx % 2
            ax = axes[row, col]
            
            # Filter out zero values and outliers for better visualization
            pre_values = pre_data[pre_data[metric] > 0][metric]
            post_values = post_data[post_data[metric] > 0][metric]
            
            if len(pre_values) == 0 or len(post_values) == 0:
                ax.text(0.5, 0.5, f'No data available for {title}', 
                       ha='center', va='center', transform=ax.transAxes)
                ax.set_title(title, fontweight='bold')
                continue
            
            # Remove extreme outliers for better visualization
            if metric in ['fcp', 'lcp', 'speed_index']:
                pre_values = pre_values[pre_values <= pre_values.quantile(0.95)]
                post_values = post_values[post_values <= post_values.quantile(0.95)]
            
            # Create histogram with specified number of bins
            ax.hist([pre_values, post_values], bins=bins, alpha=0.7,
                   label=['Before Optimization', 'After Optimization'],
                   color=['red', 'green'], edgecolor='black', density=True)
            
            # Add mean lines
            ax.axvline(pre_values.mean(), color='red', linestyle='--', linewidth=2,
                      label=f'Before Mean: {pre_values.mean():.1f}')
            ax.axvline(post_values.mean(), color='green', linestyle='--', linewidth=2,
                      label=f'After Mean: {post_values.mean():.1f}')
            
            # Add performance thresholds if applicable
            if metric == 'fcp':
                ax.axvline(1800, color='orange', linestyle=':', alpha=0.8, label='Good: <1.8s')
            elif metric == 'lcp':
                ax.axvline(2500, color='orange', linestyle=':', alpha=0.8, label='Good: <2.5s')
            elif metric == 'tbt':
                ax.axvline(200, color='orange', linestyle=':', alpha=0.8, label='Good: <200ms')
            elif metric == 'cls':
                ax.axvline(0.1, color='orange', linestyle=':', alpha=0.8, label='Good: <0.1')
            
            ax.set_title(f'{title} ({bins} bins)', fontweight='bold')
            ax.set_xlabel(title.split('(')[1].rstrip(')') if '(' in title else 'Score')
            ax.set_ylabel('Density')
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)
            
            # Add improvement percentage
            improvement = ((post_values.mean() - pre_values.mean()) / pre_values.mean()) * 100
            color = 'green' if improvement > 0 and metric == 'performance' else 'red' if improvement > 0 else 'green'
            if metric in ['fcp', 'lcp', 'speed_index', 'tbt', 'cls']:
                color = 'green' if improvement < 0 else 'red'  # Lower is better for these metrics
            
            ax.text(0.02, 0.98, f'Change: {improvement:+.1f}%', 
                   transform=ax.transAxes, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor=color, alpha=0.3))
        
        plt.tight_layout()
        plt.savefig(self.output_folder / 'core_web_vitals_detailed_comparison.png', 
                   dpi=300, bbox_inches='tight')
        plt.show()
    
    def create_traffic_performance_correlation(self, post_data):
        """Create traffic vs performance correlation for post-optimization data"""
        
        if 'traffic' not in post_data.columns:
            print("No traffic data available for correlation analysis")
            return
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Post-Optimization: Traffic vs Performance Analysis', 
                     fontsize=18, fontweight='bold', y=0.98)
        
        traffic = post_data['traffic']
        performance = post_data['performance']
        
        # Scatter plot with different bucket sizes
        ax1.scatter(traffic, performance, alpha=0.6, s=50, c='blue', edgecolors='white')
        
        # Add trend line
        z = np.polyfit(traffic, performance, 1)
        p = np.poly1d(z)
        x_trend = np.linspace(traffic.min(), traffic.max(), 100)
        ax1.plot(x_trend, p(x_trend), "red", linewidth=2, alpha=0.8)
        
        correlation = np.corrcoef(traffic, performance)[0, 1]
        ax1.text(0.05, 0.95, f'Correlation: {correlation:.3f}', 
                transform=ax1.transAxes, 
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        ax1.set_title('Traffic vs Performance Scatter Plot', fontweight='bold')
        ax1.set_xlabel('Estimated Traffic Count')
        ax1.set_ylabel('Performance Score')
        ax1.grid(True, alpha=0.3)
        
        # Traffic level analysis with small buckets
        traffic_q1 = traffic.quantile(0.33)
        traffic_q2 = traffic.quantile(0.67)
        
        low_traffic = performance[traffic <= traffic_q1]
        med_traffic = performance[(traffic > traffic_q1) & (traffic <= traffic_q2)]
        high_traffic = performance[traffic > traffic_q2]
        
        # Histogram with small bucket size for traffic levels
        ax2.hist([low_traffic, med_traffic, high_traffic], bins=15, alpha=0.7,
                label=[f'Low Traffic (≤{traffic_q1:.0f})', 
                      f'Medium Traffic ({traffic_q1:.0f}-{traffic_q2:.0f})',
                      f'High Traffic (>{traffic_q2:.0f})'],
                color=['lightgreen', 'gold', 'lightcoral'], edgecolor='black')
        
        ax2.set_title('Performance Distribution by Traffic Level (15 bins)', fontweight='bold')
        ax2.set_xlabel('Performance Score')
        ax2.set_ylabel('Frequency')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 2D Histogram with increased bins for detailed view
        hist, xedges, yedges = np.histogram2d(traffic, performance, bins=25)
        im = ax3.imshow(hist.T, origin='lower', cmap='YlOrRd', aspect='auto',
                       extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]])
        ax3.set_title('Traffic vs Performance Density (25x25 bins)', fontweight='bold')
        ax3.set_xlabel('Traffic Count')
        ax3.set_ylabel('Performance Score')
        
        cbar = plt.colorbar(im, ax=ax3)
        cbar.set_label('Frequency')
        
        # Hourly performance analysis
        hourly_perf = post_data.groupby(post_data['timestamp'].dt.hour)['performance'].agg(['mean', 'std'])
        hours = hourly_perf.index
        means = hourly_perf['mean']
        stds = hourly_perf['std'].fillna(0)
        
        bars = ax4.bar(hours, means, yerr=stds, alpha=0.7, 
                      color='skyblue', edgecolor='black', capsize=3)
        ax4.set_title('Average Performance by Hour of Day', fontweight='bold')
        ax4.set_xlabel('Hour of Day')
        ax4.set_ylabel('Performance Score')
        ax4.set_xticks(range(0, 24, 2))
        ax4.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar, mean_val in zip(bars, means):
            if not np.isnan(mean_val):
                ax4.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1,
                        f'{mean_val:.0f}', ha='center', va='bottom', fontsize=8)
        
        plt.tight_layout()
        plt.savefig(self.output_folder / 'traffic_performance_correlation_post_opt.png', 
                   dpi=300, bbox_inches='tight')
        plt.show()
    
    def create_progressive_bucket_analysis(self, pre_data, post_data):
        """Create charts with progressively increasing bucket sizes"""
        
        bucket_sizes = [10, 20, 30, 40]
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Performance Distribution: Progressive Bucket Size Analysis', 
                     fontsize=18, fontweight='bold', y=0.98)
        
        for idx, bins in enumerate(bucket_sizes):
            row = idx // 2
            col = idx % 2
            ax = axes[row, col]
            
            # Create histogram with current bucket size
            ax.hist([pre_data['performance'], post_data['performance']], 
                   bins=bins, alpha=0.7, 
                   label=['Before Optimization', 'After Optimization'],
                   color=['red', 'green'], edgecolor='black')
            
            # Add statistics
            pre_mean = pre_data['performance'].mean()
            post_mean = post_data['performance'].mean()
            
            ax.axvline(pre_mean, color='red', linestyle='--', linewidth=2,
                      label=f'Before Mean: {pre_mean:.1f}')
            ax.axvline(post_mean, color='green', linestyle='--', linewidth=2,
                      label=f'After Mean: {post_mean:.1f}')
            
            ax.set_title(f'Performance Distribution ({bins} buckets)', fontweight='bold')
            ax.set_xlabel('Performance Score')
            ax.set_ylabel('Frequency')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Add improvement text
            improvement = post_mean - pre_mean
            ax.text(0.02, 0.98, f'Improvement: {improvement:+.1f}', 
                   transform=ax.transAxes, verticalalignment='top',
                   bbox=dict(boxstyle='round', 
                           facecolor='lightgreen' if improvement > 0 else 'lightcoral', 
                           alpha=0.8))
        
        plt.tight_layout()
        plt.savefig(self.output_folder / 'progressive_bucket_analysis.png', 
                   dpi=300, bbox_inches='tight')
        plt.show()
    
    def generate_comprehensive_report(self, pre_data, post_data):
        """Generate comprehensive comparison report"""
        
        report = []
        report.append("=" * 80)
        report.append("OPTIMIZATION IMPACT ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Data summary
        report.append("DATA SUMMARY:")
        report.append("-" * 15)
        report.append(f"Pre-optimization samples: {len(pre_data)}")
        report.append(f"Post-optimization samples: {len(post_data)}")
        report.append("")
        
        # Performance analysis
        pre_perf_mean = pre_data['performance'].mean()
        post_perf_mean = post_data['performance'].mean()
        improvement = post_perf_mean - pre_perf_mean
        improvement_pct = (improvement / pre_perf_mean) * 100
        
        report.append("PERFORMANCE ANALYSIS:")
        report.append("-" * 22)
        report.append(f"Before optimization: {pre_perf_mean:.2f}")
        report.append(f"After optimization:  {post_perf_mean:.2f}")
        report.append(f"Improvement:         {improvement:+.2f} points ({improvement_pct:+.1f}%)")
        
        # Statistical significance
        try:
            stat, p_value = stats.mannwhitneyu(pre_data['performance'], post_data['performance'])
            report.append(f"Statistical significance: p = {p_value:.4f}")
            if p_value < 0.05:
                report.append("Result: STATISTICALLY SIGNIFICANT improvement")
            else:
                report.append("Result: No statistically significant difference")
        except:
            report.append("Statistical test: Could not be performed")
        
        report.append("")
        
        # Core Web Vitals comparison
        report.append("CORE WEB VITALS ANALYSIS:")
        report.append("-" * 26)
        
        metrics = [
            ('fcp', 'First Contentful Paint'),
            ('lcp', 'Largest Contentful Paint'), 
            ('speed_index', 'Speed Index'),
            ('tbt', 'Total Blocking Time'),
            ('cls', 'Cumulative Layout Shift')
        ]
        
        for metric, name in metrics:
            if metric in pre_data.columns and metric in post_data.columns:
                pre_values = pre_data[pre_data[metric] > 0][metric]
                post_values = post_data[post_data[metric] > 0][metric]
                
                if len(pre_values) > 0 and len(post_values) > 0:
                    pre_mean = pre_values.mean()
                    post_mean = post_values.mean()
                    change = post_mean - pre_mean
                    change_pct = (change / pre_mean) * 100
                    
                    report.append(f"{name}:")
                    report.append(f"  Before: {pre_mean:.1f}")
                    report.append(f"  After:  {post_mean:.1f}")
                    report.append(f"  Change: {change:+.1f} ({change_pct:+.1f}%)")
                    report.append("")
        
        # Performance categories
        report.append("PERFORMANCE CATEGORIES:")
        report.append("-" * 23)
        
        def get_category_stats(data):
            poor = len(data[data['performance'] < 50])
            needs = len(data[(data['performance'] >= 50) & (data['performance'] < 90)])
            good = len(data[data['performance'] >= 90])
            total = len(data)
            return poor, needs, good, total
        
        pre_poor, pre_needs, pre_good, pre_total = get_category_stats(pre_data)
        post_poor, post_needs, post_good, post_total = get_category_stats(post_data)
        
        report.append("Before Optimization:")
        report.append(f"  Poor (0-49):           {pre_poor} ({pre_poor/pre_total*100:.1f}%)")
        report.append(f"  Needs Improvement:     {pre_needs} ({pre_needs/pre_total*100:.1f}%)")
        report.append(f"  Good (90-100):         {pre_good} ({pre_good/pre_total*100:.1f}%)")
        report.append("")
        report.append("After Optimization:")
        report.append(f"  Poor (0-49):           {post_poor} ({post_poor/post_total*100:.1f}%)")
        report.append(f"  Needs Improvement:     {post_needs} ({post_needs/post_total*100:.1f}%)")
        report.append(f"  Good (90-100):         {post_good} ({post_good/post_total*100:.1f}%)")
        report.append("")
        
        # Key insights
        report.append("KEY INSIGHTS:")
        report.append("-" * 13)
        
        if improvement > 5:
            report.append("• SIGNIFICANT performance improvement achieved")
        elif improvement > 0:
            report.append("• Moderate performance improvement observed")
        else:
            report.append("• Performance improvement not detected")
        
        good_improvement = (post_good/post_total) - (pre_good/pre_total)
        if good_improvement > 0.1:
            report.append(f"• Substantial increase in 'Good' performance URLs (+{good_improvement*100:.1f}%)")
        
        if 'traffic' in post_data.columns:
            correlation = np.corrcoef(post_data['traffic'], post_data['performance'])[0, 1]
            if correlation < -0.3:
                report.append("• Strong negative correlation between traffic and performance")
                report.append("  → Consider further server optimization for high-traffic periods")
            elif abs(correlation) < 0.2:
                report.append("• Performance remains stable across different traffic levels")
                report.append("  → Good server capacity management")
        
        report.append("")
        report.append("GENERATED CHARTS:")
        report.append("-" * 17)
        report.append("• performance_comparison_overview.png")
        report.append("• core_web_vitals_detailed_comparison.png")
        report.append("• traffic_performance_correlation_post_opt.png")
        report.append("• progressive_bucket_analysis.png")
        
        report_text = "\n".join(report)
        print(report_text)
        
        # Save report
        with open(self.output_folder / 'optimization_impact_report.txt', 'w') as f:
            f.write(report_text)
        
        return report_text
    
    def run_complete_analysis(self):
        """Run the complete optimization comparison analysis"""
        print("Starting Optimization Impact Analysis...")
        print("=" * 60)
        
        # Load data
        pre_data = self.load_pre_optimization_data()
        post_data = self.load_post_optimization_data()
        
        if pre_data.empty:
            print("ERROR: No pre-optimization data found!")
            return
        
        if post_data.empty:
            print("ERROR: No post-optimization data found!")
            return
        
        print(f"Pre-optimization data: {len(pre_data)} samples")
        print(f"Post-optimization data: {len(post_data)} samples")
        print("")
        
        # Create all comparison charts
        print("Creating performance comparison charts...")
        self.create_performance_comparison_charts(pre_data, post_data)
        
        print("Creating detailed metrics comparison...")
        self.create_detailed_metrics_comparison(pre_data, post_data)
        
        print("Creating traffic-performance correlation...")
        self.create_traffic_performance_correlation(post_data)
        
        print("Creating progressive bucket analysis...")
        self.create_progressive_bucket_analysis(pre_data, post_data)
        
        # Generate comprehensive report
        print("Generating comprehensive report...")
        self.generate_comprehensive_report(pre_data, post_data)
        
        print("\n" + "="*60)
        print("ANALYSIS COMPLETE!")
        print("="*60)
        print(f"All charts and reports saved to: {self.output_folder}")
        print("\nGenerated files:")
        for file in self.output_folder.glob("*.png"):
            print(f"  📊 {file.name}")
        for file in self.output_folder.glob("*.txt"):
            print(f"  📄 {file.name}")

if __name__ == "__main__":
    # Run the complete analysis
    analyzer = OptimizationComparisonAnalyzer(".")
    analyzer.run_complete_analysis()
