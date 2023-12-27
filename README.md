# social2blog

A repository of scripts which I use to convert content 
from my social media websites to my markdown based blog.

## face2blog

As a facebook user one can download all the data which facebook has stored about you, see

- <https://www.facebook.com/help/212802592074644>

This script can extract the post data (including the link preview to external websites) from this data blob and convert it into markdown files with a frontmatter suitable for a
blog/homepage created by [hugo](https://gohugo.io/). 

### Prerequisites

- python 3.9
- pipenv
- facebook account

### Usage

First you need to download all your data from facebook. Follow the description from <https://www.facebook.com/help/212802592074644>.  For this script to work it is best to select

- format: JSON
- time range: all
- media quality: high

It can take several days until facebook will notify you via email, 
that your file is ready to download.

Then after cloning this repository you must first install the necessary dependencies and activate the virtual python environment

    $ pipenv install
    $ pipenv shell

Then before using the script modify the frontmatter template which is used to generate the markdown posts

    $ nano post_template.md    # You can use any other text editor of your choice

After editing and saving the `post_template.md` running the script is as simple as follows

    $ python face2blog.py <path_to_facebook_data.zip> <path_to_output_dir_for_posts>

It will unzip your facebook data blob, extract all content from the `your_posts.json` and convert each facebook post into a markdown post using the `post_template.md` as template. It will also extract external links/urls from your facebook post and create a link preview from it. This will be done in parallel, but if you have a huge number of facebook posts it might still take a while until the script has made a connection to every
url and generate a preview.

The script is conservative an will not overwrite existing files. But there 
is a option `-u` to update the frontmatter of all existing posts. This is
useful if you already created the posts and the preview, and don't want to recreate the preview, only update the frontmatter. Because sometimes urls change or vanish, so that you might not want to recreate the preview.

See all option here

    $ python face2blog.py -h
    usage: face2blog.py [-h] [-u] input output
    
    Convert data from facebook to markdown blog posts.
    
    positional arguments:
      input         Input file - the zip file downloaded from facebook
      output        Output directory for markdown files

    optional arguments:
      -h, --help    show this help message and exit
      -u, --update  Update header of existing files. Leaves content of existing files intact.

### Todo list

- use html_sessions (javascript rendering) for problematic urls
- caching url requests and link previews
- replace dead links with a link to the webarchive 
- automatically tag the content (see e.g <https://github.com/jaketae/auto-tagger>)
- download media of the post
- ~~download the preview image, so it can be used as cover image for the post~~

    

   