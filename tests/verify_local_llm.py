import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from nvidia_llm import rag_system

print("Testing NVIDIA API AI client...", flush=True)
try:
    res = rag_system.generate_response([{"role": "user", "content": "Hello"}])
    print(f"Response: {res}", flush=True)
    if 'Error' in res['message']['content']:
        print("FAILED: AI returned error.", flush=True)
    else:
        print("SUCCESS: AI responded.", flush=True)
except Exception as e:
    print(f"FAILED: {e}", flush=True)
    with open('llm_error.txt', 'w') as f:
        f.write(str(e))

if 'Error' in res.get('message', {}).get('content', ''):
     with open('llm_error.txt', 'w') as f:
         f.write(res['message']['content'])
