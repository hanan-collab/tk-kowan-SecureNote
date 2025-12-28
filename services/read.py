import json
import boto3
import os
from botocore.exceptions import ClientError
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj)
        return super(DecimalEncoder, self).default(obj)

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('NOTES')

def lambda_handler(event, context):    
    try:
        path_params = event.get('pathParameters', {})
        if not path_params:
             return build_response(400, {'message': 'Note ID is missing'})
        
        note_id = path_params.get('note_id')

        body_str = event.get('body')
        if not body_str:
             return build_response(400, {'message': 'Request body is empty'})
        
        try:
            body_json = json.loads(body_str)
        except json.JSONDecodeError:
             return build_response(400, {'message': 'Invalid JSON format'})

        input_password = body_json.get('password')
        if not input_password:
             return build_response(400, {'message': 'Password is required inside request body'})

    except Exception as e:
        return build_response(400, {'message': f'Invalid request: {str(e)}'})

    if note_id == 'test-frontend':
        if input_password == 'password-dummy': 
            return build_response(200, {
                'message': 'Note retrieved and destroyed successfully (MOCK DATA)',
                'content': 'API Gateway dan Lambda sudah terhubung. Semoga komputasi awan dapat A', 
                'salt': 'salt-dummy',
                'created_at': 1709251200,
                'ttl': 1709254800
            })
        else:
             return build_response(403, {'message': 'Invalid Password provided (MOCK)'})

    headers = event.get('headers', {})
    user_agent = headers.get('User-Agent', headers.get('user-agent', '')).lower()
    bot_keywords = ['slackbot', 'twitterbot', 'facebookexternalhit', 'discordbot', 'whatsapp', 'telegrambot']
    if any(bot in user_agent for bot in bot_keywords):
        return build_response(200, {'message': 'Link Preview', 'content': 'Hidden.'})

    table = dynamodb.Table(TABLE_NAME)
    
    try:
        response = table.get_item(Key={'note_id': note_id})
        item = response.get('Item')

        if not item:
            return build_response(404, {'message': 'Note not found or already destroyed.'})

        stored_password = item.get('password')
        
        if input_password != stored_password:
            return build_response(403, {'message': 'Invalid Password provided.'})

        table.delete_item(Key={'note_id': note_id})
        
        return build_response(200, {
            'message': 'Note retrieved and destroyed successfully',
            'content': item.get('content'),
            'salt': item.get('salt'),
            'created_at': item.get('created_at'),
            'ttl': item.get('ttl')
        })

    except Exception as e:
        print(f"Error: {e}")
        return build_response(500, {'message': f"Internal Server Error: {str(e)}"})

def build_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*', 
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }