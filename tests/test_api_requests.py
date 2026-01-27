import requests
import os

def test_audit_api():
    url = "http://localhost:8000/api/v1/audit/multi-agent"
    image_path = os.path.abspath("misc/sofa.jpg")
    
    files = {"file": ("sofa.jpg", open(image_path, "rb"), "image/jpeg")}
    data = {
        "product_title": "Modern 3-Seater Sofa",
        "product_specs": "Color: Grey, Material: Leather, Dimensions: 200x90x85cm",
        "mcat_name": "Sofas",
    }
    
    print(f"Calling {url}...")
    try:
        response = requests.post(url, data=data, files=files, timeout=120)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Success!")
            # print(response.json())
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_audit_api()
