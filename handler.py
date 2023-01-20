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

        message = json_body['message']['text']
        username = json_body['message']['from']['username']
        chat_id = json_body['message']['chat']['id']

        print(f'Chat ID: {chat_id}')
        print(f'Received message: {message}')

        if username not in users_allowed:
            send_message(chat_id, 'You are not allowed to use this bot')
            return {'statusCode': 200}

        if message == '/enable':
            start_server(chat_id)
        elif message == '/disable':
            stop_server(chat_id)
        elif message == '/status' or message == '/start':
            get_status(chat_id)
        else:
            send_message(chat_id, 'Invalid command')

        return {'statusCode': 200}
    except Exception as e:
        print(e)
        return {'statusCode': 500}


def start_server(chat_id: str):
    start_instance()
    send_message(chat_id, 'Server is starting...')


def start_instance():
    ec2 = boto3.client('ec2')
    ec2.start_instances(InstanceIds=[ec2_instance_id])


def stop_server(chat_id: str):
    stop_instance()
    send_message(chat_id, 'Server is stopping')


def stop_instance():
    ec2 = boto3.client('ec2')
    ec2.stop_instances(InstanceIds=[ec2_instance_id])


def get_status(chat_id: str):
    infos = get_instance_infos()

    status = infos.get('status')
    ip = infos.get('ip')

    status_message = f'Server status: {status.upper()}'

    if status == 'running':
        status_message += f' at {ip}'

    send_message(chat_id, status_message)


def get_instance_infos():
    ec2 = boto3.client('ec2')
    response = ec2.describe_instances(InstanceIds=[ec2_instance_id])

    status: str = response['Reservations'][0]['Instances'][0]['State']['Name']
    ip: str = response['Reservations'][0]['Instances'][0]['PublicIpAddress']

    infos = {'ip': ip, 'status': status}

    return infos


def send_message(chat_id, text):
    url = f'https://api.telegram.org/bot{telegram_token}/sendMessage'
    data = {'chat_id': chat_id, 'text': text}
    requests.post(url, data=data)
