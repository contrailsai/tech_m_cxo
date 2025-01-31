import env
import aiohttp
import aioboto3
from typing import Optional, Callable, Any, Awaitable

async def s3_uploader(s3_key: str, video_src: str) -> None:
    bucket_name = env.aws_s3_bucket_name

    session = aioboto3.Session(aws_access_key_id=env.aws_access_key_id, aws_secret_access_key=env.aws_access_key_secret)
    async with session.client('s3', region_name=env.region_name) as s3_client:
        async with aiohttp.ClientSession() as session:
            async with session.get(video_src) as response:
                if response.status == 200:
                    temp_file_path = 'temp_video.mp4'
                    with open(temp_file_path, 'wb') as f:
                        async for chunk in response.content.iter_any():
                            f.write(chunk)

                    # Upload the file to S3
                    await s3_client.upload_file(
                        Filename=temp_file_path,
                        Bucket=bucket_name,
                        Key=s3_key,
                        ExtraArgs={'ContentType': 'video/mp4'}
                    )

    print("FILE UPLOADED")

async def sqs_sender(message_body: str) -> str:
    queue_url = env.aws_sqs_queue_url
    session = aioboto3.Session(
        aws_access_key_id=env.aws_access_key_id,
        aws_secret_access_key=env.aws_access_key_secret
    )

    async with session.client('sqs', region_name=env.region_name) as sqs_client:
        response = await sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=message_body
        )

    print(f"Message sent with ID: {response['MessageId']}")
    return response['MessageId']