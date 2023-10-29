import json
import boto3
from botocore.exceptions import ClientError
from elasticsearch import Elasticsearch, RequestsHttpConnection
from boto3.dynamodb.conditions import Key, Attr
import random
import requests

def getDynamoDbData(table, requestData, businessIds):
    if len(businessIds) < 1:
        return 'No restaurant found for the following ids.'

    textString = "Hello! Here are my " + requestData['Categories']['StringValue'] + " restaurant suggestions for " + requestData['PeopleNum']['StringValue'] +" people, on " + requestData['DiningDate']['StringValue'] + " at " + requestData['DiningTime']['StringValue'] + ": Hope you enjoy your meal."
    count = 1
    
    for business in businessIds:
        response = table.query(KeyConditionExpression=Key('id').eq(business))
        if response and len(response['Items']) >= 1:
            response = response['Items'][0]
            address = response['address']
            str = str + ", " + str(count) + ". " + str(response['name']) + ", at " + str(address[0]) + " " + str(address[1])
            count+=1
    return str

def sendSmsToUser(requestData, content):
    
    personto = requestData["PhoneNumber"]["StringValue"]
    client = boto3.client(
    'sns', 
    region_name='us-west-2'
    )

    print("sending sms")

    # Send your sms message.
    client.publish(
        PhoneNumber=personto,
        Message=json.dumps(content)
    )

def lambda_handler(event, context):
    client = boto3.client('sqs','us-west-2')
    queueUrl = 'https://sqs.us-west-2.amazonaws.com/107926647271/restaurantQueue'

    # Receive message from SQS queue
    sqsResponse = client.receive_message(
        QueueUrl=queueUrl,
        AttributeNames=[
            'SequenceNumber'
        ],
        MaxNumberOfMessages=1,
        MessageAttributeNames=[
            'All'
        ],
        VisibilityTimeout=0,
        WaitTimeSeconds=1
    )

    if 'Messages' in sqsResponse:
        esUrl = 'vpc-restaurants-qnhw5k3csjkluudjry67e2z4eu.us-west-2.es.amazonaws.com'
        
        esResponse = Elasticsearch(
            hosts = [{'host': esUrl, 'port': 443}],
            use_ssl = True,
            verify_certs = True,
            connection_class = RequestsHttpConnection
        )

        dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
        table = dynamodb.Table('yelp-restaurants')

        for message in response['Messages']:
            receipt_handle = message['ReceiptHandle']
            req_attributes = message['MessageAttributes']

            # Get cuisines from queue.
            index_category = req_attributes['Categories']['StringValue']

            searchData = esResponse.search(index="restaurants", body={
                                        "query": {
                                        "match": {
                                        "categories.title": index_category
                                        }}})

            restaurantIds = []
            for hit in searchData['hits']['hits']:
                restaurantIds.append(hit['_source']['id'])

            resIds = random.sample(restaurantIds, k=3)

            smsContent = getDynamoDbData(table, req_attributes, resIds)
            #print "DynamoDB Query ResponseData" + resultData

            print("Sending sms to user")
            #send sms to user
            sendSmsToUser(req_attributes, smsContent)

            print("sms sent")
            sqsclient.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle
            )
            
            print(searchData['hits']['total'])


    else:
        return {
        'statusCode': 500,
        'body': json.dumps('Internal Server Error: Fetching message from Queue Failed.')
    }

    return {
        'statusCode': 200,
        'body': response
    }
