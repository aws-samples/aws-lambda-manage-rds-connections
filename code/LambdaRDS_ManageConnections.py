import sys
import boto3
import botocore
from datetime import datetime
import os

# Get the service resource.
dynamodb = boto3.resource('dynamodb')
cloudWatch = boto3.client('cloudwatch')
table = dynamodb.Table(os.environ['DDB_TABLE_NAME'])


def publishMetrics(connectionCount, errorCount, RDBMSName):
    #return
    cloudWatch.put_metric_data(
        Namespace='RDSLambda',
        MetricData=[
            {
                'MetricName': 'Remaining Connections',
                'Dimensions': [
                    {
                        'Name': 'DBName',
                        'Value': RDBMSName
                    },
                ],
                'Timestamp': datetime.now(),
                'Value': connectionCount,
                'Unit': 'Count',
                'StorageResolution': 1
            },
            {
                'MetricName': 'NoConnLeftError',
                'Dimensions': [
                    {
                        'Name': 'DBName',
                        'Value': RDBMSName
                    },
                ],
                'Timestamp': datetime.now(),
                'Value': errorCount,
                'Unit': 'Count',
                'StorageResolution': 1
            }
        ])


def checkConnectionCount(RDBMSName):
    allowConnection = True
    try:

        item = table.update_item(
            Key={
                'RDBMSName': RDBMSName
            },
            UpdateExpression='SET RemainingConnections = RemainingConnections - :count',
            ConditionExpression='RemainingConnections > :minCount',
            ExpressionAttributeValues={
                ':count': 1,
                ':minCount': 0
            },
            ReturnValues='UPDATED_NEW'
        )
        # Publish custom metrics
        publishMetrics(int(item['Attributes']['RemainingConnections']), 0, RDBMSName)

        # connection found, report no error
        # publishErrorMetric(0)
        # print ('RemainingConnections: ' + str(item['Attributes']['RemainingConnections']))
        # print ("Borrow Connection: Total Connections remaining:{}".format(item['Attributes']['RemainingConnections']))
        # print (item)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            # no connections left, publish 0
            # Publish Error Metric
            publishMetrics(0, 1, RDBMSName)
            allowConnection = False
        else:
            raise e
    return allowConnection


def returnConnectionToPool(RDBMSName):
    connectionReturned = True
    try:
        item = table.update_item(
            Key={
                'RDBMSName': RDBMSName
            },
            UpdateExpression='SET RemainingConnections = RemainingConnections + :count',
            ConditionExpression='RemainingConnections < MaxConnections',
            ExpressionAttributeValues={
                ':count': 1
            },
            ReturnValues='UPDATED_NEW'
        )
        # Publish custom metric and no error
        publishMetrics(int(item['Attributes']['RemainingConnections']), 0, RDBMSName)
        # print ("Return Connection: Total Connections remaining:{}".format(item['Attributes']['RemainingConnections']))
        # print (item)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            # All connections remaining, publish max
            # Publish Error
            publishMetrics(20, 1, RDBMSName)
            connectionReturned = False
        else:
            raise e
    return connectionReturned


def lambda_handler(event, context):
    result = True
    # print("incrementCounter: {}".format(event['incrementCounter']))
    if (str(event['incrementCounter']) == "True"):
        # print('Invoking checkConnectionCount')
        result = checkConnectionCount(event['RDBMSName'])
    else:
        # print('Invoking returnConnectionToPool')
        result = returnConnectionToPool(event['RDBMSName'])
    return result
