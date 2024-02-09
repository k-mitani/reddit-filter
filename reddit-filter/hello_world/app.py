import urllib.request
import xml.etree.ElementTree as ET
import json
from dataclasses import dataclass
import boto3
from time import sleep
# dynamodb
dynamodb = boto3.resource('dynamodb', region_name="ap-northeast-1")
table = dynamodb.Table('RedditEntry')



@dataclass
class RedditRssEntry:
    tag: str
    author: str
    updated: str
    published: str
    title: str
    content: str
    link: str


def fetch_entries(tag: str, url: str) -> list[RedditRssEntry]:
    rss = urllib.request.urlopen(url).read()
    root = ET.fromstring(rss)
    # entory要素を抜き出す。
    entries = root.findall(".//{http://www.w3.org/2005/Atom}entry")
    results = []
    for child in entries:
        author = child.find("{http://www.w3.org/2005/Atom}author").find("{http://www.w3.org/2005/Atom}name").text
        content = child.find("{http://www.w3.org/2005/Atom}content").text
        title = child.find("{http://www.w3.org/2005/Atom}title").text
        updated = child.find("{http://www.w3.org/2005/Atom}updated").text
        published = child.find("{http://www.w3.org/2005/Atom}published").text
        link = child.find("{http://www.w3.org/2005/Atom}link").attrib["href"]
        result = RedditRssEntry(tag, author, updated, published, title, content, link)
        results.append(result)
    return results


def lambda_handler(event, context):
    URL_DICT = {
        "Unity3D": "https://www.reddit.com/r/Unity3D.rss",
        "unity": "https://www.reddit.com/r/unity.rss",
        "playmygame": "https://www.reddit.com/r/playmygame.rss",
        "indiegames": "https://www.reddit.com/r/indiegames.rss",
        "gamedev": "https://www.reddit.com/r/gamedev.rss",
    }
    entries = []
    for i, (tag, url) in enumerate(URL_DICT.items()):
        print(f"fetching {i + 1} {tag}...")
        res = fetch_entries(tag, url)
        entries.extend(res)
        sleep(2)
    
    # dynamodbに保存する。
    consumed_capacity = 0
    for entry in entries:
        try:
            result = table.update_item(
                Key={"entry_url": entry.link},
                UpdateExpression="SET tag = :tag, author = :author, title = :title, updated = :updated, published = :published, content = :content",
                ExpressionAttributeValues={
                    ':tag': entry.tag,
                    ':author': entry.author,
                    ':title': entry.title,
                    ':updated': entry.updated,
                    ':published': entry.published,
                    ':content': entry.content,
                },
                ReturnConsumedCapacity='TOTAL',
                ConditionExpression="attribute_not_exists(entry_url)"
            )
            consumed_capacity += result['ConsumedCapacity']['CapacityUnits']
            print("OK", entry.link)
        except Exception as e:
            if "ConditionalCheckFailedException" in str(e):
                print("SKIP", entry.link)
                continue
            else:
                print("NG", entry.link, e)
    print("DONE", consumed_capacity)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "OK",
            "count": len(entries),
        }),
    }
