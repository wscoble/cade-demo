from flask import Flask, request
from time import sleep
import boto3, os, random

app = Flask(__name__)
def envvar(key):
    return os.environ.get(key)

dynamodb = boto3.resource('dynamodb')

@app.route('/', methods=['POST'])
def beautify():
    body = request.json
    s3_client = boto3.client('s3')
    table = dynamodb.Table(envvar('IMAGE_INDEX_TABLE'))
    requested_file = table.get_item(Key={'filename': body['filename']})['Item']
    if requested_file['original']:
        new_filename = random.choice(os.listdir('./pretties'))
        updated_filename = '.'.join(body['filename'].split('.')[:-1]) + '.' + new_filename.split('.')[-1]
        s3_client.upload_file(
            f"pretties/{new_filename}",
            envvar('IMAGE_BUCKET'),
            updated_filename,
            ExtraArgs={'ACL': 'public-read'}
        )
        if updated_filename != requested_file['filename']:
            table.delete_item(
                Key={
                    'filename': requested_file['filename']
                }
            )
            table.put_item(
                Item={
                    'filename': updated_filename,
                    'original': False
                }
            )
        else:
            table.update_item(
                Key={
                    'filename': requested_file['filename']
                },
                UpdateExpression='SET original = :original',
                ExpressionAttributeValues={
                    ':original': False
                }
            )
    return ''