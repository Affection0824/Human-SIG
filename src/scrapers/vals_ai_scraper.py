import json
import re
import pandas as pd
from pathlib import Path

def extract_json_from_input(input_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    match = re.search(r'props="([^"]+)"', content)
    if match:
        json_str = match.group(1).replace('&quot;', '"')
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
            
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    return None

def process_vals_data(data):
    rows = []
    if 'benchmarkView' in data:
        bv = data['benchmarkView']
        if isinstance(bv, list):
            content = next((item for item in bv if isinstance(item, dict) and 'tasks' in item), None)
            if content:
                tasks_data = content['tasks']
                if isinstance(tasks_data, list) and len(tasks_data) > 1:
                    tasks_dict = tasks_data[1]
                    if isinstance(tasks_dict, dict):
                        target_task = 'overall'
                        if target_task in tasks_dict:
                            model_data_list = tasks_dict[target_task]
                            if isinstance(model_data_list, list) and len(model_data_list) > 1:
                                model_map = model_data_list[1]
                                if isinstance(model_map, dict):
                                    for model_name, model_info in model_map.items():
                                        row = {'model_name': model_name}
                                        if isinstance(model_info, list) and len(model_info) > 1:
                                            metrics = model_info[1]
                                            if isinstance(metrics, dict):
                                                for k, v in metrics.items():
                                                    if isinstance(v, list) and len(v) > 1:
                                                        row[k] = v[1]
                                                    else:
                                                        row[k] = v
                                        rows.append(row)
    return pd.DataFrame(rows)

def run(data_dir):
    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"Error: Directory {data_path} does not exist.")
        return

    print(f"Running VALS.ai scraper on {data_path}")
    for subdir in data_path.iterdir():
        if subdir.is_dir() and not subdir.name.startswith('.') and not subdir.name.startswith('__'):
            input_file = subdir / 'input.txt'
            if input_file.exists():
                print(f"Processing {subdir.name}...")
                try:
                    data = extract_json_from_input(input_file)
                    if data:
                        df = process_vals_data(data)
                        if not df.empty:
                            output_file = subdir / 'data.csv'
                            df.to_csv(output_file, index=False)
                            print(f"  Saved data to {output_file} (Rows: {len(df)})")
                        else:
                            print(f"  Warning: No data rows found in {subdir.name}")
                    else:
                        print(f"  Warning: Could not extract JSON from {subdir.name}")
                except Exception as e:
                    print(f"  Error processing {subdir.name}: {e}")
