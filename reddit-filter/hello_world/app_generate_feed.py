from datetime import datetime
from feedgen.feed import FeedGenerator
import boto3
import os

dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
table = dynamodb.Table(os.environ['TABLE_NAME'])

s3 = boto3.resource('s3')
bucket = s3.Bucket(os.environ['BUCKET_NAME'])


def lambda_handler(event, context):
    current_from_epoch = int(datetime.now().timestamp())
    # rss_write_timeがない、または2日以内のものを取得する。
    limit_from_epoch = current_from_epoch - 60 * 60 * 24 * 2 + 60 * 60
    # published_epochが1日以上経っているものを取得する。
    target_from_epoch = current_from_epoch - 60 * 60 * 24
    res = table.scan(
        ProjectionExpression="entry_url, tag, title, published, published_epoch, author, rss_write_time",
        FilterExpression="(published_epoch < :target_from_epoch) AND (attribute_not_exists(rss_write_time) OR rss_write_time > :limit_from_epoch)",
        ExpressionAttributeValues={
            ":limit_from_epoch": limit_from_epoch,
            ":target_from_epoch": target_from_epoch,
        },
        ReturnConsumedCapacity='TOTAL',
    )

    # feedを作成する。
    fg = FeedGenerator()
    fg.title("Rexxit Feed")
    fg.link(href="https://www.reddit.com")
    fg.description(" ")
    for entry in res['Items']:
        fe = fg.add_entry()
        fe.title(f"[{entry.get('tag', 'none')}] {entry['title']}")
        fe.published(entry['published'])
        fe.link(href=entry['entry_url'])
        fe.description(" ")
    filecontent = fg.rss_str()

    # s3へ保存する。
    bucket.put_object(Key='public/rexxit.rss', Body=filecontent, ContentType='application/rss+xml')

    # dynamodbに書き込み時間を記録する。
    for entry in res['Items']:
        if "rss_write_time" in entry:
            continue
        table.update_item(
            Key={'entry_url': entry["entry_url"]},
            UpdateExpression='SET rss_write_time = :rss_write_time',
            ConditionExpression='attribute_exists(entry_url) AND attribute_not_exists(rss_write_time)',
            ExpressionAttributeValues={
                ':rss_write_time': current_from_epoch,
            },
        )
