import json
import requests
from nlp_parser import ReminderParser

phone_number_id = "+14406667376"
class WhatsAppHandler:
    def __init__(self, phone_number_id, access_token):
        self.url = f"https://graph.facebook.com/v16.0/{phone_number_id}/messages"
        self.access_token = access_token
        self.parser = ReminderParser()

    def send_message(self, to, message_text):
        """Send a WhatsApp message"""
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message_text}
        }
        return requests.post(self.url, headers=headers, json=payload)

    def process_message(self, sender, message_text):
        """Process incoming message and send response"""
        try:
            # Parse the reminder text
            result = self.parser.parse_reminder_text(message_text)
            
            # Format response message
            response = (
                f"I've parsed your reminder:\n"
                f"Title: {result['title']}\n"
                f"Start Time: {result['startTime']}\n"
                f"Time Zone: {result['timeZone']}\n"
                f"Reminder set for: {result['reminder']} minutes before\n\n"
                f"Is this correct? Reply with 'yes' to confirm or 'no' to try again."
            )
            
            # Send response
            self.send_message(sender, response)
            
            return {
                'statusCode': 200,
                'body': json.dumps({'status': 'Message processed'})
            }
            
        except Exception as e:
            error_message = (
                "Sorry, I couldn't process that reminder. "
                "Please try rephrasing it like: 'remind me to call John in 2 hours'"
            )
            self.send_message(sender, error_message)
            return {
                'statusCode': 500,
                'body': json.dumps({'status': 'Error processing message', 'error': str(e)})
            }

def lambda_handler(event, context):
    """AWS Lambda handler"""
    # Load configuration
    PHONE_NUMBER_ID = "YOUR_PHONE_NUMBER_ID"
    ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"
    
    # Initialize handler
    whatsapp = WhatsAppHandler(PHONE_NUMBER_ID, ACCESS_TOKEN)
    
    try:
        # Parse incoming webhook
        body = json.loads(event['body'])
        
        # Extract message details
        message = body['entry'][0]['changes'][0]['value']['messages'][0]
        sender = message['from']
        message_text = message['text']['body']
        
        # Process message and send response
        return whatsapp.process_message(sender, message_text)
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        } 