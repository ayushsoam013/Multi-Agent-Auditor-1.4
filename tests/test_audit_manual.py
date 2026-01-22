import sys
import os
from fastapi.testclient import TestClient

# Add project root to sys.path to allow importing app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app

def test_audit_endpoint():
    client = TestClient(app)
    
    image_path = os.path.abspath("misc/sofa.jpg")
    
    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        return

    print(f"Testing with image: {image_path}")
    
    with open(image_path, "rb") as f:
        files = {"file": ("sofa.jpg", f, "image/jpeg")}
        data = {
            "product_title": "Modern 3-Seater Sofa",
            "product_specs": "Color: Grey, Material: Ledger, Dimensions: 200x90x85cm",
            "mcat_name": "Sofas"
        }
        
        response = client.post("/api/v1/audit/multi-agent", data=data, files=files)
        
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Success!")
        print("Response JSON:")
        print(response.json())
    else:
        print("Failed!")
        print("Response Content:")
        print(response.text)

if __name__ == "__main__":
    test_audit_endpoint()
