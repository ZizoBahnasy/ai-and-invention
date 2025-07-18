import os
import json
import csv
import re

# --- Configuration ---
# Use os.path for compatibility
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "cpc_title_lists")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
JSON_OUTPUT_PATH = os.path.join(OUTPUT_DIR, "cpc_hierarchy.json")
CSV_OUTPUT_PATH = os.path.join(OUTPUT_DIR, "cpc_paths.tsv")

# --- CSV Generation Functions (Helper) ---

def get_max_depth(nodes):
    if not nodes:
        return 0
    return 1 + max(get_max_depth(node.get('children', [])) for node in nodes)

def find_leaf_paths(nodes, current_path, all_paths):
    for node in nodes:
        new_path = current_path + [node]
        if not node.get('children'):
            all_paths.append(new_path)
        else:
            find_leaf_paths(node['children'], new_path, all_paths)

def generate_csv_from_tree(json_tree, output_filename):
    print("\nStarting CSV generation...")
    max_depth = get_max_depth(json_tree)
    print("Maximum hierarchy depth found: {}".format(max_depth))
    
    header = []
    for i in range(1, max_depth + 1):
        header.extend(['code_level_{}'.format(i), 'title_level_{}'.format(i)])

    all_paths = []
    find_leaf_paths(json_tree, [], all_paths)
    print("Found {} unique paths to leaf nodes.".format(len(all_paths)))
    
    csv_rows = []
    num_columns = max_depth * 2
    for path in all_paths:
        row = []
        for node in path:
            row.extend([node.get('code', ''), node.get('title', '')])
        row.extend([''] * (num_columns - len(row)))
        csv_rows.append(row)

    try:
        with open(output_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(header)
            writer.writerows(csv_rows)
        print("Successfully created CSV paths file at: {}".format(output_filename))
    except Exception as e:
        print("Error writing CSV file: {}".format(e))

# --- Main Parsing Function ---

def main():
    """
    Parses CPC text files, builds a JSON hierarchy and a flat path CSV.
    """
    all_lines = []
    print("Searching for CPC files in: {}".format(DATA_DIR))

    try:
        filenames = sorted([f for f in os.listdir(DATA_DIR) if f.startswith('cpc-section-') and f.endswith('.txt')])
        if not filenames:
            print("Error: No CPC files found in '{}'. Please place data files there.".format(DATA_DIR))
            return

        print("Found {} files: {}".format(len(filenames), ', '.join(filenames)))
        print("Concatenating files...")

        for filename in filenames:
            filepath = os.path.join(DATA_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                all_lines.extend(f.readlines())
    except FileNotFoundError:
        print("Error: Data directory not found at '{}'.".format(DATA_DIR))
        return

    print("Building hierarchy from parsed data...")
    json_tree = []
    nodes_by_code = {}
    level_path_stack = []
    last_high_level_parent = None

    line_pattern = re.compile(r'^(?P<code>[A-Z0-9/]+)\s+(?:(?P<level>\d+)\s+)?(?P<title>.*)$')

    for line in all_lines:
        line = line.strip()
        if not line:
            continue

        match = line_pattern.match(line)
        if not match:
            print("Warning: Could not parse line: '{}'".format(line))
            continue

        parts = match.groupdict()
        code = parts['code']
        level_str = parts['level']
        title = parts['title'].strip()
        
        new_node = {'code': code, 'title': title, 'children': []}
        nodes_by_code[code] = new_node
        
        if level_str is None:
            level_path_stack = []
            last_high_level_parent = new_node
            parent_code = None
            if len(code) == 3: parent_code = code[:1]
            elif len(code) > 3: parent_code = code[:-1] if code[:-1] in nodes_by_code else code[:3]

            if parent_code and parent_code in nodes_by_code:
                nodes_by_code[parent_code]['children'].append(new_node)
            else:
                json_tree.append(new_node)
        else:
            level = int(level_str)
            level_path_stack = level_path_stack[:level]
            
            if level == 0:
                if last_high_level_parent:
                    last_high_level_parent['children'].append(new_node)
                else:
                    print("Warning: Found level 0 node '{}' without high-level parent.".format(code))
                    json_tree.append(new_node)
            else:
                if level_path_stack:
                    level_path_stack[-1]['children'].append(new_node)
                else:
                    parent = last_high_level_parent if last_high_level_parent else (json_tree[-1] if json_tree else None)
                    if parent:
                        print("Warning: Found orphaned level {} node '{}'. Attaching to {}.".format(level, code, parent['code']))
                        parent['children'].append(new_node)
                    else:
                        print("Warning: Found orphaned level {} node '{}' with no available parent. Adding to root.".format(level, code))
                        json_tree.append(new_node)

            level_path_stack.append(new_node)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    try:
        with open(JSON_OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(json_tree, f, indent=2, ensure_ascii=False)
        print("\nSuccessfully created JSON hierarchy at: {}".format(JSON_OUTPUT_PATH))
    except Exception as e:
        print("\nError writing JSON file: {}".format(e))
        return

    generate_csv_from_tree(json_tree, CSV_OUTPUT_PATH)

if __name__ == "__main__":
    main()