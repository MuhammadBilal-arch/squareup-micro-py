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
            categories = item_data.get('categories', [])
            categories_list = [category['id'] for category in categories]

            calories_count = item_data.get('food_and_beverage_details', {}).get('calorie_count', '')
            print('------------------')
            print(categories_list)
            print('------------------')
            transformed_item = {
                'name': item_data.get('name', ' '),
                'description': item_data.get('description', ''),
                'item_type': item_data.get('product_type', ''),
                'dietary_preferences': dietary_prefs_list,
                'nutrition_contain_following':ingredients_list, 
                'product_from_square': True,
                'square_id':item.get('id', ''),            
                'calories_count': calories_count,
                'category': categories_list,
            }
            transformed_items.append(transformed_item)
            print('------------------')
            print(transformed_items)
            print('------------------')
        node_api_url = 'http://192.168.0.105:1700/api/create-item-sync'
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

# CATEGORIES
@app.route('/categories', methods=['GET'])
def categories():
    auth_header = request.headers.get('Authorization')
    token = None

    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(" ")[1]
    if not token:
        return jsonify({'error': 'Authorization token is missing'}), 401

    result = client.catalog.list_catalog(types="CATEGORY")
    
    if result.is_success():
        catalog_data = result.body  
        items = catalog_data.get('objects', [])

        transformed_items = []
        for item in items:
            item_data = item.get('category_data', {})
                        
            transformed_item = {
                'name': item_data.get('name', ' '),
                'square_id': item.get('id','')
            }
            transformed_items.append(transformed_item)
        
        node_api_url = 'http://192.168.0.105:1700/api/create-category'
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

        # return jsonify(transformed_items) , 200

@app.route('/modifiers', methods=['GET'])
def modifiers():
    auth_header = request.headers.get('Authorization')
    token = None

    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(" ")[1]
    if not token:
        return jsonify({'error': 'Authorization token is missing'}), 401

    result = client.catalog.list_catalog(types="MODIFIER_LIST")
    
    if result.is_success():
        catalog_data = result.body

    items = catalog_data.get('objects', [])
    transformed_items = []

    for item in items:
        item_data = item.get('modifier_list_data', {})
        
        # Prepare the basic structure of the transformed item
        is_single_modifier = item_data.get('selection_type', '') == 'SINGLE'
        is_conversational_modifier = not is_single_modifier  # Assuming any non-SINGLE type is conversational for simplicity

        transformed_item = {
            'name': item_data.get('name', ''),
            'display_name': item_data.get('internal_name', ''),
            'square_id': item.get('id', ''),
            'type': item_data.get('modifier_type', ''),
            'character_limit': item_data.get('max_length', ''),
            'modifier_values': [],
            'conversational_modifiers': is_conversational_modifier,
            'single_modifier_selection': is_single_modifier,
        }

        # Process modifiers if they exist
        modifiers = item_data.get('modifiers', [])
        for modifier in modifiers:
            modifier_detail = modifier.get('modifier_data', {})
            transformed_modifier = {
                'name': modifier_detail.get('name', ''),
                'price': modifier_detail.get('price_money', {}).get('amount', 0) / 100,  # Assuming amount is in cents
                'in_stock': modifier_detail.get('on_by_default', False),
            }
            transformed_item['modifier_values'].append(transformed_modifier)
        
        transformed_items.append(transformed_item)

    # Now, send the transformed items to the node API
    node_api_url = 'http://192.168.0.105:1700/api/create-modifier-sync'
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

    # Return aggregated responses
    if all(response['status_code'] == 200 for response in responses):
        return jsonify(responses), 200
    else:
        return jsonify(responses), 207

if __name__ == '__main__':
    app.run(debug=True)
