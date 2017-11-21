import sys
import pymysql
import boto3
import botocore
import json
import random
import time
import os

# rds settings
rds_host = os.environ['RDS_HOST']
name = os.environ['RDS_USERNAME']
password = os.environ['RDS_PASSWORD']
db_name = os.environ['RDS_DB_NAME']
helperFunctionARN = os.environ['HELPER_FUNCTION_ARN']

conn = None

# Get the service resource.
lambdaClient = boto3.client('lambda')


def invokeConnCountManager(incrementCounter):
    # return True
    response = lambdaClient.invoke(
        FunctionName=helperFunctionARN,
        InvocationType='RequestResponse',
        Payload='{"incrementCounter":' + str.lower(str(incrementCounter)) + ',"RDBMSName": "Prod_MySQL"}'
    )
    retVal = response['Payload']
    retVal1 = retVal.read()
    return retVal1


def openConnection():
    global conn
    try:
        print("Opening Connection")
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


def lambda_handler(event, context):
    if invokeConnCountManager(True) == "false":
        print ("Not enough Connections available.")
        return False

    item_count = 0
    try:
        openConnection()
        # Introducing artificial random delay to mimic actual DB query time. Remove this code for actual use.
        time.sleep(random.randint(1, 3))
        with conn.cursor() as cur:
            cur.execute("select * from Employees")
            for row in cur:
                item_count += 1
                print(row)
                # print(row)
    except Exception as e:
        # Error while opening connection or processing
        print(e)
    finally:
        print("Closing Connection")
        if(conn is not None and conn.open):
            conn.close()
        invokeConnCountManager(False)

    return "Selected %d items from RDS MySQL table" % (item_count)
