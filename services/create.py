import json
import boto3
import uuid
import time
import os
from datetime import datetime, timezone

dyanomodb = boto3.resource('dynamodb')
scheduler = boto3.client('scheduler')

# -- Environment Variables --
TABLE_NAME = os.environ.get('NOTES')
CLEANUP_TARGET_ARN = os.environ.get('CLEANUP_TARGET_ARN')
SCHEDULER_ROLE_ARN = os.environ.get('SCHEDULER_ROLE_ARN')
APP_BASE_URL = os.environ.get('APP_BASE_URL')
DEFAULT_TTL_MINUTES = 60

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        content = body.get('content')
        password = body.get('password')
        salt = body.get('salt')

        minutes_to_expire = body.get('ttl', DEFAULT_TTL_MINUTES)

        if not content:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Content is required'})
            }

        if not password:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Password is required'})
            }
        
        note_id = str(uuid.uuid4())
        current_time = int(time.time())
        expiry_time = current_time + (minutes_to_expire * 60)

        item = {
            'note_id': note_id,
            'content': content,
            'created_at': current_time,
            'ttl': expiry_time,
            'password': password,
            'salt': salt
        }

        # -- Create shareable link --
        shareable_link = f"{APP_BASE_URL}/read/{note_id}"

        # -- Save note to DynamoDB --
        table = dyanomodb.Table(TABLE_NAME)
        table.put_item(Item=item)

        # -- Schedule cleanup job --
        schedule_date = datetime.fromtimestamp(expiry_time, tz=timezone.utc)
        schedule_str = schedule_date.strftime('%Y-%m-%dT%H:%M:%S')

        try:
            scheduler.create_schedule(
                Name=f"cleanup-{note_id}",
                ScheduleExpression=f"at({schedule_str})",
                Target={
                    'Arn': CLEANUP_TARGET_ARN,
                    'RoleArn': SCHEDULER_ROLE_ARN,
                    'Input': json.dumps({'note_id': note_id})
                },
                FlexibleTimeWindow={'Mode': 'OFF'},                 
                ActionAfterCompletion='DELETE'
            )
        except Exception as e:
            # Dynamodb TTL as backup cleanup
            print(f"Error scheduling cleanup job: {e}")

        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Note created successfully',
                'note_id': note_id,
                'link': shareable_link,
                'expires_at': expiry_time
            })
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'Internal server error: {str(e)}'})
        }