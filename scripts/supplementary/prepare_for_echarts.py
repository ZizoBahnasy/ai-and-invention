import json
import os # <-- Added the missing import

def format_node_for_echarts(node):
    """
    Recursively formats a node to be compatible with ECharts.
    ECharts Tree Chart expects a 'name' field for the label.
    """
    # Combine code and title for a descriptive name
    formatted_name = "{} - {}".format(node.get('code', ''), node.get('title', ''))
    
    # If the title is very long, truncate it for better display
    if len(formatted_name) > 150:
        formatted_name = "{} - {}...".format(node.get('code', ''), node.get('title', '')[:147])

    new_node = {
        'name': formatted_name,
        # Keep original data for potential tooltips or other interactions
        'original_code': node.get('code', ''),
        'original_title': node.get('title', '')
    }
    
    if node.get('children'):
        new_node['children'] = [format_node_for_echarts(child) for child in node['children']]
    
    return new_node

def convert_cpc_to_echarts_format(input_json_path, output_json_path):
    """
    Reads the CPC hierarchy JSON and converts it to a format suitable for ECharts.
    """
    print("Reading from {}...".format(input_json_path))
    try:
        with open(input_json_path, 'r', encoding='utf-8') as f:
            cpc_tree = json.load(f)
    except FileNotFoundError:
        print("Error: The file {} was not found. Please run the main parsing script first.".format(input_json_path))
        return
    except Exception as e:
        print("Error reading JSON file: {}".format(e))
        return

    print("Converting to ECharts format...")
    # ECharts works best with a single root node. We'll create a virtual root.
    echarts_tree = {
        'name': 'CPC Hierarchy',
        'children': [format_node_for_echarts(node) for node in cpc_tree]
    }
    
    print("Writing ECharts-compatible JSON to {}...".format(output_json_path))
    try:
        with open(output_json_path, 'w', encoding='utf-8') as f:
            # Use compact format for faster loading in the browser
            json.dump(echarts_tree, f, separators=(',', ':'), ensure_ascii=False)
        print("Conversion complete!")
    except Exception as e:
        print("Error writing ECharts JSON file: {}".format(e))


if __name__ == '__main__':
    # Get paths relative to the project root for robustness
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    OUTPUT_DIR = os.path.join(BASE_DIR, 'outputs')
    
    input_file = os.path.join(OUTPUT_DIR, 'cpc_hierarchy.json')
    output_file = os.path.join(OUTPUT_DIR, 'echarts_data.json')
    
    convert_cpc_to_echarts_format(input_file, output_file)