import sys
import pymysql
import boto3
import botocore
import json
import os


# Get the service resource.
lambdaClient = boto3.client('lambda')

testFunctionARN = os.environ['TEST_FUNCTION_ARN']


def invokeTestLambda(functionARN, operation, iterations):

    if operation == 'unit':
        iterations = 1
    for i in range(1, iterations):
        print ('Invoking test function: iteration ' + str(i))
        lambdaClient.invoke(
            FunctionName=functionARN,
            InvocationType='Event'
            )
    return True


def lambda_handler(event, context):
    invokeTestLambda(testFunctionARN, str(event['operation']), int(event['iterations']))
    print('Test Succeeded')
    return True
