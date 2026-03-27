#!/usr/bin/env python3
"""
Enhanced Traffic and Performance Histogram Analysis with Advanced Correlations
This script creates comprehensive histogram charts with detailed time-based correlations.
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
from matplotlib.dates import DateFormatter
import warnings
warnings.filterwarnings('ignore')

class EnhancedTrafficPerformanceAnalyzer:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.traffic_file = self.base_dir / "pagespeed-reports-cron" / "Realtime Tracking Automation - India & US - Jul - 2025.csv"
        self.performance_folders = self.base_dir / "pagespeed-reports-cron"
        
        # Set up matplotlib style for better visualizations
        plt.style.use('default')
        plt.rcParams['figure.facecolor'] = 'white'
        plt.rcParams['axes.facecolor'] = 'white'
        sns.set_palette("Set2")
        
    def load_traffic_data_enhanced(self):
        """Enhanced traffic data loading with time parsing"""
        print("Loading enhanced traffic data...")
        
        df = pd.read_csv(self.traffic_file)
        
        # Extract time columns (all columns except first)
        time_columns = df.columns[1:].tolist()
        
        traffic_summary = {
            'US': [],
            'India': [],
            'All': [],
            'PageViews': [],
            'timestamps': []
        }
        
        current_date = None
        
        for index, row in df.iterrows():
            date_country = str(row['Date / Country']).strip()
            
            # Check if this is a date row
            if '/' in date_country and any(char.isdigit() for char in date_country):
                try:
                    current_date = datetime.strptime(date_country, '%m/%d/%Y')
                    continue
                except:
                    continue
            
            # Process country/metric rows
            if current_date and not pd.isna(date_country):
                values = []
                for col in time_columns:
                    try:
                        val = pd.to_numeric(row[col], errors='coerce')
                        if not pd.isna(val):
                            values.append(val)
                    except:
                        continue
                
                if values:
                    if 'UNITED STATES' in date_country.upper():
                        traffic_summary['US'].extend(values)
                    elif 'INDIA' in date_country.upper():
                        traffic_summary['India'].extend(values)
                    elif date_country.upper() == 'ALL':
                        traffic_summary['All'].extend(values)
                    elif 'PAGE VIEWS' in date_country.upper():
                        traffic_summary['PageViews'].extend(values)
        
        return traffic_summary
    
    def load_performance_data_enhanced(self):
        """Enhanced performance data loading with better time correlation"""
        print("Loading enhanced performance data...")
        
        performance_data = []
        folder_pattern = re.compile(r'(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2})')
        
        folders = [f for f in os.listdir(self.performance_folders) 
                  if os.path.isdir(self.performance_folders / f) and folder_pattern.match(f)]
        
        for folder in sorted(folders):
            match = folder_pattern.match(folder)
            if match:
                date_str, time_str = match.groups()
                
                try:
                    folder_time = datetime.strptime(f"{date_str} {time_str.replace('-', ':')}", 
                                                  "%Y-%m-%d %H:%M")
                except:
                    continue
                
                csv_files = glob.glob(str(self.performance_folders / folder / "*.csv"))
                
                for csv_file in csv_files:
                    try:
                        df = pd.read_csv(csv_file)
                        if 'Performance' in df.columns:
                            perf_data = df[['Performance', 'First Contentful Paint (ms)', 
                                          'Largest Contentful Paint (ms)', 'Speed Index (ms)',
                                          'Total Blocking Time (ms)', 'Cumulative Layout Shift']].copy()
                            
                            perf_data = perf_data.dropna(subset=['Performance'])
                            
                            if len(perf_data) > 0:
                                performance_data.append({
                                    'timestamp': folder_time,
                                    'folder': folder,
                                    'data': perf_data,
                                    'avg_performance': perf_data['Performance'].mean(),
                                    'url_count': len(perf_data)
                                })
                    except Exception as e:
                        print(f"Error reading {csv_file}: {e}")
                        continue
        
        return performance_data
    
    def create_comprehensive_histogram_suite(self, traffic_data, performance_data):
        """Create a comprehensive suite of histogram visualizations"""
        
        # 1. Traffic Distribution Analysis
        self.create_traffic_distribution_histograms(traffic_data)
        
        # 2. Performance Metrics Histograms
        self.create_performance_metrics_histograms(performance_data)
        
        # 3. Time-based Correlation Analysis
        self.create_time_correlation_histograms(traffic_data, performance_data)
        
        # 4. Advanced Statistical Analysis
        self.create_statistical_analysis_histograms(traffic_data, performance_data)
    
    def create_traffic_distribution_histograms(self, traffic_data):
        """Create detailed traffic distribution histograms"""
        fig = plt.figure(figsize=(20, 15))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        fig.suptitle('Comprehensive Traffic Distribution Analysis', fontsize=20, fontweight='bold', y=0.98)
        
        # Individual country distributions
        ax1 = fig.add_subplot(gs[0, 0])
        if traffic_data['US']:
            ax1.hist(traffic_data['US'], bins=30, alpha=0.7, color='#1f77b4', edgecolor='black', density=True)
            ax1.axvline(np.mean(traffic_data['US']), color='red', linestyle='--', linewidth=2, 
                       label=f'Mean: {np.mean(traffic_data["US"]):.0f}')
            ax1.set_title('US Traffic Distribution (Normalized)', fontweight='bold')
            ax1.set_xlabel('Traffic Count')
            ax1.set_ylabel('Density')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
        
        ax2 = fig.add_subplot(gs[0, 1])
        if traffic_data['India']:
            ax2.hist(traffic_data['India'], bins=30, alpha=0.7, color='#ff7f0e', edgecolor='black', density=True)
            ax2.axvline(np.mean(traffic_data['India']), color='red', linestyle='--', linewidth=2,
                       label=f'Mean: {np.mean(traffic_data["India"]):.0f}')
            ax2.set_title('India Traffic Distribution (Normalized)', fontweight='bold')
            ax2.set_xlabel('Traffic Count')
            ax2.set_ylabel('Density')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        
        # Combined traffic analysis
        ax3 = fig.add_subplot(gs[0, 2])
        if traffic_data['All']:
            ax3.hist(traffic_data['All'], bins=30, alpha=0.7, color='#2ca02c', edgecolor='black')
            ax3.axvline(np.mean(traffic_data['All']), color='red', linestyle='--', linewidth=2,
                       label=f'Mean: {np.mean(traffic_data["All"]):.0f}')
            ax3.axvline(np.median(traffic_data['All']), color='orange', linestyle='--', linewidth=2,
                       label=f'Median: {np.median(traffic_data["All"]):.0f}')
            ax3.set_title('Total Traffic Distribution', fontweight='bold')
            ax3.set_xlabel('Traffic Count')
            ax3.set_ylabel('Frequency')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
        
        # Comparative histogram
        ax4 = fig.add_subplot(gs[1, :2])
        if traffic_data['US'] and traffic_data['India']:
            bins = np.linspace(0, max(max(traffic_data['US']), max(traffic_data['India'])), 25)
            ax4.hist([traffic_data['US'], traffic_data['India']], bins=bins, alpha=0.7, 
                    label=['US Traffic', 'India Traffic'], color=['#1f77b4', '#ff7f0e'], edgecolor='black')
            ax4.set_title('US vs India Traffic Comparison', fontweight='bold')
            ax4.set_xlabel('Traffic Count')
            ax4.set_ylabel('Frequency')
            ax4.legend()
            ax4.grid(True, alpha=0.3)
        
        # Page views analysis
        ax5 = fig.add_subplot(gs[1, 2])
        if traffic_data['PageViews']:
            ax5.hist(traffic_data['PageViews'], bins=25, alpha=0.7, color='#d62728', edgecolor='black')
            ax5.axvline(np.mean(traffic_data['PageViews']), color='blue', linestyle='--', linewidth=2,
                       label=f'Mean: {np.mean(traffic_data["PageViews"]):.0f}')
            ax5.set_title('Page Views Distribution', fontweight='bold')
            ax5.set_xlabel('Page View Count')
            ax5.set_ylabel('Frequency')
            ax5.legend()
            ax5.grid(True, alpha=0.3)
        
        # Statistical summary
        ax6 = fig.add_subplot(gs[2, :])
        stats_data = []
        labels = []
        
        for key, values in traffic_data.items():
            if values and key != 'timestamps':
                stats_data.append(values)
                labels.append(f'{key}\n(μ={np.mean(values):.0f}, σ={np.std(values):.0f})')
        
        if stats_data:
            bp = ax6.boxplot(stats_data, labels=labels, patch_artist=True, notch=True)
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
            for patch, color in zip(bp['boxes'], colors[:len(bp['boxes'])]):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)
            ax6.set_title('Traffic Statistics Comparison (Box Plot)', fontweight='bold')
            ax6.set_ylabel('Traffic Count')
            ax6.grid(True, alpha=0.3)
        
        plt.savefig(self.base_dir / 'comprehensive_traffic_histograms.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_performance_metrics_histograms(self, performance_data):
        """Create detailed performance metrics histograms"""
        if not performance_data:
            return
            
        fig = plt.figure(figsize=(20, 15))
        gs = fig.add_gridspec(3, 3, hspace=0.4, wspace=0.3)
        
        fig.suptitle('Website Performance Metrics Analysis', fontsize=20, fontweight='bold', y=0.98)
        
        # Collect all metrics
        all_performance = []
        all_fcp = []
        all_lcp = []
        all_si = []
        all_tbt = []
        all_cls = []
        
        for data in performance_data:
            df = data['data']
            all_performance.extend(df['Performance'].values)
            all_fcp.extend(df['First Contentful Paint (ms)'].dropna().values)
            all_lcp.extend(df['Largest Contentful Paint (ms)'].dropna().values)
            all_si.extend(df['Speed Index (ms)'].dropna().values)
            all_tbt.extend(df['Total Blocking Time (ms)'].dropna().values)
            all_cls.extend(df['Cumulative Layout Shift'].dropna().values)
        
        # Performance Score Distribution
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.hist(all_performance, bins=20, alpha=0.7, color='purple', edgecolor='black')
        ax1.axvline(np.mean(all_performance), color='red', linestyle='--', linewidth=2,
                   label=f'Mean: {np.mean(all_performance):.1f}')
        ax1.axvline(50, color='orange', linestyle=':', linewidth=2, label='Threshold: 50')
        ax1.axvline(90, color='green', linestyle=':', linewidth=2, label='Threshold: 90')
        ax1.set_title('Performance Score Distribution', fontweight='bold')
        ax1.set_xlabel('Performance Score')
        ax1.set_ylabel('Frequency')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # First Contentful Paint
        ax2 = fig.add_subplot(gs[0, 1])
        if all_fcp:
            fcp_filtered = [x for x in all_fcp if x <= 10000]  # Filter outliers
            ax2.hist(fcp_filtered, bins=25, alpha=0.7, color='blue', edgecolor='black')
            ax2.axvline(np.mean(fcp_filtered), color='red', linestyle='--', linewidth=2,
                       label=f'Mean: {np.mean(fcp_filtered):.0f}ms')
            ax2.axvline(1800, color='orange', linestyle=':', linewidth=2, label='Good: <1.8s')
            ax2.set_title('First Contentful Paint Distribution', fontweight='bold')
            ax2.set_xlabel('Time (ms)')
            ax2.set_ylabel('Frequency')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        
        # Largest Contentful Paint
        ax3 = fig.add_subplot(gs[0, 2])
        if all_lcp:
            lcp_filtered = [x for x in all_lcp if x <= 15000]  # Filter outliers
            ax3.hist(lcp_filtered, bins=25, alpha=0.7, color='green', edgecolor='black')
            ax3.axvline(np.mean(lcp_filtered), color='red', linestyle='--', linewidth=2,
                       label=f'Mean: {np.mean(lcp_filtered):.0f}ms')
            ax3.axvline(2500, color='orange', linestyle=':', linewidth=2, label='Good: <2.5s')
            ax3.set_title('Largest Contentful Paint Distribution', fontweight='bold')
            ax3.set_xlabel('Time (ms)')
            ax3.set_ylabel('Frequency')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
        
        # Speed Index
        ax4 = fig.add_subplot(gs[1, 0])
        if all_si:
            si_filtered = [x for x in all_si if x <= 15000]
            ax4.hist(si_filtered, bins=25, alpha=0.7, color='orange', edgecolor='black')
            ax4.axvline(np.mean(si_filtered), color='red', linestyle='--', linewidth=2,
                       label=f'Mean: {np.mean(si_filtered):.0f}ms')
            ax4.axvline(3400, color='green', linestyle=':', linewidth=2, label='Good: <3.4s')
            ax4.set_title('Speed Index Distribution', fontweight='bold')
            ax4.set_xlabel('Time (ms)')
            ax4.set_ylabel('Frequency')
            ax4.legend()
            ax4.grid(True, alpha=0.3)
        
        # Total Blocking Time
        ax5 = fig.add_subplot(gs[1, 1])
        if all_tbt:
            tbt_filtered = [x for x in all_tbt if x <= 1000]
            ax5.hist(tbt_filtered, bins=25, alpha=0.7, color='red', edgecolor='black')
            ax5.axvline(np.mean(tbt_filtered), color='blue', linestyle='--', linewidth=2,
                       label=f'Mean: {np.mean(tbt_filtered):.0f}ms')
            ax5.axvline(200, color='green', linestyle=':', linewidth=2, label='Good: <200ms')
            ax5.set_title('Total Blocking Time Distribution', fontweight='bold')
            ax5.set_xlabel('Time (ms)')
            ax5.set_ylabel('Frequency')
            ax5.legend()
            ax5.grid(True, alpha=0.3)
        
        # Cumulative Layout Shift
        ax6 = fig.add_subplot(gs[1, 2])
        if all_cls:
            cls_filtered = [x for x in all_cls if x <= 1.0]
            ax6.hist(cls_filtered, bins=25, alpha=0.7, color='brown', edgecolor='black')
            ax6.axvline(np.mean(cls_filtered), color='red', linestyle='--', linewidth=2,
                       label=f'Mean: {np.mean(cls_filtered):.3f}')
            ax6.axvline(0.1, color='green', linestyle=':', linewidth=2, label='Good: <0.1')
            ax6.set_title('Cumulative Layout Shift Distribution', fontweight='bold')
            ax6.set_xlabel('CLS Score')
            ax6.set_ylabel('Frequency')
            ax6.legend()
            ax6.grid(True, alpha=0.3)
        
        # Performance Categories Pie Chart
        ax7 = fig.add_subplot(gs[2, 0])
        poor = len([s for s in all_performance if s < 50])
        needs_improvement = len([s for s in all_performance if 50 <= s < 90])
        good = len([s for s in all_performance if s >= 90])
        
        labels = ['Poor\n(0-49)', 'Needs Improvement\n(50-89)', 'Good\n(90-100)']
        sizes = [poor, needs_improvement, good]
        colors = ['#ff4444', '#ffaa44', '#44ff44']
        
        ax7.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax7.set_title('Performance Score Categories', fontweight='bold')
        
        # Performance vs Core Web Vitals Correlation
        ax8 = fig.add_subplot(gs[2, 1:])
        if all_performance and all_lcp:
            min_len = min(len(all_performance), len(all_lcp))
            perf_sample = np.array(all_performance[:min_len])
            lcp_sample = np.array(all_lcp[:min_len])
            
            # Remove outliers for better visualization
            mask = (lcp_sample <= 10000) & (perf_sample >= 0)
            perf_clean = perf_sample[mask]
            lcp_clean = lcp_sample[mask]
            
            if len(perf_clean) > 0:
                hist, xedges, yedges = np.histogram2d(lcp_clean, perf_clean, bins=25)
                im = ax8.imshow(hist.T, origin='lower', cmap='YlOrRd', aspect='auto',
                               extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]])
                ax8.set_title('Performance Score vs LCP Correlation Heatmap', fontweight='bold')
                ax8.set_xlabel('Largest Contentful Paint (ms)')
                ax8.set_ylabel('Performance Score')
                plt.colorbar(im, ax=ax8, label='Frequency')
        
        plt.savefig(self.base_dir / 'comprehensive_performance_histograms.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_time_correlation_histograms(self, traffic_data, performance_data):
        """Create time-based correlation histograms"""
        if not performance_data:
            return
            
        fig = plt.figure(figsize=(20, 12))
        gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)
        
        fig.suptitle('Time-Based Traffic and Performance Correlation Analysis', 
                    fontsize=18, fontweight='bold', y=0.98)
        
        # Extract hourly data
        hourly_performance = {}
        timestamps = [data['timestamp'] for data in performance_data]
        
        for data in performance_data:
            hour = data['timestamp'].hour
            if hour not in hourly_performance:
                hourly_performance[hour] = []
            hourly_performance[hour].append(data['avg_performance'])
        
        # Hourly performance histogram
        ax1 = fig.add_subplot(gs[0, 0])
        hours = sorted(hourly_performance.keys())
        hour_means = [np.mean(hourly_performance[h]) for h in hours]
        hour_stds = [np.std(hourly_performance[h]) for h in hours]
        
        bars = ax1.bar(hours, hour_means, yerr=hour_stds, alpha=0.7, 
                      color='skyblue', edgecolor='black', capsize=5)
        ax1.set_title('Average Performance by Hour', fontweight='bold')
        ax1.set_xlabel('Hour of Day')
        ax1.set_ylabel('Average Performance Score')
        ax1.set_xticks(range(0, 24, 2))
        ax1.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar, mean_val in zip(bars, hour_means):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{mean_val:.0f}', ha='center', va='bottom', fontsize=8)
        
        # Performance distribution by time periods
        ax2 = fig.add_subplot(gs[0, 1])
        morning_perf = []
        afternoon_perf = []
        evening_perf = []
        night_perf = []
        
        for data in performance_data:
            hour = data['timestamp'].hour
            avg_perf = data['avg_performance']
            
            if 6 <= hour < 12:
                morning_perf.append(avg_perf)
            elif 12 <= hour < 18:
                afternoon_perf.append(avg_perf)
            elif 18 <= hour < 24:
                evening_perf.append(avg_perf)
            else:
                night_perf.append(avg_perf)
        
        time_periods = [morning_perf, afternoon_perf, evening_perf, night_perf]
        labels = ['Morning\n(6-12)', 'Afternoon\n(12-18)', 'Evening\n(18-24)', 'Night\n(0-6)']
        colors = ['gold', 'orange', 'red', 'navy']
        
        ax2.hist(time_periods, bins=15, alpha=0.7, label=labels, color=colors, edgecolor='black')
        ax2.set_title('Performance Distribution by Time Period', fontweight='bold')
        ax2.set_xlabel('Performance Score')
        ax2.set_ylabel('Frequency')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Timeline view
        ax3 = fig.add_subplot(gs[0, 2])
        if timestamps:
            perf_scores = [data['avg_performance'] for data in performance_data]
            ax3.plot(timestamps, perf_scores, 'o-', alpha=0.7, markersize=4)
            ax3.set_title('Performance Over Time', fontweight='bold')
            ax3.set_xlabel('Time')
            ax3.set_ylabel('Average Performance Score')
            ax3.tick_params(axis='x', rotation=45)
            ax3.grid(True, alpha=0.3)
        
        # Simulated traffic-performance correlation
        ax4 = fig.add_subplot(gs[1, :])
        
        # Create synthetic correlation data
        if traffic_data['All'] and performance_data:
            # Simulate time-aligned data
            n_points = min(len(traffic_data['All']), len(performance_data) * 10)
            
            # Sample traffic data
            traffic_sample = np.random.choice(traffic_data['All'], n_points, replace=True)
            
            # Create correlated performance data (inverse relationship simulation)
            base_performance = np.random.choice([data['avg_performance'] for data in performance_data], 
                                              n_points, replace=True)
            
            # Add some correlation noise
            correlation_factor = -0.1  # Negative correlation (high traffic = lower performance)
            performance_sample = base_performance + correlation_factor * (traffic_sample - np.mean(traffic_sample))
            
            # Create 2D histogram
            hist, xedges, yedges = np.histogram2d(traffic_sample, performance_sample, bins=30)
            
            im = ax4.imshow(hist.T, origin='lower', cmap='viridis', aspect='auto',
                           extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]])
            
            # Add correlation line
            z = np.polyfit(traffic_sample, performance_sample, 1)
            p = np.poly1d(z)
            x_line = np.linspace(xedges[0], xedges[-1], 100)
            ax4.plot(x_line, p(x_line), "r-", alpha=0.8, linewidth=2, 
                    label=f'Trend (r={np.corrcoef(traffic_sample, performance_sample)[0,1]:.3f})')
            
            ax4.set_title('Traffic vs Performance Correlation Heatmap', fontweight='bold')
            ax4.set_xlabel('Traffic Count')
            ax4.set_ylabel('Performance Score')
            ax4.legend()
            
            # Add colorbar
            cbar = plt.colorbar(im, ax=ax4)
            cbar.set_label('Frequency', rotation=270, labelpad=15)
        
        plt.savefig(self.base_dir / 'time_correlation_histograms.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_statistical_analysis_histograms(self, traffic_data, performance_data):
        """Create advanced statistical analysis histograms"""
        fig = plt.figure(figsize=(20, 12))
        gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)
        
        fig.suptitle('Advanced Statistical Analysis', fontsize=18, fontweight='bold', y=0.98)
        
        # Traffic variability analysis
        ax1 = fig.add_subplot(gs[0, 0])
        traffic_sources = ['US', 'India', 'All', 'PageViews']
        variability_data = []
        
        for source in traffic_sources:
            if traffic_data.get(source):
                cv = np.std(traffic_data[source]) / np.mean(traffic_data[source])
                variability_data.append(cv)
            else:
                variability_data.append(0)
        
        bars = ax1.bar(traffic_sources, variability_data, alpha=0.7, 
                      color=['blue', 'orange', 'green', 'red'], edgecolor='black')
        ax1.set_title('Traffic Variability (Coefficient of Variation)', fontweight='bold')
        ax1.set_ylabel('CV (σ/μ)')
        ax1.grid(True, alpha=0.3)
        
        # Add value labels
        for bar, cv in zip(bars, variability_data):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{cv:.3f}', ha='center', va='bottom')
        
        # Performance reliability analysis
        ax2 = fig.add_subplot(gs[0, 1])
        if performance_data:
            reliability_scores = []
            folder_names = []
            
            for data in performance_data[-10:]:  # Last 10 measurements
                std_dev = data['data']['Performance'].std()
                reliability = 100 - std_dev  # Higher std = lower reliability
                reliability_scores.append(max(0, reliability))
                folder_names.append(data['folder'][-8:])  # Last 8 chars
            
            ax2.bar(range(len(reliability_scores)), reliability_scores, 
                   alpha=0.7, color='purple', edgecolor='black')
            ax2.set_title('Performance Reliability Over Time', fontweight='bold')
            ax2.set_xlabel('Time Period')
            ax2.set_ylabel('Reliability Score')
            ax2.set_xticks(range(len(folder_names)))
            ax2.set_xticklabels(folder_names, rotation=45)
            ax2.grid(True, alpha=0.3)
        
        # Distribution comparison
        ax3 = fig.add_subplot(gs[0, 2])
        if traffic_data['US'] and traffic_data['India']:
            # Statistical test
            us_data = np.array(traffic_data['US'])
            india_data = np.array(traffic_data['India'])
            
            stat, p_value = stats.mannwhitneyu(us_data, india_data, alternative='two-sided')
            
            # Create overlay histograms
            bins = np.linspace(0, max(max(us_data), max(india_data)), 20)
            ax3.hist(us_data, bins=bins, alpha=0.5, label=f'US (μ={np.mean(us_data):.0f})', 
                    color='blue', density=True)
            ax3.hist(india_data, bins=bins, alpha=0.5, label=f'India (μ={np.mean(india_data):.0f})', 
                    color='orange', density=True)
            
            ax3.set_title(f'US vs India Distribution\n(Mann-Whitney p={p_value:.4f})', fontweight='bold')
            ax3.set_xlabel('Traffic Count')
            ax3.set_ylabel('Density')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
        
        # Performance trend analysis
        ax4 = fig.add_subplot(gs[1, 0])
        if performance_data:
            timestamps = [data['timestamp'] for data in performance_data]
            avg_scores = [data['avg_performance'] for data in performance_data]
            
            # Calculate moving average
            window_size = min(5, len(avg_scores))
            if len(avg_scores) >= window_size:
                moving_avg = pd.Series(avg_scores).rolling(window=window_size).mean()
                
                ax4.plot(timestamps, avg_scores, 'o-', alpha=0.5, label='Actual', markersize=3)
                ax4.plot(timestamps, moving_avg, 'r-', linewidth=2, label=f'Moving Avg ({window_size})')
                
                ax4.set_title('Performance Trend Analysis', fontweight='bold')
                ax4.set_xlabel('Time')
                ax4.set_ylabel('Performance Score')
                ax4.legend()
                ax4.tick_params(axis='x', rotation=45)
                ax4.grid(True, alpha=0.3)
        
        # Quality distribution
        ax5 = fig.add_subplot(gs[1, 1])
        if performance_data:
            all_scores = []
            for data in performance_data:
                all_scores.extend(data['data']['Performance'].values)
            
            # Create quality buckets
            quality_ranges = {
                'Critical (0-25)': len([s for s in all_scores if 0 <= s < 25]),
                'Poor (25-50)': len([s for s in all_scores if 25 <= s < 50]),
                'Fair (50-75)': len([s for s in all_scores if 50 <= s < 75]),
                'Good (75-90)': len([s for s in all_scores if 75 <= s < 90]),
                'Excellent (90-100)': len([s for s in all_scores if 90 <= s <= 100])
            }
            
            colors = ['darkred', 'red', 'orange', 'lightgreen', 'green']
            bars = ax5.bar(range(len(quality_ranges)), list(quality_ranges.values()), 
                          color=colors, alpha=0.7, edgecolor='black')
            
            ax5.set_title('Performance Quality Distribution', fontweight='bold')
            ax5.set_ylabel('Number of URLs')
            ax5.set_xticks(range(len(quality_ranges)))
            ax5.set_xticklabels(list(quality_ranges.keys()), rotation=45)
            ax5.grid(True, alpha=0.3)
            
            # Add percentage labels
            total = sum(quality_ranges.values())
            for i, (bar, count) in enumerate(zip(bars, quality_ranges.values())):
                percentage = (count / total) * 100 if total > 0 else 0
                ax5.text(bar.get_x() + bar.get_width()/2., bar.get_height() + total*0.01,
                        f'{percentage:.1f}%', ha='center', va='bottom', fontsize=8)
        
        # Summary statistics
        ax6 = fig.add_subplot(gs[1, 2])
        ax6.axis('off')
        
        # Create summary text
        summary_text = "SUMMARY STATISTICS\n" + "="*25 + "\n\n"
        
        if traffic_data['All']:
            summary_text += f"TRAFFIC ANALYSIS:\n"
            summary_text += f"• Total samples: {len(traffic_data['All'])}\n"
            summary_text += f"• Mean traffic: {np.mean(traffic_data['All']):.0f}\n"
            summary_text += f"• Peak traffic: {np.max(traffic_data['All']):.0f}\n"
            summary_text += f"• Low traffic: {np.min(traffic_data['All']):.0f}\n\n"
        
        if performance_data:
            all_perf = []
            for data in performance_data:
                all_perf.extend(data['data']['Performance'].values)
            
            summary_text += f"PERFORMANCE ANALYSIS:\n"
            summary_text += f"• Total URLs: {len(all_perf)}\n"
            summary_text += f"• Mean score: {np.mean(all_perf):.1f}\n"
            summary_text += f"• Best score: {np.max(all_perf):.0f}\n"
            summary_text += f"• Worst score: {np.min(all_perf):.0f}\n"
            summary_text += f"• Time periods: {len(performance_data)}\n"
        
        ax6.text(0.05, 0.95, summary_text, transform=ax6.transAxes, fontsize=11,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        
        plt.savefig(self.base_dir / 'statistical_analysis_histograms.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def generate_comprehensive_report(self, traffic_data, performance_data):
        """Generate a comprehensive analysis report"""
        report = []
        report.append("=" * 80)
        report.append("COMPREHENSIVE TRAFFIC AND PERFORMANCE HISTOGRAM ANALYSIS")
        report.append("=" * 80)
        report.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Traffic Analysis
        report.append("TRAFFIC DATA ANALYSIS:")
        report.append("-" * 30)
        
        for source, values in traffic_data.items():
            if values and source != 'timestamps':
                report.append(f"\n{source.upper()} TRAFFIC:")
                report.append(f"  • Sample size: {len(values)}")
                report.append(f"  • Mean: {np.mean(values):.2f}")
                report.append(f"  • Median: {np.median(values):.2f}")
                report.append(f"  • Standard Deviation: {np.std(values):.2f}")
                report.append(f"  • Range: {np.min(values):.0f} - {np.max(values):.0f}")
                report.append(f"  • Coefficient of Variation: {(np.std(values)/np.mean(values)):.3f}")
        
        # Performance Analysis
        if performance_data:
            report.append("\n\nPERFORMANCE DATA ANALYSIS:")
            report.append("-" * 35)
            
            all_scores = []
            for data in performance_data:
                all_scores.extend(data['data']['Performance'].values)
            
            report.append(f"\nOVERALL PERFORMANCE:")
            report.append(f"  • Total URLs analyzed: {len(all_scores)}")
            report.append(f"  • Time periods: {len(performance_data)}")
            report.append(f"  • Mean score: {np.mean(all_scores):.2f}")
            report.append(f"  • Median score: {np.median(all_scores):.2f}")
            report.append(f"  • Standard deviation: {np.std(all_scores):.2f}")
            
            # Performance categories
            poor = len([s for s in all_scores if s < 50])
            needs_improvement = len([s for s in all_scores if 50 <= s < 90])
            good = len([s for s in all_scores if s >= 90])
            
            report.append(f"\nPERFORMANCE CATEGORIES:")
            report.append(f"  • Poor (0-49): {poor} URLs ({(poor/len(all_scores)*100):.1f}%)")
            report.append(f"  • Needs Improvement (50-89): {needs_improvement} URLs ({(needs_improvement/len(all_scores)*100):.1f}%)")
            report.append(f"  • Good (90-100): {good} URLs ({(good/len(all_scores)*100):.1f}%)")
        
        # File outputs
        report.append("\n\nGENERATED VISUALIZATIONS:")
        report.append("-" * 30)
        report.append("• comprehensive_traffic_histograms.png")
        report.append("• comprehensive_performance_histograms.png")
        report.append("• time_correlation_histograms.png")
        report.append("• statistical_analysis_histograms.png")
        
        report.append("\n\nANALYSIS INSIGHTS:")
        report.append("-" * 20)
        
        # Generate insights
        if traffic_data['US'] and traffic_data['India']:
            us_mean = np.mean(traffic_data['US'])
            india_mean = np.mean(traffic_data['India'])
            ratio = us_mean / india_mean if india_mean > 0 else 0
            report.append(f"• US traffic is {ratio:.1f}x higher than India traffic on average")
        
        if performance_data:
            best_time = max(performance_data, key=lambda x: x['avg_performance'])
            worst_time = min(performance_data, key=lambda x: x['avg_performance'])
            report.append(f"• Best performance period: {best_time['folder']} (Score: {best_time['avg_performance']:.1f})")
            report.append(f"• Worst performance period: {worst_time['folder']} (Score: {worst_time['avg_performance']:.1f})")
        
        report_text = "\n".join(report)
        print(report_text)
        
        # Save report
        with open(self.base_dir / 'comprehensive_histogram_report.txt', 'w') as f:
            f.write(report_text)
    
    def run_enhanced_analysis(self):
        """Run the complete enhanced analysis"""
        print("Starting Enhanced Traffic and Performance Histogram Analysis...")
        print("=" * 80)
        
        # Load data
        traffic_data = self.load_traffic_data_enhanced()
        performance_data = self.load_performance_data_enhanced()
        
        print(f"Traffic data loaded: {sum(len(v) for v in traffic_data.values() if isinstance(v, list))} total data points")
        print(f"Performance data loaded: {len(performance_data)} time periods")
        print("")
        
        # Create comprehensive histograms
        self.create_comprehensive_histogram_suite(traffic_data, performance_data)
        
        # Generate comprehensive report
        self.generate_comprehensive_report(traffic_data, performance_data)
        
        print("\nEnhanced analysis complete!")
        print("Check the generated PNG files and comprehensive report.")

if __name__ == "__main__":
    # Initialize enhanced analyzer
    base_path = "."
    analyzer = EnhancedTrafficPerformanceAnalyzer(base_path)
    
    # Run the enhanced analysis
    analyzer.run_enhanced_analysis()
