import requests
import os
import random

def test_multi_agent_audit():
    url = "http://localhost:8000/api/v1/audit/multi-agent"
    
    # Path to the image
    image_path = r"c:\Users\Imart\Documents\POC\Multi-Agent-Auditor-1.4\misc\sofa.jpg"
    
    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        return

    # Random titles, specs, and categories
    titles = [
        "Luxury Velvet Sofa - Emerald Green",
        "Modern Minimalist Fabric Couch",
        "Contemporary Leather Recliner",
        "Nordic Style 3-Seater Sofa",
        "Classic Chesterfield Sofa"
    ]
    
    specs = [
        "Material: Velvet, Wood; Dimensions: 200x90x85cm; Color: Green",
        "Eco-friendly fabric, high-density foam, 2-seater, grey color",
        "Genuine leather, electric reclining mechanism, USB charging port",
        "Solid oak frame, linen fabric, removable covers, minimalist design",
        "Deep button tufting, scroll arms, turned wooden feet, antique brown"
    ]

    categories = [
        "Living Room Furniture",
        "Office Chairs",
        "Home Decor",
        "Luxury Seating"
    ]
    
    title = random.choice(titles)
    spec = random.choice(specs)
    category = random.choice(categories)
    
    print(f"Testing with Title: {title}")
    print(f"Testing with Specs: {spec}")
    print(f"Testing with Category: {category}")
    print(f"Using image: {image_path}")
    
    # Prepare files and data
    files = {
        'file': ('sofa.jpg', open(image_path, 'rb'), 'image/jpeg')
    }
    data = {
        'product_title': title,
        'product_specs': spec,
        'mcat_name': category
    }
    
    try:
        response = requests.post(url, data=data, files=files)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Success!")
            print("Response JSON:")
            import json
            print(json.dumps(response.json(), indent=2))
        else:
            print("Error details:")
            print(response.text)
            
    except Exception as e:
        print(f"Request failed: {e}")
    finally:
        files['file'][1].close()

if __name__ == "__main__":
    test_multi_agent_audit()
