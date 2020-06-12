from flask import Flask, request
from time import sleep
from utils import envvar
import boto3, os, random

app = Flask(__name__)


@app.route('/beautify')
def beautify():
    sleep(10)
    body = request.json()
    s3_client = boto3.client('s3')
    table = boto3.client('dynamodb').table(envvar('IMAGE_INDEX_TABLE'))
    new_filename = random.choice(os.listdir('./pretties'))
    s3_client.upload_file(f"pretties/{new_filename}", envvar('IMAGE_BUCKET'), body['filename'])
    table.update_item(
        Key={
            'filename': body['filename']
        },
        UpdateExpression='SET original = false'
    )
    return ''