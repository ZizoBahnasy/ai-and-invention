#!/usr/bin/env python3
"""
Generate a sample hierarchy tree with multiple leaves per shared prefix,
and save it as Markdown under outputs/taxonomy.
"""
import pandas as pd
import random
import os

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATASET_PATH = os.path.join(BASE_DIR, "outputs", "cpc_paths.tsv")
TAXONOMY_DIR = os.path.join(BASE_DIR, "outputs", "taxonomy")
TAXONOMY_FILE = os.path.join(TAXONOMY_DIR, "sample_cpc_taxonomy.md")

def sample_leaves(df, min_depth, max_depth=None):
    """Find a prefix and sample two distinct leaves under it."""
    if max_depth:
        bucket = df[(df['depth'] >= min_depth) & (df['depth'] < max_depth)]
    else:
        bucket = df[df['depth'] >= min_depth]

    if bucket.empty:
        print("Warning: No data found for depth range {}-{}".format(min_depth, max_depth))
        return []

    prefix_len = min_depth - 1
    code_cols = ['code_level_{}'.format(i+1) for i in range(prefix_len)]
    leaf_col = 'code_level_{}'.format(min_depth)

    # Group by the shared prefix
    groups = bucket.groupby(code_cols, dropna=False)

    # Keep only prefixes where there are 2+ distinct leaf_col values
    valid_prefixes = [
        (prefix, grp)
        for prefix, grp in groups
        if grp[leaf_col].nunique() >= 2
    ]
    if not valid_prefixes:
        print("Warning: No prefix with at least two leaves found at depth {}".format(min_depth))
        # Fallback: just return two random rows from the bucket if no such prefix exists
        return bucket.sample(n=min(2, len(bucket)), random_state=42).to_dict(orient="records")

    random.seed(42)
    _, grp = random.choice(valid_prefixes)
    return grp.sample(n=2, random_state=42).to_dict(orient="records")

def build_tree_from_samples(samples):
    """Builds a nested dictionary from a list of sample rows."""
    tree = {"CPC": {}}
    for row in samples:
        path_nodes = []
        # Determine the number of levels based on the length of the row dict
        num_levels = len(row) // 2
        for i in range(1, num_levels + 1):
            code = row.get('code_level_{}'.format(i))
            title = row.get('title_level_{}'.format(i))
            if code:
                path_nodes.append("{} - {}".format(code, title))
        
        subtree = tree["CPC"]
        for node in path_nodes:
            subtree = subtree.setdefault(node, {})
    return tree

def generate_markdown_tree(tree_dict):
    """Generates markdown lines from the nested dictionary."""
    lines = ["# Sample CPC Taxonomy", "", "```", "CPC"]
    def collect(node_dict, prefix=""):
        keys = list(node_dict.keys())
        for i, key in enumerate(keys):
            is_last = (i == len(keys) - 1)
            connector = "└── " if is_last else "├── "
            lines.append("{}{}{}".format(prefix, connector, key))
            child_prefix = prefix + ("    " if is_last else "│   ")
            collect(node_dict[key], child_prefix)
    collect(tree_dict["CPC"])
    lines.append("```")
    return lines

def main():
    """Main function."""
    if not os.path.exists(DATASET_PATH):
        print("Dataset file not found at: {}. Run cpc_parser.py first.".format(DATASET_PATH))
        return

    df = pd.read_csv(DATASET_PATH, sep="\t", dtype=str).fillna('')
    max_cols = len(df.columns)
    df['depth'] = df.apply(lambda row: sum(1 for i in range(0, max_cols, 2) if row.iloc[i]), axis=1)

    samples = []
    # Sample at different depths to ensure variety
    samples.extend(sample_leaves(df, 4, 5))
    samples.extend(sample_leaves(df, 6, 7))
    samples.extend(sample_leaves(df, 8, 9))
    
    if not samples:
        print("Could not generate any samples to create a taxonomy.")
        return

    tree = build_tree_from_samples(samples)
    markdown_lines = generate_markdown_tree(tree)
    
    os.makedirs(TAXONOMY_DIR, exist_ok=True)
    with open(TAXONOMY_FILE, "w", encoding='utf-8') as f:
        f.write("\n".join(markdown_lines))
    
    print("\n".join(markdown_lines))
    print("\nSaved sample taxonomy to {}".format(TAXONOMY_FILE))

if __name__ == "__main__":
    main()