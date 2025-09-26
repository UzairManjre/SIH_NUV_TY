import requests
import json

def test_simple_validation():
    """Test a simple validation endpoint to check if the server is working"""
    try:
        response = requests.get("http://localhost:8001/")
        print("\nTesting root endpoint:")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"\nError testing root endpoint: {e}")
        raise  # Re-raise to fail the test

def test_analysis():
    url = "http://localhost:8001/analyze-progress/"
    
    # Prepare the request
    image_path = 'test_images/construction.jpg'
    
    try:
        # First test if we can read the image
        with open(image_path, 'rb') as img_file:
            print(f"\nSuccessfully read image: {image_path} (Size: {len(img_file.read())} bytes)")
        
        # Now try the actual request
        with open(image_path, 'rb') as img_file:
            files = {
                'image': ('construction.jpg', img_file, 'image/jpeg')
            }
            
            metadata = {
                'activity_type': 'construction',  # Using a simpler activity type
                'location_stretch': 'Test Location'
            }
            
            data = {'metadata': json.dumps(metadata)}
            
            # Print request details
            print("\nSending request to:", url)
            print("With metadata:", json.dumps(metadata, indent=2))
            
            # Send the request with a timeout
            response = requests.post(url, files=files, data=data, timeout=30)
            
            # Print response details
            print("\nResponse Status Code:", response.status_code)
            print("Response Headers:", json.dumps(dict(response.headers), indent=2))
            
            try:
                print("Response Body:", json.dumps(response.json(), indent=2))
            except:
                print("Response Text:", response.text)
            
            response.raise_for_status()
            
    except requests.exceptions.RequestException as e:
        print(f"\nRequest failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Status code: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
    except FileNotFoundError:
        print(f"\nError: Could not find image file at {image_path}")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print(f"Type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_validation()
    test_analysis()
