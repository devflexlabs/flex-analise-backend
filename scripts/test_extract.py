import requests
import json
import os
import sys

def test_extract(file_path):
    url = "http://localhost:8000/api/extract"
    
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return
    
    print(f"Testing extraction with file: {file_path}")
    
    # Open file in binary mode
    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f, 'image/png')}
        
        try:
            # Send POST request
            response = requests.post(url, files=files)
            
            # Check response
            if response.status_code == 200:
                print("[SUCCESS] Success!")

                print("Results:")
                result = response.json()
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
                # Check for analysis_id
                if result.get("analise_id"):
                    print(f"\nAnalysis saved to database with ID: {result['analise_id']}")
                
                # Check for token limit issues (truncated text message)
                if "[... texto intermediário removido" in result.get("observacoes", ""):
                    print("\n[INFO] Note: Text was truncated to fit token limits (as expected).")
                
            else:
                print(f"[ERROR] Error: {response.status_code}")

                print(response.text)
                
        except Exception as e:
            print(f"[ERROR] Connection error: {e}")


if __name__ == "__main__":
    # Path to test image
    test_file = "tests/test_contract.png"
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        
    test_extract(test_file)
