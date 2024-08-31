import boto3
import json
from botocore.exceptions import ClientError
from datetime import datetime, timedelta, timezone

s3 = boto3.client('s3')

BUCKET_NAME = 'my-bucket-change-to-your-name'
RATE_LIMIT_PREFIX = 'rate_limits/'

def check_rate_limit(user_id, limit, time_window_seconds):
    current_time = datetime.now(timezone.utc)
    window_start = current_time - timedelta(seconds=time_window_seconds)
    
    # Generate keys for the current time window
    keys = [f"{RATE_LIMIT_PREFIX}{user_id}/{(window_start + timedelta(seconds=i)).timestamp()}" for i in range(limit)]
    
    count = 0
    for key in keys:
        try:
            # Try to create an object. If it succeeds, increment the count.
            s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=b'', IfNoneMatch='*')
            count += 1
            if count >= limit:
                return False  # Rate limit exceeded
        except ClientError as e:
            if e.response['Error']['Code'] == 'PreconditionFailed':
                # Object already exists, continue to next key
                continue
            else:
                # Handle other errors
                raise
    
    return True  # Rate limit not exceeded

# Example usage
user_id = 'user123'
rate_limit = 5
time_window = 60  # 60 seconds

if check_rate_limit(user_id, rate_limit, time_window):
    print(f"Request allowed for user {user_id}")
else:
    print(f"Rate limit exceeded for user {user_id}")
    