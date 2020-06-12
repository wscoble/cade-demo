from flask import Flask, request, Response, render_template, redirect
from .utils import envvar
import json

import boto3

# Default config vals
THEME = 'default' if envvar('THEME') is None else envvar('THEME')
FLASK_DEBUG = 'false' if envvar('FLASK_DEBUG') is None else envvar('FLASK_DEBUG')

# Create the Flask app
app = Flask(__name__)

# Load config values specified above
app.config.from_object(__name__)

# Load configuration vals from a file
app.config.from_envvar('APP_CONFIG', silent=True)

# Only enable Flask debugging if an env var is set to true
app.debug = envvar('FLASK_DEBUG') in ['true', 'True']

# Connect to DynamoDB and get ref to Table
dynamodb = boto3.resource('dynamodb')
table = None
try:
    table = dynamodb.create_table(
        TableName=envvar('IMAGE_INDEX_TABLE'),
        KeySchema=[
            {
                'AttributeName': 'filename',
                'AttributeType': 'S'
            }
        ])
    table.meta.client.get_waiter('table_exists').wait(TableName='users')
except:
    pass


@app.route('/')
def index():
    table = dynamodb.Table(envvar('IMAGE_INDEX_TABLE'))
    files = table.scan().get('Items', [])
    context = {
        'bucket_url': envvar('BUCKET_URL'),
        'files': files
    }
    return render_template('index.html', **context)

@app.route('/upload', methods = ['POST'])
def upload():
    f = request.files['file']
    f.save(f"uploads/{f.filename}")
    s3_client = boto3.client('s3')
    table = dynamodb.Table(envvar('IMAGE_INDEX_TABLE'))
    s3_client.upload_file(
        f"uploads/{f.filename}",
        envvar('IMAGE_BUCKET'),
        f.filename,
        ExtraArgs={'ACL': 'public-read'})
    table.put_item(
        Item={
            'filename': f.filename,
            'original': True
        }
    )
    return redirect('/')

@app.route('/beautify/<filename>')
def beautify(filename):
    sqs_client = boto3.client('sqs')
    sqs_client.send_message(
        QueueUrl=envvar('SQS_QUEUE_URL'),
        MessageBody=json.dumps({'filename': filename})
    )
    return redirect('/')
