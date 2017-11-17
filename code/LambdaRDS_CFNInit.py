import sys
import pymysql
import boto3
import botocore
import json
import os
from botocore.vendored import requests

# rds settings
rds_host = os.environ['RDS_HOST']
name = os.environ['RDS_USERNAME']
password = os.environ['RDS_PASSWORD']
db_name = os.environ['RDS_DB_NAME']

SUCCESS = "SUCCESS"
FAILED = "FAILED"


conn = None

# Get the service resource.
lambdaClient = boto3.client('lambda')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DDB_TABLE_NAME'])


def openConnection():
    global conn
    try:
        #print("Opening Connection")
        if(conn is None):
            conn = pymysql.connect(
                rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
        elif (not conn.open):
            # print(conn.open)
            conn = pymysql.connect(
                rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)

    except Exception as e:
        print (e)
        print("ERROR: Unexpected error: Could not connect to MySql instance.")
        raise e


# CloudFormation uses a pre-signed S3 URL to receive the response back from the custom resources managed by it. This is a simple function
# which shall be used to send the response back to CFN custom resource by performing PUT request to the pre-signed S3 URL.
def sendResponse(event, context, responseStatus, responseData, physicalResourceId):
    responseUrl = event['ResponseURL']

    print responseUrl

    responseBody = {}
    responseBody['Status'] = responseStatus
    responseBody['Reason'] = 'See the details in CloudWatch Log Stream: ' + \
        context.log_stream_name
    responseBody['PhysicalResourceId'] = physicalResourceId or context.log_stream_name
    responseBody['StackId'] = event['StackId']
    responseBody['RequestId'] = event['RequestId']
    responseBody['LogicalResourceId'] = event['LogicalResourceId']
    responseBody['Data'] = responseData

    json_responseBody = json.dumps(responseBody)

    print "Response body:\n" + json_responseBody

    headers = {
        'content-type': '',
        'content-length': str(len(json_responseBody))
    }

    try:
        response = requests.put(responseUrl,
                                data=json_responseBody,
                                headers=headers)
        print "Status code: " + response.reason
    except Exception as e:
        print "send(..) failed executing requests.put(..): " + str(e)


def lambda_handler(event, context):

    # For Delete requests, immediately send a SUCCESS response.
    print (event)
    responseData = {}
    if event['RequestType'] == 'Delete':
        sendResponse(event, context, FAILED, responseData, None)
        return True

    try:
        openConnection()

        with conn.cursor() as cur:
             # create table
            cur.execute(
                "Create Table  if not exists Employees (EmployeeID int AUTO_INCREMENT Primary Key, FirstName varchar(50), LastName varchar(50))")

            # insert sample data
            cur.execute(
                "Insert into Employees (EmployeeID, FirstName, LastName) Values (null, \"John\", \"Smith\")")
            cur.execute(
                "Insert into Employees (EmployeeID, FirstName, LastName) Values (null, \"Jane\", \"Doe\")")
            cur.execute(
                "Insert into Employees (EmployeeID, FirstName, LastName) Values (null, \"Bob\", \"Rogers\")")
            conn.commit()
    except Exception as e:
        # Error while opening connection or processing
        print(e)
    finally:
        #print("Closing Connection")
        if(conn is not None and conn.open):
            conn.close()

    # insert a row into DynamoDB

    try:

        table.put_item(
            Item={
                'RDBMSName': 'Prod_MySQL',
                'MaxConnections': 50,
                'RemainingConnections': 50
            },
            ConditionExpression='attribute_not_exists(RDBMSName)'
        )
    except Exception as e:
        # Error while inserting into DDB
        print(e)

    # send response back to CFN
    sendResponse(event, context, SUCCESS, responseData, None)
    return True
