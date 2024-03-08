from flask import Flask, jsonify , request
# from dotenv import load_dotenv
from square.client import Client
from flask_cors import CORS
import requests

# Load environment variables
# load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

 # Initialize Square client
# client = Client(
#     access_token=os.environ['SQUARE_ACCESS_TOKEN'],
#     environment='production')

# baseUrl = 'http://192.168.18.11:1700/api/'
baseUrl = 'https://square-strapi-production.up.railway.app/api/'

@app.route('/items', methods=['GET'])
def list_catalog():
    square_access_token = request.headers.get('Square-Access-Token')

    if not square_access_token:
        return jsonify({'error': 'Square access token is missing'}), 401

    # Initialize the Square client with the token from the frontend
    client = Client(
        access_token=square_access_token,
        environment='production'
    )
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
            variations = item_data.get('variations', [])
            all_variations = [{
                    'name': variation.get('item_variation_data', {}).get('name', ''),
                    'price': variation.get('item_variation_data', {}).get('price_money', {}).get('amount', 0) / 100,  # Assuming price is in cents
                    'sku': variation.get('item_variation_data', {}).get('sku', ''),
                    'weight': '',
                    'unit': '',
                } for variation in variations]
            # return jsonify(all_variations,'Variations')
            modifier_list_info = item_data.get('modifier_list_info', [])
            modifiers = [info['modifier_list_id'] for info in modifier_list_info]
            dietary_preferences = item_data.get('food_and_beverage_details', {}).get('dietary_preferences', [])
            dietary_prefs_list = [dietary_pref.get('standard_name') for dietary_pref in dietary_preferences]
            ingredients = item_data.get('food_and_beverage_details', {}).get('ingredients', [])
            ingredients_list = [dietary_pref.get('standard_name') for dietary_pref in ingredients]
            categories = item_data.get('categories', [])
            categories_list = [category['id'] for category in categories]

            calories_count = item_data.get('food_and_beverage_details', {}).get('calorie_count', '')

        if 'custom_attribute_values' in item:
            custom_attribute_values = item['custom_attribute_values']
            custom_attribute_definition_ids = [value['custom_attribute_definition_id'] for value in custom_attribute_values.values()]

            # return jsonify(custom_attribute_definition_ids)
            # return
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
                'modifiers': modifiers,
                'filteredAttributes': custom_attribute_definition_ids,
                'all_variations': all_variations
                
            }
            transformed_items.append(transformed_item)

        node_api_url = f'{baseUrl}create-item-sync'
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
        return jsonify(responses)
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
    square_access_token = request.headers.get('Square-Access-Token')

    if not square_access_token:
        return jsonify({'error': 'Square access token is missing'}), 401

    # Initialize the Square client with the token from the frontend
    client = Client(
        access_token=square_access_token,
        environment='production'
    )
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
        node_api_url = f'{baseUrl}create-category'        
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
    square_access_token = request.headers.get('Square-Access-Token')

    if not square_access_token:
        return jsonify({'error': 'Square access token is missing'}), 401

    # Initialize the Square client with the token from the frontend
    client = Client(
        access_token=square_access_token,
        environment='production'
    )
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

    node_api_url = f'{baseUrl}create-modifier-sync'
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

@app.route('/custom-attributes', methods=['GET'])
def custom_attributes():
    square_access_token = request.headers.get('Square-Access-Token')

    if not square_access_token:
        return jsonify({'error': 'Square access token is missing'}), 401

    # Initialize the Square client with the token from the frontend
    client = Client(
        access_token=square_access_token,
        environment='production'
    )
    auth_header = request.headers.get('Authorization')
    token = None

    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(" ")[1]
    if not token:
        return jsonify({'error': 'Authorization token is missing'}), 401

    result = client.catalog.list_catalog(types="CUSTOM_ATTRIBUTE_DEFINITION")
    
    if result.is_success():
        catalog_data = result.body

    items = catalog_data.get('objects', [])
    transformed_items = []
    # return jsonify(items)
    for item in items:
        print("Processing item:", item)
        item_data = item.get('custom_attribute_definition_data', {})
        precision = item_data.get('number_config', {}).get('precision', None)
    
        # Initialize transformed_item with properties common to all items
        transformed_item = {
            'name': item_data.get('name', ''),
            'type': item_data.get('type', ''),
            'key': item_data.get('key', ''),
            'square_id': item.get('id', ''),
            'precision': precision,  # Note the typo correction from 'percision' to 'precision'
        }

    # Additional logic for 'SELECTION' type items
        if item_data.get('type') == 'SELECTION' and 'selection_config' in item_data:
            allowed_selections = item_data['selection_config'].get('allowed_selections', [])
            selections = [{'value': selection['name'], 'square_id': selection.get('uid', '')} for selection in allowed_selections]
            transformed_item['attribute_values'] = selections
    
         # Add the transformed item to the list
        transformed_items.append(transformed_item)
        # return jsonify(transformed_items)
    # return
    # Now, send the transformed items to the node API
    node_api_url = f'{baseUrl}create-sync-attribute'
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
        }

    responses = []
    print(len(transformed_items),'___list_')
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

@app.route('/discounts', methods=['GET'])
def discounts():
    square_access_token = request.headers.get('Square-Access-Token')

    if not square_access_token:
        return jsonify({'error': 'Square access token is missing'}), 401

    # Initialize the Square client with the token from the frontend
    client = Client(
        access_token=square_access_token,
        environment='production'
    )
    auth_header = request.headers.get('Authorization')
    token = None

    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(" ")[1]
    if not token:
        return jsonify({'error': 'Authorization token is missing'}), 401

    result = client.catalog.list_catalog(types="DISCOUNT")
    
    if result.is_success():
        catalog_data = result.body

    items = catalog_data.get('objects', [])
    transformed_items = []
    # return jsonify(items)
    for item in items:

        item_data = item.get('discount_data', {})
        if item_data.get('discount_type') in ['FIXED_PERCENTAGE', 'VARIABLE_PERCENTAGE']:
            discount_value = item_data.get('percentage', '0')   # Append % symbol for clarity
        elif item_data.get('discount_type') in ['FIXED_AMOUNT', 'VARIABLE_AMOUNT']:
            # Assuming amount is in cents and we want to convert it to dollars
            amount = item_data.get('amount_money', {}).get('amount', 0) / 100
            discount_value = amount  # Format as a dollar value
        else:
            discount_value = 'N/A'  # Default case if discount type is unknown

    
        # Initialize transformed_item with properties common to all items
        transformed_item = {
            'name': item_data.get('name', ''),
            'type': item_data.get('discount_type', ''),
            'discount': discount_value,
            'square_id': item.get('id', ''),

        }    
         # Add the transformed item to the list
        transformed_items.append(transformed_item)
        # return jsonify(transformed_items)

    node_api_url = f'{baseUrl}create-sync-discount'
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
