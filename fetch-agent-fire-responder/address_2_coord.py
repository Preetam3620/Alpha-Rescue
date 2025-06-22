import requests
import google.generativeai as genai

# Your API keys
GOOGLE_MAPS_API_KEY="AIzaSyCBwkO7BVuyjU_m8LE-j7fMhEWs7d4sjkM"
GEMINI_API_KEY="AIzaSyAMBaufidL79w1X6tf3nnTMjvuvoFYj_1U"

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

def clean_address_with_gemini(vague_input: str) -> str:
    """
    Use Gemini to convert vague location input into a clean, Google Maps–compatible address.
    """
    prompt = f"""
Given a vague or informal place description, return a cleaned-up, Google Maps-compatible address.
Include street names, city, and state.

Input: "{vague_input}"
Cleaned Address:"""

    response = model.generate_content(prompt)
    return response.text.strip().replace("Cleaned Address:", "").strip('" ').strip()

def get_coordinates_from_google(cleaned_address: str) -> tuple[float, float]:
    """
    Use Google Maps Geocoding API to get precise coordinates of a cleaned address.
    """
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        'address': cleaned_address,
        'key': GOOGLE_MAPS_API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()

    if data['status'] == 'OK' and data['results']:
        location = data['results'][0]['geometry']['location']
        return float(location['lat']), float(location['lng'])
    else:
        raise ValueError(f"❌ Google Maps API Error: {data.get('status')} — {data.get('error_message')}")

def get_smart_coordinates(vague_input: str) -> tuple[float, float]:
    """
    Full flow: vague input → Gemini cleans it → Google Maps returns precise coordinates.
    Returns: latitude (float), longitude (float), cleaned address (str)
    """
    print(f"🧠 Raw Input: {vague_input}")
    cleaned_address = clean_address_with_gemini(vague_input)
    print(f"📍 Gemini Cleaned Address: {cleaned_address}")
    lat, lon = get_coordinates_from_google(cleaned_address)
    return lat, lon

# ✅ Example usage
if __name__ == "__main__":
    vague_place = input("📍 Enter a vague address or place name: ")
    try:
        lat, lon = get_smart_coordinates(vague_place)
        print("✅ Latitude:", lat)
        print("✅ Longitude:", lon)
        print(f"🔗 Google Maps: https://www.google.com/maps?q={lat},{lon}")
    except Exception as e:
        print(str(e))
    