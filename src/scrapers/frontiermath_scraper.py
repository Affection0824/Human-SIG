import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path

def parse_frontier_table(input_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'lxml')
    rows = soup.select('.table-row')
    
    data = []
    for row in rows:
        row_data = {}
        if row.has_attr('data-model-key'):
            row_data['model_key'] = row['data-model-key']
            
        cells = row.select('.cell')
        for cell in cells:
            classes = cell.get('class', [])
            col_name = 'unknown'
            for cls in classes:
                if cls.endswith('-cell') and cls != 'cell' and cls != 'column-cell':
                    col_name = cls.replace('-cell', '')
                    break
            
            if 'chart-cell' in classes:
                continue
                
            text = cell.get_text(" ", strip=True)
            row_data[col_name] = text
            
            if col_name == 'score':
                val = cell.select_one('.score-value')
                err = cell.select_one('.score-error')
                if val:
                    row_data['score_value'] = val.get_text(strip=True)
                if err:
                    row_data['score_error'] = err.get_text(strip=True)

        if row_data:
            data.append(row_data)
            
    return pd.DataFrame(data)

def run(data_dir):
    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"Error: Directory {data_path} does not exist.")
        return

    print(f"Running FrontierMath scraper on {data_path}")
    for subdir in data_path.iterdir():
        if subdir.is_dir() and not subdir.name.startswith('.') and not subdir.name.startswith('__'):
            input_file = subdir / 'input.txt'
            if input_file.exists():
                print(f"Processing {subdir.name}...")
                try:
                    df = parse_frontier_table(input_file)
                    if not df.empty:
                        output_file = subdir / 'data.csv'
                        df.to_csv(output_file, index=False, encoding='utf-8')
                        print(f"  Saved data to {output_file} (Rows: {len(df)})")
                    else:
                        print(f"  Warning: No data extracted for {subdir.name}")
                except Exception as e:
                    print(f"  Error processing {subdir.name}: {e}")
