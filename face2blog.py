import argparse
import zipfile
import pathlib
import json
from datetime import datetime
from string import Template
import re
import linkpreview
from linkpreview import Link, LinkPreview, LinkGrabber
import requests
from urllib.parse import urlparse

# see https://stackoverflow.com/questions/5574042/string-slugification-in-python
def _slugify(text):
	import unicodedata

	slug = unicodedata.normalize('NFKD', text)
	slug = slug.encode('ascii', 'ignore').decode('ascii').lower()
	slug = re.sub(r'[^a-z0-9]+', '-', slug).strip('-')
	slug = re.sub(r'[-]+', '-', slug)
	return slug


parser = argparse.ArgumentParser(description="Convert data from facebook to markdown blog posts.")
parser.add_argument("input", type=str, help="Input file - the zip file downloaded from facebook")
parser.add_argument("output", type=str, help="Output directory for markdown files")
args = parser.parse_args()

target = pathlib.Path(args.input).with_suffix("")
if not target.exists(): 
	with zipfile.ZipFile(args.input,"r") as infile:
		target.mkdir(parents=True, exist_ok=True) 
		infile.extractall(target)

posts = target / "posts" / "your_posts_1.json"
with posts.open(encoding="raw_unicode_escape") as f:
	# see https://stackoverflow.com/questions/50540370/decode-utf-8-encoding-in-json-string
	data = json.loads(f.read().encode("raw_unicode_escape").decode())
	for post in data[:]:

		# skip facebook posts with messsages to other peoples "Chronik"
		if "title" in post:
			if "Chronik" in post["title"]:
				continue

		# get timestamp	
		t = int(post["timestamp"])
		date_time = datetime.fromtimestamp(t).astimezone()
		date = date_time.date()	

		# generate a title from the content
		content = ""
		for element in post["data"]:
			if "post" in element:
				content = element["post"]		

		title = ""		
		tokens = [token for token in content.split() if "http" not in token]		
		len_tokens = len(tokens)
		if len_tokens > 0:
			if len_tokens > 3:
				title = " ".join(tokens[:5]) + " ..."
			else:
				title = " ".join(tokens[:len_tokens]) + " ..."
			# Put title in single quotes to prevent YAML issues in Hugo			
			title = "'" + title + "'"   		

		url = None
		if "attachments" in post:
			for attachment in post["attachments"]:
				#print(attachment)
				if "data" in attachment:
					for element in attachment["data"]:
						#print(element)
						if "external_context" in element:
							url = element["external_context"]["url"]
		if url:
			try:
				# see https://stackoverflow.com/questions/27652543/how-to-use-python-requests-to-fake-a-browser-visit-a-k-a-and-generate-user-agent
				headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'} 	
				r = requests.get(url, headers=headers)
				uri = urlparse(r.url)
				domain = re.sub('^www\.', '', uri.netloc)

				grabber = LinkGrabber()
				link = Link(url, grabber.get_content(url, headers=headers))
				preview = LinkPreview(link)

				# preview = linkpreview.link_preview(url)
				content += "\n"
				if preview.image:
					content += "> [![]("+ preview.image + ")](" + url + ")\n"

				content += "> " + domain + "\n"	
				content += "> ## [" + preview.title + "](" + url + ")\n"
				content += ">\n"
				if preview.description:
					content += ">" + preview.description + "\n"
				# In case the content was empty get the title from the preview	
				if not title:
					if not preview.title:
						title = preview.force_title
					else:
						title = preview.title	
			except (requests.exceptions.RequestException, linkpreview.exceptions.MaximumContentSizeError) as err:
				print(err)
				content += "\n"
				content += "> " + url + "\n"
		else:
			# if we have neither url nor a title the post is empty and we skip it
			if not title:
				continue		

		print(date_time, title)
		filename = _slugify(date.isoformat() + "-" + title) + ".md"
		output_path = pathlib.Path(args.output) / filename
		with output_path.open("w") as outfile:
			with open("post_template.md", "r") as temp_file:
				post_template = Template(temp_file.read())	
				markdown = post_template.substitute(content=content,title=title,datetime=date_time.isoformat(),date=date.isoformat())
				outfile.write(markdown)
				# print(markdown)

