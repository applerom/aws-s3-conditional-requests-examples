import boto3
import json
from botocore.exceptions import ClientError

s3 = boto3.client('s3')

BUCKET_NAME = 'my-bucket-change-to-your-name'
RATE_LIMIT_KEY = 'rate_limits.json'

def atomic_increment(user_id, increment=1, max_attempts=5):
    for attempt in range(max_attempts):
        try:
            # Get the current rate limit data
            response = s3.get_object(Bucket=BUCKET_NAME, Key=RATE_LIMIT_KEY)
            rate_limits = json.loads(response['Body'].read())
            etag = response['ETag']

            # Increment the user's count
            if user_id not in rate_limits:
                rate_limits[user_id] = 0
            rate_limits[user_id] += increment

            # Try to update the object with the new data
            s3.put_object(
                Bucket=BUCKET_NAME,
                Key=RATE_LIMIT_KEY,
                Body=json.dumps(rate_limits),
                IfMatch=etag
            )

            return rate_limits[user_id]

        except ClientError as e:
            if e.response['Error']['Code'] == 'PreconditionFailed':
                # Another process updated the object, retry
                continue
            else:
                # Handle other errors
                raise

    raise Exception("Failed to update rate limit after maximum attempts")

def check_rate_limit(user_id, limit):
    current_count = atomic_increment(user_id)
    return current_count <= limit

# Example usage
user_id = 'user123'
rate_limit = 100

if check_rate_limit(user_id, rate_limit):
    print(f"Request allowed for user {user_id}")
else:
    print(f"Rate limit exceeded for user {user_id}")
