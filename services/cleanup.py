import json
import boto3

TABLE_NAME = os.environ.get('NOTES')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    try:
        note_id = event.get('note_id')

        if not note_id:
            print('note_id is not found in the payload')
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'note_id is required'})
            }
        
        table = dynamodb.Table(TABLE_NAME)
        table.delete_item(Key={'note_id': note_id})

        print('Note deleted successfully')

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Note deleted successfully'})
        }

    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal server error'})
        }
