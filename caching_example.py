import boto3
from flask import Flask, request, jsonify
from datetime import datetime, timezone

app = Flask(__name__)
s3 = boto3.client('s3')

BUCKET_NAME = 'your-bucket-name'

@app.route('/content/<key>', methods=['GET'])
def get_content(key):
    # Get If-Modified-Since header from request
    if_modified_since = request.headers.get('If-Modified-Since')

    try:
        # Convert If-Modified-Since to datetime object
        if if_modified_since:
            if_modified_since = datetime.strptime(if_modified_since, "%a, %d %b %Y %H:%M:%S GMT").replace(tzinfo=timezone.utc)

        # Attempt to get the object with condition
        response = s3.get_object(
            Bucket=BUCKET_NAME,
            Key=key,
            IfModifiedSince=if_modified_since
        )

        # If we reach here, the content has been modified
        content = response['Body'].read().decode('utf-8')
        last_modified = response['LastModified'].strftime("%a, %d %b %Y %H:%M:%S GMT")

        return jsonify({
            'content': content,
            'last_modified': last_modified
        }), 200, {'Last-Modified': last_modified}

    except s3.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '304':
            # Content not modified, return 304 response
            return '', 304
        else:
            # Handle other errors
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
