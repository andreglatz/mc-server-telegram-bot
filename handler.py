import os
import json
import boto3
import requests

ec2_instance_id = os.environ['EC2_INSTANCE_ID']
telegram_token = os.environ['TELEGRAM_TOKEN']
users_allowed = os.environ['USERS_ALLOWED'].split(',')


def handle_bot(event, context):
    try:
        json_body = json.loads(event['body'])

        message = json_body['message']
        chat_id = message['chat']['id']

        print(f'Chat ID: {chat_id}')
        print(f'Received message: {message["text"]}')

        if message['from']['username'] not in users_allowed:
            send_message(chat_id, 'You are not allowed to use this bot')
            return {'statusCode': 200}

        if message['text'] == '/enable':
            start_server()
            send_message(chat_id, 'Server started')
        elif message['text'] == '/disable':
            stop_server()
            send_message(chat_id, 'Server stopped')
        elif message['text'] == '/status' or message['text'] == '/start':
            status = get_status()
            send_message(chat_id, status)
        else:
            send_message(chat_id, 'Invalid command')

        return {'statusCode': 200}
    except Exception as e:
        print(e)
        return {'statusCode': 500}


def start_server():
    ec2 = boto3.client('ec2')
    ec2.start_instances(InstanceIds=[ec2_instance_id])


def stop_server():
    ec2 = boto3.client('ec2')
    ec2.stop_instances(InstanceIds=[ec2_instance_id])


def get_status():
    ec2 = boto3.client('ec2')
    response = ec2.describe_instances(InstanceIds=[ec2_instance_id])

    status = response['Reservations'][0]['Instances'][0]['State']['Name']
    status = f'Server is {status}'

    if status == 'Server is running':
        public_ip = response['Reservations'][0]['Instances'][0]['PublicIpAddress']
        status += f' at IP: {public_ip}'

    return status


def send_message(chat_id, text):
    url = f'https://api.telegram.org/bot{telegram_token}/sendMessage'
    data = {'chat_id': chat_id, 'text': text}
    requests.post(url, data=data)
