import requests
import os

API = "http://localhost:8001"

def test_flow():
    # 1. Login
    print("Testing Login...")
    res = requests.post(f"{API}/api/login", json={"username": "admin", "password": "admin123"})
    if res.status_code != 200:
        print(f"Login failed: {res.text}")
        return
    
    data = res.json()
    token = data["token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Login successful.")

    # 2. Get Accounts
    print("Fetching accounts...")
    res = requests.get(f"{API}/api/accounts", headers=headers)
    accounts = res.json()
    vw_id = next(a["id"] for a in accounts if a["slug"] == "volkswagen")
    print(f"Found Volkswagen ID: {vw_id}")

    # 3. Get Dealers
    print(f"Fetching dealers for {vw_id}...")
    res = requests.get(f"{API}/api/accounts/{vw_id}/dealers", headers=headers)
    dealers = res.json()
    dealer_ids = ",".join(str(d["id"]) for d in dealers)
    print(f"Dealers to process: {dealer_ids}")

    # 4. Generate
    print("Generating creatives...")
    bg_path = r"D:\DCAT\assets\assets\Sample-input-images\vw11.jpg"
    files = {"background": open(bg_path, "rb")}
    data = {
        "dealer_ids": dealer_ids,
        "output_format": "square",
        "logo_enabled": "dark"
    }
    res = requests.post(f"{API}/api/generate", headers=headers, files=files, data=data)
    if res.status_code != 200:
        print(f"Generation failed: {res.text}")
        return
    
    result = res.json()
    print(f"Successfully generated {result['count']} creatives.")
    for r in result["results"]:
        print(f" - {r['dealer_name']}: {r['output_filename']}")
        # check if file exists
        out_path = os.path.join(r"D:\DCAT\output", r["output_filename"])
        if os.path.exists(out_path):
            print(f"   [OK] File exists at {out_path}")
        else:
            print(f"   [ERROR] File missing at {out_path}")

if __name__ == "__main__":
    test_flow()
