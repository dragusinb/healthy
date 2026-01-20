import requests
import json

BASE_URL = "http://localhost:8000"
EMAIL = "dragusinb@gmail.com"
PASSWORD = "J@guar123"

def test_api():
    session = requests.Session()
    
    # 1. Login
    print("Testing Login...")
    try:
        resp = session.post(f"{BASE_URL}/auth/token", data={"username": EMAIL, "password": PASSWORD})
        if resp.status_code != 200:
            print(f"Login Failed: {resp.text}")
            return
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Login Success.")
    except Exception as e:
        print(f"Connection Error: {e}")
        return

    # 2. Storage
    print("\nTesting Dashboard Stats...")
    resp = requests.get(f"{BASE_URL}/dashboard/stats", headers=headers)
    print(f"Status: {resp.status_code}, Body: {resp.json()}")

    # 3. Documents
    print("\nTesting Documents List...")
    resp = requests.get(f"{BASE_URL}/documents/", headers=headers)
    print(f"Status: {resp.status_code}, Docs Found: {len(resp.json())}")

    # 4. Evolution (Mock param)
    print("\nTesting Evolution (Hemoglobina)...")
    resp = requests.get(f"{BASE_URL}/dashboard/evolution/Hemoglobina", headers=headers)
    print(f"Status: {resp.status_code}, Data Points: {len(resp.json())}")
    
    # 5. Frontend Reachability
    print("\nTesting Frontend Reachability...")
    try:
        f_resp = requests.get("http://localhost:5173/")
        print(f"Frontend Status: {f_resp.status_code} (OK)")
    except:
        print("Frontend unreachable via Python requests.")

if __name__ == "__main__":
    test_api()
