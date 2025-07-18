import json
import os
from collections import Counter
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
HIERARCHY_FILE = os.path.join(OUTPUT_DIR, "cpc_hierarchy.json")
DEPTH_ANALYSIS_DIR = os.path.join(OUTPUT_DIR, "depth_analysis")
RESULTS_FILE = os.path.join(DEPTH_ANALYSIS_DIR, "cpc_hierarchy_permutations.txt")
BAR_CHART_FILE = os.path.join(DEPTH_ANALYSIS_DIR, "cpc_depth_distribution.png")
SMOOTH_CHART_FILE = os.path.join(DEPTH_ANALYSIS_DIR, "cpc_depth_smooth.png")

ANTHROPIC_ORANGE = '#f9734a'

def get_paths(nodes, current_path, all_paths, depth_counter):
    for node in nodes:
        path = current_path + [node['code']]
        depth = len(path)
        if not node.get('children'):
            all_paths.append(path)
            depth_counter[depth] += 1
        else:
            get_paths(node['children'], path, all_paths, depth_counter)

def visualize_depth_distribution(depth_counts):
    depths = sorted(depth_counts.keys())
    counts = [depth_counts[d] for d in depths]
    total = float(sum(counts))
    percentages = [(c / total) * 100 if total > 0 else 0 for c in counts]
    
    plt.figure(figsize=(12, 7))
    bars = plt.bar(depths, counts, color=ANTHROPIC_ORANGE, alpha=0.9)
    plt.xlabel('Hierarchy Depth', fontsize=12)
    plt.ylabel('Number of Leaf Nodes', fontsize=12)
    plt.title('Distribution of CPC Leaf Nodes by Hierarchy Depth', fontsize=14)
    plt.xticks(depths)
    for bar, count, pct in zip(bars, counts, percentages):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                 '{:,}\n({:.1f}%)'.format(count, pct), ha='center', va='bottom', fontsize=9)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(BAR_CHART_FILE, dpi=300)
    plt.close()

    plt.figure(figsize=(12, 7))
    if len(depths) > 3:
        x_smooth = np.linspace(min(depths), max(depths), 300)
        spl = make_interp_spline(depths, counts, k=3)
        y_smooth = spl(x_smooth)
        plt.plot(x_smooth, y_smooth, color=ANTHROPIC_ORANGE, linewidth=3)
        plt.fill_between(x_smooth, y_smooth, color=ANTHROPIC_ORANGE, alpha=0.3)
    
    plt.scatter(depths, counts, color=ANTHROPIC_ORANGE, s=100, zorder=5)
    for x, y, pct in zip(depths, counts, percentages):
        plt.annotate('{:,}\n({:.1f}%)'.format(y, pct), (x, y), textcoords="offset points", 
                     xytext=(0, 10), ha='center', fontsize=9)
    
    plt.xlabel('Hierarchy Depth', fontsize=12)
    plt.ylabel('Number of Leaf Nodes', fontsize=12)
    plt.title('Distribution of CPC Leaf Nodes by Hierarchy Depth', fontsize=14)
    plt.xticks(depths)
    plt.grid(linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(SMOOTH_CHART_FILE, dpi=300)
    plt.close()
    
    print("Visualizations saved to {}".format(DEPTH_ANALYSIS_DIR))

def analyze_permutations():
    if not os.path.exists(HIERARCHY_FILE):
        print("Error: {} not found. Run cpc_parser.py first.".format(HIERARCHY_FILE))
        return

    with open(HIERARCHY_FILE, "r", encoding='utf-8') as f:
        hierarchy = json.load(f)
        
    all_paths = []
    depth_counts = Counter()
    get_paths(hierarchy, [], all_paths, depth_counts)
    
    path_structures = Counter(tuple(len(p) for p in path.split('/')[0]) for path in ('/'.join(p) for p in all_paths))
    total_paths = len(all_paths) if len(all_paths) > 0 else 1

    os.makedirs(DEPTH_ANALYSIS_DIR, exist_ok=True)
    visualize_depth_distribution(depth_counts)

    with open(RESULTS_FILE, "w", encoding='utf-8') as f:
        f.write("CPC Hierarchy Permutation Analysis\n")
        f.write("="*35 + "\n\n")

        deepest_path = max(all_paths, key=len)
        f.write("DEEPEST HIERARCHY PATH:\n")
        f.write("Path: {}\n".format(' > '.join(deepest_path)))
        f.write("Depth: {}\n\n".format(len(deepest_path)))
        
        f.write("DEPTH DISTRIBUTION:\n")
        f.write("------------------\n")
        for depth, count in sorted(depth_counts.items()):
            f.write("Depth {}: {:,} leaf nodes ({:.2f}%)\n".format(depth, count, (count/total_paths)*100))
        f.write("\n")

        f.write("ALL PERMUTATION STRUCTURES (by frequency):\n")
        f.write("-------------------------------------------\n\n")
        for structure, count in path_structures.most_common():
            f.write("Structure (lengths): {}\n".format(structure))
            f.write("Count: {}\n\n".format(count))

    print("Analysis complete. Report saved to {}".format(RESULTS_FILE))

if __name__ == "__main__":
    analyze_permutations()