
import json
import re

def inspect_vals_robust():
    print("\n--- Vals AI Robust Inspection ---")
    try:
        with open('Human-SIG/data/raw/vals_ai/mgsm/input.txt', 'r') as f:
            content = f.read()
        
        # Find props="..."
        start_marker = 'props="'
        start_idx = content.find(start_marker)
        if start_idx != -1:
            start_content = start_idx + len(start_marker)
            # Find the next quote "
            end_idx = content.find('"', start_content)
            if end_idx != -1:
                json_str = content[start_content:end_idx]
                json_str = json_str.replace('&quot;', '"')
                try:
                    data = json.loads(json_str)
                    print("JSON Parsed Successfully!")
                    # Now let's explore the structure
                    # We know models are at data['benchmarkView'][1]['default'][1]['metadata'][1]['models'][1] based on previous dump
                    # Let's try to navigate safely
                    bv = data.get('benchmarkView')
                    if bv:
                        # bv seems to be [0, { ... }]
                        obj = bv[1]
                        if 'default' in obj:
                             # default -> [0, { ... }]
                             inner = obj['default'][1]
                             print("Inner keys:", inner.keys())
                             if 'metadata' in inner:
                                 # metadata -> [0, { ... }]
                                 meta = inner['metadata']
                                 if isinstance(meta, list) and len(meta) > 1:
                                     print("Metadata content:", meta[1].keys())
                                     if 'models' in meta[1]:
                                          # models -> [1, ...]
                                          models_ref = meta[1]['models']
                                          print("Models ref:", models_ref)
                                          # If it's [1, ...], the data is likely in a shared array?
                                          # This serialization format [id, value] usually implies references.
                                          # But here it seems to be [type, value].
                                          # Let's see what `tasks` has.
                             if 'tasks' in inner:
                                 # tasks -> [0, { ... }]
                                 tasks = inner['tasks']
                                 if isinstance(tasks, list) and len(tasks) > 1:
                                     print("Tasks content sample:", tasks[1])
                except Exception as e:
                    print("JSON Parse Error:", e)
                    # print("Snippet:", json_str[:100])
        else:
            print("props attribute not found")
            
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    inspect_vals_robust()
