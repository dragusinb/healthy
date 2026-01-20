import requests
import json

BASE_URL = "http://localhost:8000"
EMAIL = "dragusinb@gmail.com"
PASSWORD = "J@guar123"

def verify_data():
    session = requests.Session()
    # Login
    resp = session.post(f"{BASE_URL}/auth/token", data={"username": EMAIL, "password": PASSWORD})
    if resp.status_code != 200:
        print("Login Failed")
        return
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Check Biomarkers
    resp = requests.get(f"{BASE_URL}/dashboard/biomarkers", headers=headers)
    data = resp.json()
    print(f"Biomarkers Count: {len(data)}")
    if len(data) > 0:
        print(f"Sample: {data[0]['name']} = {data[0]['value']} ({data[0]['status']})")
    
    # Check Documents
    resp = requests.get(f"{BASE_URL}/documents/", headers=headers)
    print(f"Documents Count: {len(resp.json())}")

if __name__ == "__main__":
    verify_data()
