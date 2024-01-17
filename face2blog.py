import argparse
from socket import timeout
import zipfile
import pathlib
import json
from datetime import datetime
from string import Template
import re
import linkpreview
from linkpreview import Link, LinkPreview
import requests
from urllib.parse import urlparse
import concurrent.futures
from timeit import default_timer as timer
from requests_cache import CachedSession
from requests_html import HTMLSession
import filetype


IN_PATH = ""
OUT_PATH = ""

# POST_PATH = pathlib.Path("posts/your_posts_1.json")  # old version of facebook data
POST_PATH = pathlib.Path("your_activity_across_facebook/posts/your_posts__check_ins__photos_and_videos_1.json")

SESSION = CachedSession()


# see https://stackoverflow.com/questions/5574042/string-slugification-in-python
# TODO: Fix to work also for russian chars/posts
def _slugify(text):
    import unicodedata

    slug = unicodedata.normalize('NFKD', text)
    slug = slug.encode('ascii', 'ignore').decode('ascii').lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug).strip('-')
    slug = re.sub(r'[-]+', '-', slug)
    return slug


def _valid(post):
    if "title" in post:
        # skip facebook posts with messsages to other peoples "Chronik"
        if "Chronik" in post["title"]:
            return False
        # skip facebook posts showing that the author is is "Sicherheit"
        if "Sicherheit" in post["title"]:
            return False
    return True


def _extract_date_time(post):
    # get timestamp
    t = int(post["timestamp"])
    return datetime.fromtimestamp(t).astimezone()


def _extract_content(post):
    content = ""
    if "data" in post:
        for element in post["data"]:
            if "post" in element:
                content = element["post"]
    return content


def _create_title(content):
    # generate a title from the content
    title = ""
    tokens = [token for token in content.split() if "http" not in token]
    len_tokens = len(tokens)
    if len_tokens > 0:
        if len_tokens > 3:
            title = " ".join(tokens[:5]) + " ..."
        else:
            title = " ".join(tokens[:len_tokens]) + " ..."
        # Put title in single quotes to prevent YAML issues in Hugo
        title = title.replace("'", "")
        title = "'" + title + "'"

    return title


def _extract_url(post):
    url = None
    if "attachments" in post:
        for attachment in post["attachments"]:
            #print(attachment)
            if "data" in attachment:
                for element in attachment["data"]:
                    #print(element)
                    if "external_context" in element:
                        url = element["external_context"]["url"]
    return url


def _get_preview(url, headers = None, session = SESSION):

    if not headers:
        # see https://github.com/meyt/linkpreview/issues/9#issuecomment-925643793
        # and https://developers.google.com/search/docs/advanced/crawling/overview-google-crawlers
        # headers = {'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)', 'Referer': 'https://www.google.com'}
        # see https://github.com/meyt/linkpreview/issues/9#issuecomment-1774215623
        # and https://user-agents.net/bots/facebookexternalhit/versions/1-1
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/601.2.4 (KHTML, like Gecko) Version/9.0.1 Safari/601.2.4 facebookexternalhit/1.1 Facebot'}

    r = session.get(url, headers=headers, timeout=10)

    # Many web pages will return nonsense previews if status code is not 200
    r.raise_for_status()

    uri = urlparse(r.url)
    domain = re.sub('^www\\.', '', uri.netloc)
    # Unfortunately HTMLSession is not thread safe
    # So we cannot use it.
    # TODO: Find a fix for this problem
    if isinstance(session, HTMLSession):
        print("Rendering Javascript...")
        r.html.render(sleep=1, timeout=10)
        text = r.html.raw_html
    else:
        text = r.text

    # from_cache = 'hit' if r.from_cache else 'miss'
    # print(f'{url} is {len(r.content)} bytes (cache {from_cache})')

    link = Link(r.url, text)
    preview = LinkPreview(link)
    return preview, domain


def _is_url(text):
    # see https://stackoverflow.com/questions/7160737/how-to-validate-a-url-in-python-malformed-or-not
    try:
        result = urlparse(text)
        return all([result.scheme, result.netloc])
    except:
        return False


def _create_markdown(url, preview, domain):
    # print("DEBUG: Entering create_markdown", url, domain, preview.title, preview.description)
    markdown = ""
    image_url = preview.absolute_image
    # Note: preview.absolute_image is sometimes not a valid url and not even a string
    if image_url and _is_url(str(image_url)):
        markdown += "> [![](" + str(image_url) + ")](" + url + ")\n"

    markdown += "> " + domain + "\n"
    if preview.title:
        markdown += "> ## [" + preview.title + "](" + url + ")\n"
    else:
        markdown += "> ## [" + preview.force_title + "](" + url + ")\n"
    markdown += ">\n"
    try:
        if preview.description:
            markdown += ">" + preview.description + "\n"
    except (KeyError, json.decoder.JSONDecodeError) as err:
        # catch a weird exception when reading the description
        # (probably caused by a bug in beautifulSoup)
        print(url)
        print(err)
    return markdown


def _process_post(post, index):
    if not _valid(post):
        return None

    date_time = _extract_date_time(post)
    content = _extract_content(post)
    title = _create_title(content)
    url = _extract_url(post)
    image_url = None

    content += "\n"

    if not title and not url:
        # if we have neither url nor a title the post is empty and we skip it
        return None

    if url:
        try:
            preview, domain = _get_preview(url)
            preview_md = _create_markdown(url, preview, domain)
            image_url = preview.absolute_image

            # In case the content was empty get the title from the preview
            if not title:
                title = _create_title(preview.title)
            # if preview.title was also empty use the force title
            if not title:
                title = _create_title(preview.force_title)

        except (requests.exceptions.RequestException, linkpreview.exceptions.LinkPreviewException, AttributeError) as err:
            print(f"Post number {index}", url)
            print(f"Post number {index}", err)
            if not title:
                title = _create_title(str(err))
            preview_md = "> " + url + "\n"
        # add markdown with preview to content of post
        content += preview_md

    return title, date_time, content, image_url


def _write_markdown_file(title, date_time, content, date, output_path):
    with output_path.open("w") as outfile:
     with open("post_template.md", "r") as temp_file:
      post_template = Template(temp_file.read())	
      markdown = post_template.substitute(content=content,title=title,datetime=date_time.isoformat(),date=date.isoformat())
      outfile.write(markdown)
      print(date_time, title)


def _read_content(output_path):
    with output_path.open("r") as oldfile:
        lines = oldfile.readlines()

        frontmatter = []
        for i,line in enumerate(lines):
            if line.startswith("---"):
                frontmatter.append(i)
            if len(frontmatter) > 1:
                break
        # The content we want to extract starts at the line after the frontmatter
        return "".join(lines[frontmatter[1]+1:])


def _write_outfile(title, date_time, content, update_header=False):
    date = date_time.date()
    filename = _slugify(date.isoformat() + "-" + title) + ".md"
    output_path = pathlib.Path(OUT_PATH) / filename
    if not output_path.exists():
        _write_markdown_file(title, date_time, content, date, output_path)
    else:
        if update_header:
            print("Updating header of existing file " + filename)
            old_content = _read_content(output_path)
            _write_markdown_file(title, date_time, old_content, date, output_path)
        else:
            print("Skipping existing file " + filename)

    return True


def _is_image(file_content):
    kind = filetype.guess(file_content)

    if kind is not None and kind.mime.startswith('image/'):
        # The file is an image
        return True
    else:
        # The file is not an image
        return False


def _write_pagebundle(title, date_time, content, image_url=None, update_header=False ):
    date = date_time.date()
    dirname = _slugify(date.isoformat() + "-" + title)
    output_path = pathlib.Path(OUT_PATH) / dirname / "index.md"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not output_path.exists():
        _write_markdown_file(title, date_time, content, date, output_path)
    else:
        if update_header:
            print(f"Updating header of existing file {output_path}")
            old_content = _read_content(output_path)
            _write_markdown_file(title, date_time, old_content, date, output_path)
        else:
            print(f"Skipping existing file {output_path}")

    if image_url:
        # see https://stackoverflow.com/questions/13137817/how-to-download-image-using-requests
        # image_name = url.split("/")[-1]
        # see https://docs.hugoblox.com/reference/page-features/
        image_path = output_path.parent / "featured.jpg"
        print(f"Storing preview image {image_url}")
        try:
            r = SESSION.get(image_url)

            if r.status_code == 200:
                file_content = r.content

                if _is_image(file_content):
                    # The image_url is an image
                    with open(image_path, 'wb') as outfile:
                        outfile.write(file_content)
                else:
                    # The image_url is not an image
                    print("The image_url is not an image. Skipping.")

        except requests.exceptions.RequestException as err:
            print(err)

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert data from facebook to markdown blog posts.")
    parser.add_argument("input", type=str, help="Input file - the zip file downloaded from facebook")
    parser.add_argument("output", type=str, help="Output directory for markdown files")
    parser.add_argument("-u", "--update", action="store_true", help="Update header of existing files. Leaves content of existing files intact.")
    args = parser.parse_args()

    IN_PATH = args.input
    OUT_PATH = args.output

    target = pathlib.Path(args.input).with_suffix("")
    # only unzip the input file, if it wasn't already unzipped, because it might take a long time
    if not target.exists():
        with zipfile.ZipFile(IN_PATH, "r") as infile:
            target.mkdir(parents=True, exist_ok=True)
            infile.extractall(target)

    posts = target / POST_PATH
    with posts.open(encoding="raw_unicode_escape") as f:
        # see https://stackoverflow.com/questions/50540370/decode-utf-8-encoding-in-json-string
        data = json.loads(f.read().encode("raw_unicode_escape").decode())

        start = timer()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(_process_post, post, index) for index, post in enumerate(data[:])
            }

            for fut in concurrent.futures.as_completed(futures):
                result = fut.result()
                if result:
                    success = _write_pagebundle(result[0], result[1], result[2], result[3], args.update)
        end = timer()
        print(end - start)

