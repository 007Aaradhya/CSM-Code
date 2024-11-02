import json
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
from decimal import Decimal

def lambda_handler(event, context):
    """
    Main handler for the Lambda function
    """
    print("Received event:", json.dumps(event, indent=2))  # Debug logging
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('aaradhya-users-table')
    
    # Get HTTP method and path from API Gateway event
    http_method = event['httpMethod']
    
    try:
        # Handle OPTIONS request for CORS
        if http_method == 'OPTIONS':
            return build_response(200, {'message': 'CORS enabled'})
            
        # Route requests based on HTTP method
        if http_method == 'GET':
            # List all users - simplified for web app
            response = table.scan()
            items = convert_decimals(response['Items'])  # Convert Decimal values
            return build_response(200, {
                'Items': items,
                'message': 'Users retrieved successfully'
            })
                
        elif http_method == 'POST':
            # Create new user
            try:
                user_data = json.loads(event['body'])
                # Validate required fields
                if 'user_id' not in user_data or 'email' not in user_data:
                    return build_response(400, {
                        'message': 'Missing required fields: user_id and email'
                    })
                
                # Add timestamp
                user_data['createdAt'] = datetime.now().isoformat()
                
                table.put_item(Item=user_data)
                return build_response(201, {
                    'message': 'User created successfully',
                    'user': user_data
                })
            except json.JSONDecodeError:
                return build_response(400, {
                    'message': 'Invalid JSON in request body'
                })
            
        elif http_method == 'PUT':
            # Update user
            try:
                user_data = json.loads(event['body'])
                if 'user_id' not in user_data or 'email' not in user_data:
                    return build_response(400, {
                        'message': 'Missing required fields: user_id and email'
                    })
                
                user_id = user_data['user_id']
                email = user_data['email']
                
                update_expression = 'SET '
                expression_attribute_names = {}
                expression_attribute_values = {}
                
                for key, value in user_data.items():
                    if key not in ['user_id', 'email']:
                        update_expression += f'#{key} = :{key}, '
                        expression_attribute_names[f'#{key}'] = key
                        expression_attribute_values[f':{key}'] = value
                
                if len(expression_attribute_values) == 0:
                    return build_response(400, {
                        'message': 'No fields to update'
                    })
                
                table.update_item(
                    Key={
                        'user_id': user_id,
                        'email': email
                    },
                    UpdateExpression=update_expression[:-2],
                    ExpressionAttributeNames=expression_attribute_names,
                    ExpressionAttributeValues=expression_attribute_values
                )
                return build_response(200, {
                    'message': 'User updated successfully'
                })
            except json.JSONDecodeError:
                return build_response(400, {
                    'message': 'Invalid JSON in request body'
                })
            
        elif http_method == 'DELETE':
            if not event.get('queryStringParameters') or \
               'user_id' not in event['queryStringParameters'] or \
               'email' not in event['queryStringParameters']:
                return build_response(400, {
                    'message': 'Missing required query parameters: user_id and email'
                })
                
            table.delete_item(
                Key={
                    'user_id': event['queryStringParameters']['user_id'],
                    'email': event['queryStringParameters']['email']
                }
            )
            return build_response(200, {
                'message': 'User deleted successfully'
            })
            
        else:
            return build_response(400, {
                'message': 'Unsupported HTTP method'
            })
            
    except ClientError as e:
        print("DynamoDB error:", str(e))  # Debug logging
        return build_response(500, {
            'message': 'Database error',
            'error': str(e)
        })
    except Exception as e:
        print("Unexpected error:", traceback.format_exc())  # More detailed logging
        return build_response(500, {
            'message': 'Internal server error',
            'error': str(e)
        })

def convert_decimals(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, list):
        return [convert_decimals(x) for x in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    return obj

def build_response(status_code, body):
    """
    Build the response object with CORS headers
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
        },
        'body': json.dumps(body)
    }
