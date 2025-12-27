import json
import boto3
import os
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')

# -- Environment Variables --
TABLE_NAME = os.environ.get('NOTES')

def lambda_handler(event, context):    
    try:
        path_params = event.get('pathParameters', {})
        if not path_params:
             return build_response(400, {'message': 'Note ID is missing'})
        
        note_id = path_params.get('note_id')
    except Exception:
        return build_response(400, {'message': 'Invalid request'})

    headers = event.get('headers', {})
    user_agent = headers.get('User-Agent', headers.get('user-agent', '')).lower()
    
    bot_keywords = ['slackbot', 'twitterbot', 'facebookexternalhit', 'discordbot', 'whatsapp', 'telegrambot']
    
    if any(bot in user_agent for bot in bot_keywords):
        print(f"Bot detected: {user_agent}. Preventing deletion.")
        return build_response(200, {
            'message': 'Secure Note Link Preview',
            'content': 'This content is hidden for security reasons. Please open the link directly in your browser.'
        })

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
            'salt': deleted_item.get('salt')          
        })

    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return build_response(404, {'message': 'Note not found or already destroyed.'})
        else:
            print(f"Database error: {e}")
            return build_response(500, {'message': 'Internal Server Error'})
            
    except Exception as e:
        print(f"Unexpected error: {e}")
        return build_response(500, {'message': f"Error: {str(e)}"})

def build_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*', 
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps(body)
    }