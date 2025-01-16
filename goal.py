import json
import boto3
import uuid
import datetime
from datetime import timedelta, timezone
from decimal import Decimal
from botocore.exceptions import ClientError
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from nlp_parser import process_text

# Initialize the DynamoDB client
tableName = 'goalTable'
dynamodb = boto3.resource('dynamodb', region_name = 'us-east-1')
table = dynamodb.Table(tableName)

statusPath = '/status'
goalPath = '/goal'
goalsPath = '/goals'

# google-api-key = 'AIzaSyCsT4kUgc7uSGGzwSHMoT3ask-8B9cDo84'

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

CREDS = None



def get_google_credentials():
    """Get Google credentials from AWS Parameter Store."""
    ssm = boto3.client('ssm')
    try:
        # Get service account credentials from Parameter Store
        response = ssm.get_parameter(
            Name='google-auth-token',  # Your parameter name
            WithDecryption=True
        )
        service_account_info = json.loads(response['Parameter']['Value'])
        
        # Create credentials object
        credentials = Credentials.from_authorized_user_info(
            service_account_info,
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        return credentials
    except ClientError as e:
        print(f"Error getting credentials from Parameter Store: {e}")
        raise




def lambda_handler(event, context):


    # load_google_calendar_api() # set the api 
    
    print("Event Data:", json.dumps(event)) 
    
    try:
        httpsMethod = event['httpMethod']
        path = event['path']
    except KeyError as e:
        print(f"KeyError: {e}")
        return buildResponse(500, 'Internal Server Error')
    
    if path == statusPath and httpsMethod == 'GET':
        response = buildResponse(200, "Service is available")
    elif path == goalPath:
        try:
            if httpsMethod == 'GET':
                goalId = event['queryStringParameters']['goalId']
                response = getGoal(goalId)
            elif httpsMethod == 'POST':
                body = json.loads(event['body'])
                response = createGoal(body)
            elif httpsMethod == 'PATCH':
                body = json.loads(event['body'])
                response = modifyGoal(body['goalId'], body['updateKey'], body['updateValue'])
            elif httpsMethod == 'DELETE':
                goalId = event['queryStringParameters']['goalId']
                response = deleteGoal(goalId)
            else:
                response = buildResponse(405, 'Method Not Allowed')
        except KeyError as e:
            print(f"KeyError: {e}")
            response = buildResponse(400, 'Bad Request')
        except json.JSONDecodeError:
            response = buildResponse(400, 'Invalid JSON')
    elif path == goalsPath and httpsMethod == 'GET':
        response = getAllGoals()
    else:
        response = buildResponse(404, '404 Not Found')
    
    return response

def getGoal(goalId):
    try:
        response = table.get_item(Key={'goalId': goalId})
        return buildResponse(200, response.get('Item'))
    except ClientError as e:
        print('Error:', e)
        return buildResponse(400, e.response['Error']['Message'])

def getAllGoals():
    try:
        response = table.scan()
        data = response.get('Items', [])
        return buildResponse(200, data)
    except ClientError as e:
        print('Error:', e)
        return buildResponse(400, e.response['Error']['Message'])

def createGoal(requestBody):
    try:
        # If input is a text string, parse it first
        if isinstance(requestBody, str):
            parsed_reminder = process_text(requestBody)
            requestBody = {
                'title': parsed_reminder['title'],
                'description': parsed_reminder['description'],
                'startTime': parsed_reminder['startTime'],
                'endTime': parsed_reminder['endTime'],
                'timeZone': parsed_reminder['timeZone'],
                'reminder': parsed_reminder['reminder']
            }
        
        # Generate a unique ID for the goal
        goalId = str(uuid.uuid4())
        requestBody['goalId'] = goalId
        requestBody['createdDate'] = int(datetime.datetime.now(timezone.utc).strftime('%Y%m%d'))

        # Get Google Calendar credentials and create event
        creds = get_google_credentials()
        service = build("calendar", "v3", credentials=creds)

        event = {
            'summary': requestBody['title'],
            'description': requestBody['description'],
            'start': {
                'dateTime': requestBody['startTime'],
                'timeZone': requestBody['timeZone'],
            },
            'end': {
                'dateTime': requestBody['endTime'],
                'timeZone': requestBody['timeZone'],
            }
        }

        # Insert event to Google Calendar
        calendar_event = service.events().insert(calendarId='primary', body=event).execute()
        
        # Add calendar event ID to the goal data
        requestBody['calendarEventId'] = calendar_event['id']
        
        # Save to DynamoDB
        table.put_item(Item=requestBody)
        body = {
            'Operation': 'SAVE',
            'Message': 'SUCCESS',
            'Item': requestBody
        }
        return buildResponse(200, body)
    except ClientError as e:
        print('Error', e)
        return buildResponse(400, e.response['Error']['Message'])

def modifyGoal(goalId, updateKey, updateValue):
    try:
        response = table.update_item(Key={'goalId':goalId}, 
                                     UpdateExpression=f'SET {updateKey} = :value',
                                     ExpressionAttributeValues={':value': updateValue},
                                     ReturnValues='UPDATED_NEW')
        body = {
            'Operation':'UPDATE',
            'Message':'SUCCESS',
            'Item': response
        }
        return buildResponse(200,body)
    except ClientError as e:
        print('Error', e)
        return buildResponse(400, e.response['Error']['Message'])

def deleteGoal(goalId):
    try:
        response = table.delete_item(Key={'goalId':goalId},
                                     ReturnValues='ALL_OLD')
        body = {
            'Operation':'DELETE',
            'Message':'SUCCESS',
            'Item': response
        }
        return buildResponse(200,body)
    except ClientError as e:
        print('Error', e)
        return buildResponse(400, e.response['Error']['Message'])


def buildResponse(statusCode, body=None):
    response = {
        'statusCode': statusCode,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }
    }

    if body is not None:
        response['body'] = json.dumps(body, cls=DecimalEnconder)

    return response

class DecimalEnconder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            if obj % 1 == 0:
                return int(obj)
            else:
                return float(obj)
        return json.JSONEncoder.default(self,obj)