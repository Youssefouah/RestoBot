#LF0

import json
import boto3

def lambda_handler(event, context):
    client = boto3.client('lex-runtime')
        
    response = client.post_text(
        botName = 'DiningConcierge',
        botAlias = 'lexLuthor',
        userId = "12345", #event["userId"]
        inputText = event["message"]
    )   
    
    return {
        'statusCode': 200,
        'headers': { 
            "Access-Control-Allow-Origin": "*" 
        },
        'body': json.dumps(response['message'])
    }
