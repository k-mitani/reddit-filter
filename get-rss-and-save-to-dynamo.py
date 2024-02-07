import xml.etree.ElementTree as ET
import urllib.request

def handler(event, context):
    RSS_URL = "https://www.reddit.com/r/Unity3D.rss"
    rss = urllib.request.urlopen(RSS_URL).read()
    root = ET.fromstring(rss)

    for child in root:
        # content要素
        author = child.find("{http://www.w3.org/2005/Atom}author").find("{http://www.w3.org/2005/Atom}name").text
        content = child.find("{http://www.w3.org/2005/Atom}content").text
        title = child.find("{http://www.w3.org/2005/Atom}title").text
        updated = child.find("{http://www.w3.org/2005/Atom}updated").text
        published = child.find("{http://www.w3.org/2005/Atom}published").text
        link = child.find("{http://www.w3.org/2005/Atom}link").attrib["href"]

        print({
            "author": author,
            "content": content,
            "title": title,
            "updated": updated,
            "published": published,
            "link": link
        })

    print("Done")
