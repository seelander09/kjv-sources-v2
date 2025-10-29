import requests
import json
import os

def get_property_data_json():
    url = "https://app.realie.ai/api/public/property/search"
    headers = {
        "Authorization": "bbf57563056ba1313097842042b7d6a1",
        "Content-Type": "application/json"
    }
    
    try:
        print("🔍 Fetching property data from Realie API...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract the three fields
        result = []
        for prop in data["properties"]:
            result.append({
                "totalAssessedValue": prop.get("totalAssessedValue"),
                "neighborhood": prop.get("neighborhood"),
                "equityCurrentEstBal": prop.get("equityCurrentEstBal")
            })
        
        print("✅ Data retrieved successfully!")
        print(f"📊 Found {len(result)} properties")
        
        # Save data to JSON file
        output_file = "property_data.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"💾 Data saved to: {output_file}")
        print(f"📁 Full path: {os.path.abspath(output_file)}")
        print("\n" + "="*50)
        print(json.dumps(result, indent=2))
        print("="*50)
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching data: {e}")
        return None
    except KeyError as e:
        print(f"❌ Error parsing response: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

if __name__ == "__main__":
    print("🏠 Realie Property Data - JSON Output")
    print("Fields: totalAssessedValue, neighborhood, equityCurrentEstBal")
    print("="*60)
    get_property_data_json()
