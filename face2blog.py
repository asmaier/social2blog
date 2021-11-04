import argparse
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


IN_PATH = ""
OUT_PATH = ""

SESSION = CachedSession()

# see https://stackoverflow.com/questions/5574042/string-slugification-in-python
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

def _get_preview(url):
	# see https://github.com/meyt/linkpreview/issues/9#issuecomment-925643793
	# and https://developers.google.com/search/docs/advanced/crawling/overview-google-crawlers
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)', 
    'Referer': 'https://www.google.com'} 

    r = SESSION.get(url, headers=headers)

    # from_cache = 'hit' if r.from_cache else 'miss'
    # print(f'{url} is {len(r.content)} bytes (cache {from_cache})')

    uri = urlparse(r.url)
    domain = re.sub('^www\.', '', uri.netloc)

    link = Link(r.url, r.text)
    preview = LinkPreview(link)
    return preview, domain


def _create_markdown(url, preview, domain):
	markdown = ""

	if preview.image: 
		markdown += "> [![]("+ preview.image + ")](" + url + ")\n"
		
	markdown += "> " + domain + "\n"
	if preview.title:
		markdown += "> ## [" + preview.title + "](" + url + ")\n"
	else:
		markdown += "> ## [" + preview.force_title + "](" + url + ")\n"	
	markdown += ">\n"
	try:
		if preview.description:
			markdown += ">" + preview.description + "\n"
	except KeyError as kerr:
        # catch a weird exception when reading the description
        # (probably caused by a bug in beautifulSoup)
		print(kerr)
	return markdown			

def _process_post(post):
	if not _valid(post):
		return None

	date_time = _extract_date_time(post)
	content = _extract_content(post)	
	title = _create_title(content) 		
	url = _extract_url(post)

	content += "\n"

	if not title and not url:
		# if we have neither url nor a title the post is empty and we skip it
		return None

	if url:
		try:
			preview, domain = _get_preview(url)
			preview_md = _create_markdown(url, preview, domain)

			# In case the content was empty get the title from the preview	
			if not title:
				title = _create_title(preview.title)
			# if preview.title was also empty use the force title	
			if not title:
				title = _create_title(preview.force_title)
					
		except (requests.exceptions.RequestException, linkpreview.exceptions.LinkPreviewException) as err:
			print(url)
			print(err)
			preview_md = "> " + url + "\n"		
		# add markdown with preview to content of post 
		content += preview_md

	return (title, date_time, content, post)

def _write_outfile(title, date_time, content):
	date = date_time.date()
	filename = _slugify(date.isoformat() + "-" + title) + ".md"
	output_path = pathlib.Path(OUT_PATH) / filename
	with output_path.open("w") as outfile:
		with open("post_template.md", "r") as temp_file:
			post_template = Template(temp_file.read())	
			markdown = post_template.substitute(content=content,title=title,datetime=date_time.isoformat(),date=date.isoformat())
			outfile.write(markdown)
			print(date_time, title)
	return True		

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Convert data from facebook to markdown blog posts.")
	parser.add_argument("input", type=str, help="Input file - the zip file downloaded from facebook")
	parser.add_argument("output", type=str, help="Output directory for markdown files")
	args = parser.parse_args()
	
	IN_PATH = args.input
	OUT_PATH = args.output

	target = pathlib.Path(args.input).with_suffix("")
	if not target.exists(): 
		with zipfile.ZipFile(IN_PATH,"r") as infile:
			target.mkdir(parents=True, exist_ok=True) 
			infile.extractall(target)

	posts = target / "posts" / "your_posts_1.json"
	with posts.open(encoding="raw_unicode_escape") as f:
		# see https://stackoverflow.com/questions/50540370/decode-utf-8-encoding-in-json-string
		data = json.loads(f.read().encode("raw_unicode_escape").decode())

		start = timer()
		with concurrent.futures.ThreadPoolExecutor() as executor:
			futures = {
        		executor.submit(_process_post, post) for post in data[:]
    		}

			for fut in concurrent.futures.as_completed(futures):
				result = fut.result()
				if result:
					success = _write_outfile(result[0], result[1], result[2])
		end = timer()
		print(end - start)			


		
