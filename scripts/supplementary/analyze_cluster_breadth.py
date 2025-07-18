import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np

def simple_tokenizer(text):
    return text.split()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
BREADTH_ANALYSIS_DIR = os.path.join(OUTPUT_DIR, "breadth_analysis")
DATASET_PATH = os.path.join(OUTPUT_DIR, "cpc_paths.tsv")
REPORT_PATH = os.path.join(BREADTH_ANALYSIS_DIR, "cpc_breadth_report.txt")
VERTICAL_CHART_FILE = os.path.join(BREADTH_ANALYSIS_DIR, "cpc_breadth_vertical.png")
TOKEN_VERTICAL_CHART_FILE = os.path.join(BREADTH_ANALYSIS_DIR, "cpc_tokens_vertical.png")

ANTHROPIC_ORANGE = '#f9734a'

def count_tokens(name_list):
    total = 0
    for name in name_list:
        if isinstance(name, str):
            total += len(simple_tokenizer(name))
    return total

def visualize_vertical_chart(data, parents, levels, title, xlabel, output_file):
    fig, ax = plt.subplots(figsize=(10, 12))
    y_pos = np.arange(len(data))
    half_data = [d / 2.0 for d in data]

    ax.barh(y_pos, half_data, align='center', color=ANTHROPIC_ORANGE, alpha=0.7)
    ax.barh(y_pos, [-d for d in half_data], align='center', color=ANTHROPIC_ORANGE, alpha=0.7)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(levels)
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_title(title, fontsize=14)

    for i, value in enumerate(data):
        ax.text(half_data[i] + (max(data) * 0.01), i, '{:,}'.format(value), 
                va='center', ha='left', fontsize=10, fontweight='bold')

    ax.axvline(x=0, color='black', linestyle='-', alpha=0.3)
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.invert_yaxis()
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print("Visualization saved to {}".format(output_file))

def analyze_breadth():
    if not os.path.exists(DATASET_PATH):
        print("Dataset file not found at: {}. Run cpc_parser.py first.".format(DATASET_PATH))
        return
        
    df = pd.read_csv(DATASET_PATH, sep='\t', dtype=str).fillna('')
    report_lines = []
    
    breadths, tokens_list, parent_names, cluster_levels = [], [], ["Root"], []
    
    max_depth = len(df.columns) // 2
    cluster_cols = ['code_level_{}'.format(i+1) for i in range(max_depth)]
    title_cols = ['title_level_{}'.format(i+1) for i in range(max_depth)]
    
    lvl0_titles = df['title_level_1'].dropna().unique().tolist()
    breadth0 = len(lvl0_titles)
    tokens0 = count_tokens(lvl0_titles)
    line0 = "Level 1 (Top-level Sections) breadth: {}, tokens: {}".format(breadth0, tokens0)
    print(line0); report_lines.append(line0)
    breadths.append(breadth0)
    tokens_list.append(tokens0)
    cluster_levels.append("Level 1")

    for i in range(1, max_depth):
        parent_level_cols = cluster_cols[:i]
        child_level_col = cluster_cols[i]
        level_df = df[df[child_level_col] != ''].copy()
        
        if level_df.empty: break
            
        child_title_col = title_cols[i]
        grouped = level_df.groupby(parent_level_cols)[child_level_col].nunique()
        
        if grouped.empty: continue
            
        max_breadth = grouped.max()
        parent_group = grouped.idxmax()
        parent_path = parent_group if isinstance(parent_group, tuple) else (parent_group,)
        parent_title_col_index = i - 1
        parent_title = df[df[cluster_cols[parent_title_col_index]] == parent_path[-1]][title_cols[parent_title_col_index]].iloc[0]

        filter_mask = pd.Series(True, index=level_df.index)
        for j, p_val in enumerate(parent_path):
            filter_mask &= (level_df[cluster_cols[j]] == p_val)
        
        children_titles = level_df[filter_mask][child_title_col].dropna().unique().tolist()
        tokens = count_tokens(children_titles)
        
        line = "Level {} max breadth: {} under '{}..., tokens: {}".format(i+1, max_breadth, parent_title[:50], tokens)
        print(line); report_lines.append(line)
        
        breadths.append(max_breadth)
        tokens_list.append(tokens)
        parent_names.append(parent_title)
        cluster_levels.append("Level {}".format(i+1))

    os.makedirs(BREADTH_ANALYSIS_DIR, exist_ok=True)
    
    visualize_vertical_chart(breadths, parent_names, cluster_levels, 
                             'CPC Hierarchy Breadth Distribution', 
                             'Number of Children', VERTICAL_CHART_FILE)
    visualize_vertical_chart(tokens_list, parent_names, cluster_levels, 
                             'CPC Hierarchy Token Usage Distribution', 
                             'Token Count', TOKEN_VERTICAL_CHART_FILE)
                             
    with open(REPORT_PATH, "w", encoding='utf-8') as f:
        f.write("\n".join(report_lines))
    print("\nReport saved to {}".format(REPORT_PATH))

if __name__ == "__main__":
    analyze_breadth()