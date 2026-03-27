#!/usr/bin/env python3
"""
Same URL Comparison Analysis
Analyzing performance improvements for the exact same URLs tested before and after optimization.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import glob
import re
from pathlib import Path
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class SameURLComparisonAnalyzer:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir).parent  # Go back to main directory
        self.pre_opt_folder = self.base_dir / "pagespeed-reports"
        self.post_opt_folder = self.base_dir / "pagespeed-reports-cron" 
        self.output_folder = self.base_dir / "comparison-over-time"
        
        # Set up plotting style
        plt.style.use('default')
        sns.set_palette("Set2")
        plt.rcParams['figure.facecolor'] = 'white'
        
    def load_all_urls_data(self):
        """Load all URL data from both periods"""
        print("Loading all URL data...")
        
        # Load pre-optimization data
        pre_urls = {}
        csv_files = glob.glob(str(self.pre_opt_folder / "*" / "*.csv"))
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                if 'URL' in df.columns and 'Performance' in df.columns:
                    for _, row in df.iterrows():
                        if pd.notna(row['URL']) and pd.notna(row['Performance']):
                            url = str(row['URL']).strip().strip('"')
                            if url not in pre_urls:
                                pre_urls[url] = []
                            
                            pre_urls[url].append({
                                'performance': row['Performance'],
                                'accessibility': row.get('Accessibility', 0),
                                'best_practices': row.get('Best Practices', 0),
                                'seo': row.get('SEO', 0),
                                'fcp': row.get('First Contentful Paint (ms)', 0),
                                'lcp': row.get('Largest Contentful Paint (ms)', 0),
                                'speed_index': row.get('Speed Index (ms)', 0),
                                'tbt': row.get('Total Blocking Time (ms)', 0),
                                'cls': row.get('Cumulative Layout Shift', 0),
                                'file': csv_file
                            })
            except Exception as e:
                print(f"Error reading {csv_file}: {e}")
                continue
        
        # Load post-optimization data
        post_urls = {}
        
        # Find time-stamped folders
        folder_pattern = re.compile(r'(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2})')
        folders = [f for f in os.listdir(self.post_opt_folder) 
                  if os.path.isdir(self.post_opt_folder / f) and folder_pattern.match(f)]
        
        for folder in sorted(folders):
            csv_files = glob.glob(str(self.post_opt_folder / folder / "*.csv"))
            
            for csv_file in csv_files:
                try:
                    df = pd.read_csv(csv_file)
                    if 'URL' in df.columns and 'Performance' in df.columns:
                        for _, row in df.iterrows():
                            if pd.notna(row['URL']) and pd.notna(row['Performance']):
                                url = str(row['URL']).strip().strip('"')
                                if url not in post_urls:
                                    post_urls[url] = []
                                
                                post_urls[url].append({
                                    'performance': row['Performance'],
                                    'accessibility': row.get('Accessibility', 0),
                                    'best_practices': row.get('Best Practices', 0),
                                    'seo': row.get('SEO', 0),
                                    'fcp': row.get('First Contentful Paint (ms)', 0),
                                    'lcp': row.get('Largest Contentful Paint (ms)', 0),
                                    'speed_index': row.get('Speed Index (ms)', 0),
                                    'tbt': row.get('Total Blocking Time (ms)', 0),
                                    'cls': row.get('Cumulative Layout Shift', 0),
                                    'file': csv_file,
                                    'folder': folder
                                })
                except Exception as e:
                    continue
        
        return pre_urls, post_urls
    
    def find_common_urls(self, pre_urls, post_urls):
        """Find URLs that exist in both datasets"""
        pre_url_set = set(pre_urls.keys())
        post_url_set = set(post_urls.keys())
        
        common_urls = pre_url_set.intersection(post_url_set)
        pre_only = pre_url_set - post_url_set
        post_only = post_url_set - pre_url_set
        
        print(f"\nURL OVERLAP ANALYSIS:")
        print(f"Pre-optimization URLs: {len(pre_url_set)}")
        print(f"Post-optimization URLs: {len(post_url_set)}")
        print(f"Common URLs (same URLs tested): {len(common_urls)}")
        print(f"Pre-only URLs: {len(pre_only)}")
        print(f"Post-only URLs: {len(post_only)}")
        print(f"Overlap percentage: {len(common_urls)/max(len(pre_url_set), len(post_url_set))*100:.1f}%")
        
        return common_urls, pre_only, post_only
    
    def create_same_url_comparison_data(self, pre_urls, post_urls, common_urls):
        """Create comparison data for the same URLs"""
        comparison_data = []
        
        for url in common_urls:
            # Average the measurements if multiple tests exist
            pre_data = pre_urls[url]
            post_data = post_urls[url]
            
            # Calculate averages for pre-optimization
            pre_avg = {
                'performance': np.mean([d['performance'] for d in pre_data]),
                'accessibility': np.mean([d['accessibility'] for d in pre_data if d['accessibility'] > 0]),
                'best_practices': np.mean([d['best_practices'] for d in pre_data if d['best_practices'] > 0]),
                'seo': np.mean([d['seo'] for d in pre_data if d['seo'] > 0]),
                'fcp': np.mean([d['fcp'] for d in pre_data if d['fcp'] > 0]),
                'lcp': np.mean([d['lcp'] for d in pre_data if d['lcp'] > 0]),
                'speed_index': np.mean([d['speed_index'] for d in pre_data if d['speed_index'] > 0]),
                'tbt': np.mean([d['tbt'] for d in pre_data if d['tbt'] > 0]),
                'cls': np.mean([d['cls'] for d in pre_data if d['cls'] > 0])
            }
            
            # Calculate averages for post-optimization
            post_avg = {
                'performance': np.mean([d['performance'] for d in post_data]),
                'accessibility': np.mean([d['accessibility'] for d in post_data if d['accessibility'] > 0]),
                'best_practices': np.mean([d['best_practices'] for d in post_data if d['best_practices'] > 0]),
                'seo': np.mean([d['seo'] for d in post_data if d['seo'] > 0]),
                'fcp': np.mean([d['fcp'] for d in post_data if d['fcp'] > 0]),
                'lcp': np.mean([d['lcp'] for d in post_data if d['lcp'] > 0]),
                'speed_index': np.mean([d['speed_index'] for d in post_data if d['speed_index'] > 0]),
                'tbt': np.mean([d['tbt'] for d in post_data if d['tbt'] > 0]),
                'cls': np.mean([d['cls'] for d in post_data if d['cls'] > 0])
            }
            
            comparison_data.append({
                'url': url,
                'pre_performance': pre_avg['performance'],
                'post_performance': post_avg['performance'],
                'improvement': post_avg['performance'] - pre_avg['performance'],
                'improvement_pct': ((post_avg['performance'] - pre_avg['performance']) / pre_avg['performance']) * 100,
                'pre_fcp': pre_avg['fcp'],
                'post_fcp': post_avg['fcp'],
                'pre_lcp': pre_avg['lcp'],
                'post_lcp': post_avg['lcp'],
                'pre_tbt': pre_avg['tbt'],
                'post_tbt': post_avg['tbt'],
                'pre_cls': pre_avg['cls'],
                'post_cls': post_avg['cls'],
                'pre_tests': len(pre_data),
                'post_tests': len(post_data)
            })
        
        return pd.DataFrame(comparison_data)
    
    def create_same_url_analysis_charts(self, comparison_df):
        """Create charts specifically for same URL comparisons"""
        
        # Chart 1: Same URL Performance Comparison
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('SAME URLs: Before vs After Optimization Comparison', 
                     fontsize=18, fontweight='bold', y=0.98)
        
        # Paired comparison plot
        ax1.scatter(comparison_df['pre_performance'], comparison_df['post_performance'], 
                   alpha=0.7, s=60, c='blue', edgecolors='black')
        
        # Add diagonal line (no improvement line)
        min_val = min(comparison_df['pre_performance'].min(), comparison_df['post_performance'].min())
        max_val = max(comparison_df['pre_performance'].max(), comparison_df['post_performance'].max())
        ax1.plot([min_val, max_val], [min_val, max_val], 'r--', alpha=0.8, linewidth=2, 
                label='No Change Line')
        
        # Count improvements
        improved = len(comparison_df[comparison_df['improvement'] > 0])
        degraded = len(comparison_df[comparison_df['improvement'] < 0])
        same = len(comparison_df[comparison_df['improvement'] == 0])
        
        ax1.text(0.05, 0.95, f'Improved: {improved}\nDegraded: {degraded}\nSame: {same}', 
                transform=ax1.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        ax1.set_xlabel('Before Optimization (Performance Score)')
        ax1.set_ylabel('After Optimization (Performance Score)')
        ax1.set_title('Same URL Performance: Before vs After', fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Improvement histogram with small bucket size
        ax2.hist(comparison_df['improvement'], bins=15, alpha=0.7, color='green', edgecolor='black')
        ax2.axvline(0, color='red', linestyle='--', linewidth=2, label='No Change')
        ax2.axvline(comparison_df['improvement'].mean(), color='blue', linestyle='--', linewidth=2,
                   label=f'Mean: {comparison_df["improvement"].mean():.1f}')
        
        ax2.set_title('Performance Improvement Distribution (15 bins)', fontweight='bold')
        ax2.set_xlabel('Performance Score Change')
        ax2.set_ylabel('Number of URLs')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Before/After histograms with small buckets
        ax3.hist([comparison_df['pre_performance'], comparison_df['post_performance']], 
                bins=12, alpha=0.7, label=['Before', 'After'],
                color=['red', 'green'], edgecolor='black')
        
        ax3.axvline(comparison_df['pre_performance'].mean(), color='red', linestyle='--', linewidth=2)
        ax3.axvline(comparison_df['post_performance'].mean(), color='green', linestyle='--', linewidth=2)
        
        ax3.set_title('Performance Distribution: Same URLs (12 bins)', fontweight='bold')
        ax3.set_xlabel('Performance Score')
        ax3.set_ylabel('Number of URLs')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Top improvers and degraders
        top_improvers = comparison_df.nlargest(5, 'improvement')
        top_degraders = comparison_df.nsmallest(5, 'improvement')
        
        # Create text summary
        ax4.axis('off')
        
        summary_text = "TOP 5 IMPROVEMENTS:\n"
        for i, row in top_improvers.iterrows():
            url_short = row['url'].split('/')[-1][:30] + "..." if len(row['url'].split('/')[-1]) > 30 else row['url'].split('/')[-1]
            summary_text += f"• {url_short}: +{row['improvement']:.1f}\n"
        
        summary_text += "\nTOP 5 DEGRADATIONS:\n"
        for i, row in top_degraders.iterrows():
            url_short = row['url'].split('/')[-1][:30] + "..." if len(row['url'].split('/')[-1]) > 30 else row['url'].split('/')[-1]
            summary_text += f"• {url_short}: {row['improvement']:.1f}\n"
        
        summary_text += f"\nSTATISTICS:\n"
        summary_text += f"• Mean improvement: {comparison_df['improvement'].mean():.2f}\n"
        summary_text += f"• Median improvement: {comparison_df['improvement'].median():.2f}\n"
        summary_text += f"• Std deviation: {comparison_df['improvement'].std():.2f}\n"
        
        # Statistical test
        stat, p_value = stats.wilcoxon(comparison_df['pre_performance'], comparison_df['post_performance'])
        summary_text += f"• Wilcoxon p-value: {p_value:.4f}\n"
        
        ax4.text(0.05, 0.95, summary_text, transform=ax4.transAxes, 
                verticalalignment='top', fontsize=10, fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        ax4.set_title('Statistical Summary', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(self.output_folder / 'same_urls_performance_comparison.png', 
                   dpi=300, bbox_inches='tight')
        plt.show()
    
    def create_core_web_vitals_same_urls(self, comparison_df):
        """Create Core Web Vitals comparison for same URLs"""
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Core Web Vitals: Same URLs Before vs After', 
                     fontsize=18, fontweight='bold', y=0.98)
        
        # Filter out zero values for better analysis
        valid_lcp = comparison_df[(comparison_df['pre_lcp'] > 0) & (comparison_df['post_lcp'] > 0)]
        valid_fcp = comparison_df[(comparison_df['pre_fcp'] > 0) & (comparison_df['post_fcp'] > 0)]
        valid_tbt = comparison_df[(comparison_df['pre_tbt'] > 0) & (comparison_df['post_tbt'] > 0)]
        valid_cls = comparison_df[(comparison_df['pre_cls'] > 0) & (comparison_df['post_cls'] > 0)]
        
        # LCP Comparison
        if len(valid_lcp) > 0:
            ax1 = axes[0, 0]
            ax1.scatter(valid_lcp['pre_lcp'], valid_lcp['post_lcp'], alpha=0.7, s=50, c='orange')
            
            min_lcp = min(valid_lcp['pre_lcp'].min(), valid_lcp['post_lcp'].min())
            max_lcp = max(valid_lcp['pre_lcp'].max(), valid_lcp['post_lcp'].max())
            ax1.plot([min_lcp, max_lcp], [min_lcp, max_lcp], 'r--', alpha=0.8)
            
            lcp_improvement = ((valid_lcp['pre_lcp'].mean() - valid_lcp['post_lcp'].mean()) / valid_lcp['pre_lcp'].mean()) * 100
            ax1.text(0.05, 0.95, f'LCP Improvement: {lcp_improvement:+.1f}%', 
                    transform=ax1.transAxes, bbox=dict(boxstyle='round', facecolor='wheat'))
            
            ax1.set_xlabel('Before LCP (ms)')
            ax1.set_ylabel('After LCP (ms)')
            ax1.set_title(f'Largest Contentful Paint ({len(valid_lcp)} URLs)', fontweight='bold')
            ax1.grid(True, alpha=0.3)
        
        # FCP Comparison
        if len(valid_fcp) > 0:
            ax2 = axes[0, 1]
            ax2.scatter(valid_fcp['pre_fcp'], valid_fcp['post_fcp'], alpha=0.7, s=50, c='blue')
            
            min_fcp = min(valid_fcp['pre_fcp'].min(), valid_fcp['post_fcp'].min())
            max_fcp = max(valid_fcp['pre_fcp'].max(), valid_fcp['post_fcp'].max())
            ax2.plot([min_fcp, max_fcp], [min_fcp, max_fcp], 'r--', alpha=0.8)
            
            fcp_improvement = ((valid_fcp['pre_fcp'].mean() - valid_fcp['post_fcp'].mean()) / valid_fcp['pre_fcp'].mean()) * 100
            ax2.text(0.05, 0.95, f'FCP Change: {fcp_improvement:+.1f}%', 
                    transform=ax2.transAxes, bbox=dict(boxstyle='round', facecolor='wheat'))
            
            ax2.set_xlabel('Before FCP (ms)')
            ax2.set_ylabel('After FCP (ms)')
            ax2.set_title(f'First Contentful Paint ({len(valid_fcp)} URLs)', fontweight='bold')
            ax2.grid(True, alpha=0.3)
        
        # TBT Comparison
        if len(valid_tbt) > 0:
            ax3 = axes[1, 0]
            ax3.scatter(valid_tbt['pre_tbt'], valid_tbt['post_tbt'], alpha=0.7, s=50, c='red')
            
            min_tbt = min(valid_tbt['pre_tbt'].min(), valid_tbt['post_tbt'].min())
            max_tbt = max(valid_tbt['pre_tbt'].max(), valid_tbt['post_tbt'].max())
            ax3.plot([min_tbt, max_tbt], [min_tbt, max_tbt], 'r--', alpha=0.8)
            
            tbt_improvement = ((valid_tbt['pre_tbt'].mean() - valid_tbt['post_tbt'].mean()) / valid_tbt['pre_tbt'].mean()) * 100
            ax3.text(0.05, 0.95, f'TBT Improvement: {tbt_improvement:+.1f}%', 
                    transform=ax3.transAxes, bbox=dict(boxstyle='round', facecolor='wheat'))
            
            ax3.set_xlabel('Before TBT (ms)')
            ax3.set_ylabel('After TBT (ms)')
            ax3.set_title(f'Total Blocking Time ({len(valid_tbt)} URLs)', fontweight='bold')
            ax3.grid(True, alpha=0.3)
        
        # Improvement percentages histogram
        ax4 = axes[1, 1]
        ax4.hist(comparison_df['improvement_pct'], bins=20, alpha=0.7, color='purple', edgecolor='black')
        ax4.axvline(0, color='red', linestyle='--', linewidth=2, label='No Change')
        ax4.axvline(comparison_df['improvement_pct'].mean(), color='blue', linestyle='--', linewidth=2,
                   label=f'Mean: {comparison_df["improvement_pct"].mean():.1f}%')
        
        ax4.set_title('Performance Improvement % (20 bins)', fontweight='bold')
        ax4.set_xlabel('Improvement Percentage')
        ax4.set_ylabel('Number of URLs')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_folder / 'same_urls_core_web_vitals.png', 
                   dpi=300, bbox_inches='tight')
        plt.show()
    
    def generate_same_url_report(self, comparison_df, common_urls, pre_only, post_only):
        """Generate detailed report for same URL analysis"""
        
        report = []
        report.append("=" * 80)
        report.append("SAME URL COMPARISON ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # URL overlap analysis
        report.append("URL OVERLAP ANALYSIS:")
        report.append("-" * 22)
        total_unique_pre = len(pre_only) + len(common_urls)
        total_unique_post = len(post_only) + len(common_urls)
        
        report.append(f"Pre-optimization unique URLs: {total_unique_pre}")
        report.append(f"Post-optimization unique URLs: {total_unique_post}")
        report.append(f"Common URLs (tested both times): {len(common_urls)}")
        report.append(f"Pre-only URLs: {len(pre_only)}")
        report.append(f"Post-only URLs: {len(post_only)}")
        report.append(f"Overlap percentage: {len(common_urls)/max(total_unique_pre, total_unique_post)*100:.1f}%")
        report.append("")
        
        # Same URL performance analysis
        report.append("SAME URL PERFORMANCE ANALYSIS:")
        report.append("-" * 32)
        
        improved_urls = len(comparison_df[comparison_df['improvement'] > 0])
        degraded_urls = len(comparison_df[comparison_df['improvement'] < 0])
        unchanged_urls = len(comparison_df[comparison_df['improvement'] == 0])
        
        report.append(f"URLs that improved: {improved_urls} ({improved_urls/len(comparison_df)*100:.1f}%)")
        report.append(f"URLs that degraded: {degraded_urls} ({degraded_urls/len(comparison_df)*100:.1f}%)")
        report.append(f"URLs unchanged: {unchanged_urls} ({unchanged_urls/len(comparison_df)*100:.1f}%)")
        report.append("")
        
        # Statistical analysis
        report.append("STATISTICAL ANALYSIS:")
        report.append("-" * 21)
        report.append(f"Mean improvement: {comparison_df['improvement'].mean():.2f} points")
        report.append(f"Median improvement: {comparison_df['improvement'].median():.2f} points")
        report.append(f"Standard deviation: {comparison_df['improvement'].std():.2f}")
        report.append(f"Mean improvement %: {comparison_df['improvement_pct'].mean():.1f}%")
        
        # Wilcoxon signed-rank test (paired test for same URLs)
        try:
            stat, p_value = stats.wilcoxon(comparison_df['pre_performance'], comparison_df['post_performance'])
            report.append(f"Wilcoxon signed-rank test p-value: {p_value:.6f}")
            if p_value < 0.05:
                report.append("Result: STATISTICALLY SIGNIFICANT improvement")
            else:
                report.append("Result: No statistically significant difference")
        except:
            report.append("Wilcoxon test: Could not be performed")
        
        report.append("")
        
        # Top performers
        report.append("TOP 10 MOST IMPROVED URLs:")
        report.append("-" * 28)
        top_improved = comparison_df.nlargest(10, 'improvement')
        for i, row in top_improved.iterrows():
            url_name = row['url'].split('/')[-1]
            report.append(f"• {url_name}: {row['pre_performance']:.1f} → {row['post_performance']:.1f} (+{row['improvement']:.1f})")
        
        report.append("")
        report.append("TOP 5 MOST DEGRADED URLs:")
        report.append("-" * 26)
        top_degraded = comparison_df.nsmallest(5, 'improvement')
        for i, row in top_degraded.iterrows():
            url_name = row['url'].split('/')[-1]
            report.append(f"• {url_name}: {row['pre_performance']:.1f} → {row['post_performance']:.1f} ({row['improvement']:.1f})")
        
        # Core Web Vitals for same URLs
        valid_lcp = comparison_df[(comparison_df['pre_lcp'] > 0) & (comparison_df['post_lcp'] > 0)]
        valid_tbt = comparison_df[(comparison_df['pre_tbt'] > 0) & (comparison_df['post_tbt'] > 0)]
        
        if len(valid_lcp) > 0:
            lcp_improvement = ((valid_lcp['pre_lcp'].mean() - valid_lcp['post_lcp'].mean()) / valid_lcp['pre_lcp'].mean()) * 100
            report.append(f"\nLCP ANALYSIS ({len(valid_lcp)} URLs):")
            report.append(f"Average improvement: {lcp_improvement:+.1f}%")
        
        if len(valid_tbt) > 0:
            tbt_improvement = ((valid_tbt['pre_tbt'].mean() - valid_tbt['post_tbt'].mean()) / valid_tbt['pre_tbt'].mean()) * 100
            report.append(f"\nTBT ANALYSIS ({len(valid_tbt)} URLs):")
            report.append(f"Average improvement: {tbt_improvement:+.1f}%")
        
        # Key insights
        report.append(f"\nKEY INSIGHTS:")
        report.append("-" * 13)
        
        if len(common_urls) < 10:
            report.append("⚠️  LIMITED URL OVERLAP: Only a few URLs were tested in both periods")
            report.append("   This limits the reliability of direct before/after comparison")
        elif len(common_urls) < 50:
            report.append("⚠️  MODERATE URL OVERLAP: Some URLs tested in both periods")
            report.append("   Results provide useful insights but with limited sample size")
        else:
            report.append("✅ GOOD URL OVERLAP: Many URLs tested in both periods")
            report.append("   Results provide reliable before/after comparison")
        
        if comparison_df['improvement'].mean() > 5:
            report.append("✅ SIGNIFICANT IMPROVEMENT: Same URLs show clear performance gains")
        elif comparison_df['improvement'].mean() > 0:
            report.append("✅ MODERATE IMPROVEMENT: Same URLs show some performance gains")
        else:
            report.append("⚠️  NO CLEAR IMPROVEMENT: Same URLs show mixed or negative results")
        
        percent_improved = improved_urls / len(comparison_df) * 100
        if percent_improved > 70:
            report.append(f"✅ MAJORITY IMPROVED: {percent_improved:.1f}% of same URLs performed better")
        elif percent_improved > 50:
            report.append(f"✅ MOST IMPROVED: {percent_improved:.1f}% of same URLs performed better")
        else:
            report.append(f"⚠️  MIXED RESULTS: Only {percent_improved:.1f}% of same URLs improved")
        
        report_text = "\n".join(report)
        print(report_text)
        
        # Save report
        with open(self.output_folder / 'same_url_comparison_report.txt', 'w') as f:
            f.write(report_text)
        
        return report_text
    
    def run_same_url_analysis(self):
        """Run complete same URL analysis"""
        print("Starting Same URL Comparison Analysis...")
        print("=" * 60)
        
        # Load all URL data
        pre_urls, post_urls = self.load_all_urls_data()
        
        # Find common URLs
        common_urls, pre_only, post_only = self.find_common_urls(pre_urls, post_urls)
        
        if len(common_urls) == 0:
            print("\n❌ ERROR: No common URLs found between pre and post optimization!")
            print("The datasets contain completely different URLs.")
            print("This means we cannot do a direct same-URL comparison.")
            return None
        
        # Create comparison data
        comparison_df = self.create_same_url_comparison_data(pre_urls, post_urls, common_urls)
        
        print(f"\nCreating charts for {len(comparison_df)} common URLs...")
        
        # Create charts
        self.create_same_url_analysis_charts(comparison_df)
        self.create_core_web_vitals_same_urls(comparison_df)
        
        # Generate report
        self.generate_same_url_report(comparison_df, common_urls, pre_only, post_only)
        
        print(f"\nSame URL analysis complete!")
        print(f"Charts saved:")
        print(f"  • same_urls_performance_comparison.png")
        print(f"  • same_urls_core_web_vitals.png")
        print(f"  • same_url_comparison_report.txt")
        
        return comparison_df

if __name__ == "__main__":
    # Run the same URL analysis
    analyzer = SameURLComparisonAnalyzer("./comparison-over-time")
    comparison_df = analyzer.run_same_url_analysis()
