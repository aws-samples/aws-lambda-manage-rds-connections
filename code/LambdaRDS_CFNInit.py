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


conn = None

# Get the service resource.
lambdaClient = boto3.client('lambda')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ConnectionsCounter')


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
        sys.exit()


def lambda_handler(event, context):
    
    # For Delete requests, immediately send a SUCCESS response.
    print (event)
    if event['RequestType'] == 'Delete':
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
    return True
