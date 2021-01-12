import argparse
import zipfile
import pathlib
import json
from datetime import datetime
from string import Template
import re

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

with open("post_template.md", "r") as temp_file:
	post_template = Template(temp_file.read())	

	posts = target / "posts" / "your_posts_1.json"
	with posts.open(encoding="raw_unicode_escape") as f:
		# see https://stackoverflow.com/questions/50540370/decode-utf-8-encoding-in-json-string
		data = json.loads(f.read().encode("raw_unicode_escape").decode())
		for post in data[:10]:
			content = ""
			for element in post["data"]:
				if "post" in element:
					content = element["post"]		

			tokens = len(content.split())
			if tokens > 3:
				title = " ".join(content.split()[:3]) + " ..."
			else:
				title = " ".join(content.split()[:tokens]) + " ..."
			# Put title in single quotes to prevent YAML issues in Hugo			
			title = "'" + title + "'"   		

			t = int(post["timestamp"])
			date_time = datetime.fromtimestamp(t).astimezone()
			date = date_time.date()

			filename = _slugify(date.isoformat() + "-" + title) + ".md"
			output_path = pathlib.Path(args.output) / filename
			with output_path.open("w") as outfile:
				markdown = post_template.substitute(content=content,title=title,datetime=date_time.isoformat(),date=date.isoformat())
				outfile.write(markdown)
				# print(markdown)

