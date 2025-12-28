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
ALLOWED_ORIGIN = os.environ.get('ALLOWED_ORIGIN')

def lambda_handler(event, context):    
    try:
        path_params = event.get('pathParameters', {})
        if not path_params:
             return build_response(400, {'message': 'Note ID is missing'})
        
        note_id = path_params.get('note_id')

    except Exception as e:
        return build_response(400, {'message': f'Invalid request: {str(e)}'})

    headers = event.get('headers', {})
    user_agent = headers.get('User-Agent', headers.get('user-agent', '')).lower()
    bot_keywords = ['slackbot', 'twitterbot', 'facebookexternalhit', 'discordbot', 'whatsapp', 'telegrambot']
    if any(bot in user_agent for bot in bot_keywords):
        return build_response(200, {'message': 'Link Preview', 'content': 'Hidden.'})

    table = dynamodb.Table(TABLE_NAME)
    
    try:
        response = table.delete_item(
            Key={
                'note_id': note_id
            },
            ConditionExpression='attribute_exists(note_id)', 
            ReturnValues='ALL_OLD' 
        )
        
        deleted_item = response.get('Attributes')
        
        return build_response(200, {
            'message': 'Note retrieved and destroyed successfully',
            'content': deleted_item.get('content'),
            'password': deleted_item.get('password'),
            'salt': deleted_item.get('salt'),
            'created_at': deleted_item.get('created_at'),
            'ttl': deleted_item.get('ttl')     
        })
    except Exception as e:
        print(f"Error: {e}")
        return build_response(500, {'message': f"Internal Server Error: {str(e)}"})

def build_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': ALLOWED_ORIGIN, 
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }