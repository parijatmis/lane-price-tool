from flask import Flask, request, jsonify, render_template
import requests

app = Flask(__name__)

API_KEY = "5b3ce3597851110001cf6248278923d9ee17473e9b2ba3f22bb95974"

RATES = {
    'dry_van': 2.50,
    'flatbed': 2.70,
    'reefer': 2.90
}

def geocode_location(location, api_key):
    url = "https://api.openrouteservice.org/geocode/search"
    params = {
        "api_key": api_key,
        "text": location,
        "size": 1
    }
    response = requests.get(url, params=params)
    data = response.json()
    coords = data['features'][0]['geometry']['coordinates']
    return coords[::-1]

def get_distance_openrouteservice(origin, destination, api_key):
    try:
        coord1 = geocode_location(origin, api_key)
        coord2 = geocode_location(destination, api_key)
    except:
        return None

    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }
    body = {
        "coordinates": [[coord1[1], coord1[0]], [coord2[1], coord2[0]]]
    }

    response = requests.post(url, json=body, headers=headers)
    if response.status_code != 200:
        return None

    data = response.json()
    distance_meters = data['routes'][0]['summary']['distance']
    distance_miles = distance_meters / 1609.34
    return distance_miles

@app.route('/')
def home_page():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate_lane_price():
    data = request.get_json()
    origin = data.get('origin')
    destination = data.get('destination')
    truck_type = data.get('truck_type', 'dry_van').lower()

    if not origin or not destination:
        return jsonify({"error": "Both 'origin' and 'destination' are required."}), 400

    distance = get_distance_openrouteservice(origin, destination, API_KEY)
    if distance is None:
        return jsonify({"error": "Could not fetch distance. Please check location names."}), 400

    rate_per_mile = RATES.get(truck_type)
    if rate_per_mile is None:
        return jsonify({"error": f"Unknown truck type '{truck_type}'."}), 400

    total_price = rate_per_mile * distance

    return jsonify({
        "origin": origin,
        "destination": destination,
        "truck_type": truck_type,
        "distance_miles": round(distance, 2),
        "rate_per_mile": rate_per_mile,
        "total_price_usd": round(total_price, 2)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
