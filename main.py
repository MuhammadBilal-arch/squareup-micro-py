from flask import Flask, jsonify , request
from dotenv import load_dotenv
from square.client import Client
import requests
import os

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Initialize Square client
client = Client(
    access_token=os.environ['SQUARE_ACCESS_TOKEN'],
    environment='production')

@app.route('/locations', methods=['GET'])
def list_locations():
    result = client.locations.list_locations()
    locations_data = []

    if result.is_success():
        for location in result.body['locations']:
            location_info = {
                "id": location['id'],
                "name": location.get('name', 'N/A')
            }

            # Check if 'address' key exists before attempting to access it
            if 'address' in location and location['address'] is not None:
                address = location['address']
                location_info['address_line_1'] = address.get('address_line_1', 'N/A')
                location_info['locality'] = address.get('locality', 'N/A')
            else:
                location_info['address'] = "No address available"
            
            locations_data.append(location_info)

    elif result.is_error():
        errors = [{"category": error['category'], "code": error['code'], "detail": error['detail']} for error in result.errors]
        return jsonify({"errors": errors}), 400

    return jsonify(locations_data)

@app.route('/list-catalog', methods=['GET'])
def list_catalog():
    auth_header = request.headers.get('Authorization')
    token = None

    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(" ")[1]
    if not token:
        return jsonify({'error': 'Authorization token is missing'}), 401

    # Your existing API call to Square to fetch catalog items
    result = client.catalog.list_catalog(types="ITEM")
    
    if result.is_success():
        catalog_data = result.body  # The actual body of the response from the Square API

        items = catalog_data.get('objects', [])

        # print(dietary_prefs_list)
        transformed_items = []
        for item in items:
            item_data = item.get('item_data', {})
            dietary_preferences = item_data.get('food_and_beverage_details', {}).get('dietary_preferences', [])
            dietary_prefs_list = [dietary_pref.get('standard_name') for dietary_pref in dietary_preferences]
            ingredients = item_data.get('food_and_beverage_details', {}).get('ingredients', [])
            ingredients_list = [dietary_pref.get('standard_name') for dietary_pref in ingredients]
            
            transformed_item = {
                'name': item_data.get('name', ' '),
                'description': item_data.get('description', ''),
                'item_type': item_data.get('product_type', ''),
                'dietary_preferences': dietary_prefs_list,
                'nutrition_contain_following':ingredients_list, 
            }
            transformed_items.append(transformed_item)
        
        node_api_url = 'http://192.168.0.105:1700/api/create-item'
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

        responses = []
        
        for item in transformed_items:
            try:
                node_response = requests.post(node_api_url, json=item, headers=headers)
                response_data = {'status_code': node_response.status_code}
                if node_response.status_code == 200:
                    response_data['data'] = node_response.json()
                else:
                    response_data['error'] = node_response.json()
                responses.append(response_data)
            except requests.exceptions.RequestException as e:
                responses.append({'status_code': 500, 'error': str(e)})
        
        if all(response['status_code'] == 200 for response in responses):
            return jsonify(responses), 200
        else:
            return jsonify(responses), 207

    elif result.is_error():
        # Handle the error from the Square API
        return jsonify(result.errors), 400



if __name__ == '__main__':
    app.run(debug=True)
