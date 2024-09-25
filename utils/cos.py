from qcloud_cos import CosConfig, CosServiceError
from qcloud_cos import CosS3Client
from sts.sts import Sts
from django_saas.settings import TENCENT_COS_ID, TENCENT_COS_KEY

def create_bucket(bucket,region="ap-chengdu"):
    config = CosConfig(Region=region, SecretId=TENCENT_COS_ID, SecretKey=TENCENT_COS_KEY)
    client = CosS3Client(config)
    client.create_bucket(Bucket=bucket, ACL='public-read')
    cors_config = {
        'CORSRule': [
            {
                'AllowedOrigin': '*',
                'AllowedMethod': ['GET', 'POST', 'HEAD', 'PUT', 'DELETE'],
                'AllowedHeader': '*',
                'ExposeHeader': '*',
                'MaxAgeSeconds': 500
            }
        ]
    }
    client.put_bucket_cors(Bucket=bucket, CORSConfiguration=cors_config)

def upload_file(bucket, region, file_object, key):
    config = CosConfig(Region=region, SecretId=TENCENT_COS_ID, SecretKey=TENCENT_COS_KEY)
    client = CosS3Client(config)
    client.upload_file_from_buffer(
        Bucket=bucket,
        Body=file_object,
        Key=key
    )
    return "https://{}.cos.{}.myqcloud.com/{}".format(bucket, region, key)

def delete_file(bucket, region, key):
    config = CosConfig(Region=region, SecretId=TENCENT_COS_ID, SecretKey=TENCENT_COS_KEY)
    client = CosS3Client(config)
    client.delete_object(
        Bucket=bucket,
        Key=key
    )

def delete_file_list(bucket, region, key_list):
    config = CosConfig(Region=region, SecretId=TENCENT_COS_ID, SecretKey=TENCENT_COS_KEY)
    client = CosS3Client(config)
    objects = {
        "Quiet": "true",
        "Object": key_list
    }
    client.delete_objects(
        Bucket=bucket,
        Delete=objects
    )

def credential(bucket, region):
    config = {
        'duration_seconds': 1800,
        'secret_id': TENCENT_COS_ID,
        'secret_key': TENCENT_COS_KEY,
        'region': region,
        'bucket': bucket,
        'allow_prefix': '*',
        'allow_actions': [
            '*'
        ],
    }
    sts = Sts(config)
    data_dict = sts.get_credential()
    return data_dict

def check_file(bucket, region, key):
    config = CosConfig(Region=region, SecretId=TENCENT_COS_ID, SecretKey=TENCENT_COS_KEY)
    client = CosS3Client(config)
    data = client.head_object(Bucket=bucket, Key=key)
    return data

def delete_bucket(bucket,region):
    config = CosConfig(Region=region, SecretId=TENCENT_COS_ID, SecretKey=TENCENT_COS_KEY)
    client = CosS3Client(config)
    try:
        while 1:
            part_objects = client.list_objects(Bucket=bucket)
            contents = part_objects.get('Contents')
            if not contents:
                break
            objects = {
                "Quiet": "true",
                "Object": [{"Key": item["Key"]} for item in contents]
            }
            client.delete_objects(Bucket=bucket, Delete=objects)
            if part_objects["IsTruncated"] == "false":
                break
        while 1:
            part_uploads = client.list_objects(Bucket=bucket)
            uploads = part_uploads.get('Upload')
            if not uploads:
                break
            for item in uploads:
                client.abort_multipart_upload(bucket, item["Key"], item["UploadId"])
            if part_uploads["IsTruncated"] == "false":
                break
        client.delete_bucket(Bucket=bucket)
    except CosServiceError as e:
        pass
