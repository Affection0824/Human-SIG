
import pandas as pd
import json
import os
from bs4 import BeautifulSoup
import re

def inspect_artificial():
    print("--- Artificial Analysis Headers ---")
    try:
        with open('Human-SIG/data/raw/artificial_analysis/input.txt', 'r') as f:
            html = f.read()
        
        soup = BeautifulSoup(html, 'lxml')
        # Find all headers in the thead
        headers = []
        for th in soup.select('thead th'):
             text = th.get_text(strip=True)
             if text:
                 headers.append(text)
        
        # If that fails, try simple pandas read
        dfs = pd.read_html(html)
        if dfs:
            print("Pandas Columns:", dfs[0].columns.tolist())
    except Exception as e:
        print("Error inspecting AA:", e)

def inspect_vals():
    print("\n--- Vals AI JSON Structure ---")
    try:
        with open('Human-SIG/data/raw/vals_ai/mgsm/input.txt', 'r') as f:
            content = f.read()
        
        # Extract the JSON props object
        match = re.search(r'props="({.*})"', content)
        if match:
            json_str = match.group(1).replace('&quot;', '"')
            data = json.loads(json_str)
            # Traverse to find relevant data
            # Based on previous read: benchmarkView -> 0/1 -> default -> ...
            # The structure seemed to be a compressed list/array format typical of Astro/serialized data?
            # Let's just print keys of the root and first few levels
            print("Root keys:", data.keys())
            if 'benchmarkView' in data:
                print("benchmarkView:", data['benchmarkView'])
        else:
            print("Could not find props json")
    except Exception as e:
        print("Error inspecting Vals:", e)

def inspect_frontier():
    print("\n--- FrontierMath Parsing ---")
    try:
        with open('Human-SIG/data/raw/frontiermath/frontiermath_tier4/input.txt', 'r') as f:
            html = f.read()
        soup = BeautifulSoup(html, 'lxml')
        rows = soup.select('.table-row')
        print(f"Found {len(rows)} rows")
        if rows:
            first_row = rows[0]
            name = first_row.select_one('.name-cell').get_text(strip=True)
            score = first_row.select_one('.score-value').get_text(strip=True)
            print(f"Sample: {name} -> {score}")
    except Exception as e:
        print("Error inspecting Frontier:", e)

if __name__ == "__main__":
    inspect_artificial()
    inspect_vals()
    inspect_frontier()
