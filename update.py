#!/usr/bin/python2.6

import sys
import os
import stat
import urllib2
import datetime
import re
import time
from subprocess import check_call

file_mode = 0o644

sys.path.append('.')
from BeautifulSoup import BeautifulSoup

sys.path.append('PyRSS2Gen')
import PyRSS2Gen

download_directory = "downloaded"

number_to_keep = None
base_podcast_url = None

try:
    if len(sys.argv) != 3:
        raise Exception, "Wrong number of arguments"
    number_to_keep = int(sys.argv[1])
    base_podcast_url = sys.argv[2]
except Exception as e:
    print >> sys.stderr, str(e)
    print >> sys.stderr, "Usage: %s <NUMBER-TO-KEEP> <BASE_PODCAST_URL>"
    sys.exit(1)

def is_mp3(f):
    return re.search('\.mp3$',f,re.I)

files = [ os.path.join(download_directory,x) for x in os.listdir(download_directory) if is_mp3(x) ]

def mtime(f):
    return datetime.datetime.fromtimestamp(os.stat(f)[stat.ST_MTIME])

files.sort( key = mtime )

for f in files[0:-number_to_keep]:
    os.remove(f)

opener = urllib2.build_opener()

show_url = "http://www.bbc.co.uk/programmes/b00slvl3"

soup = BeautifulSoup(opener.open(show_url))

def iplayer_console_tag(x):
    if x.name != 'a':
        return False
    for t in x.attrs:
        if t[0] == 'href':
            if re.search('^http://www.bbc.co.uk/iplayer/console/[a-z0-9]+$',t[1]):
                return True
    return False

a = soup.find( iplayer_console_tag )

check_call(["mkdir","-p",download_directory])

def iplayer_dl(url):
    command = [ "ruby", "-I", "iplayer-dl/lib", "iplayer-dl/bin/iplayer-dl",
                "-d", download_directory, url ]
    check_call(command)

iplayer_dl(a['href'])

# Now generate the XML for the podcast:

files = [ x for x in os.listdir(download_directory) if is_mp3(x) ]
files.sort( key = lambda x: mtime(os.path.join(download_directory,x)) )

# Make them readable:
for f in files:
    time.sleep(2)
    os.chmod(os.path.join(download_directory,f),file_mode)

def item_from_file(f):
    full = os.path.join(download_directory,f)
    extension_removed = re.sub('\.mp3$','',f,re.I)
    return PyRSS2Gen.RSSItem(
        title = extension_removed,
        link = show_url,
        description = "An episode of Tom Ravenscroft's show on BBC Radio 6",
        guid = PyRSS2Gen.Guid(f),
        pubDate = mtime(full),
        enclosure = PyRSS2Gen.Enclosure(base_podcast_url + urllib2.quote(f),
                                        os.path.getsize(full),
                                        "audio/mpeg"))

rss = PyRSS2Gen.RSS2(
    title = "Tom Ravenscroft on BBC Radio 6",
    link = show_url,
    description = "An unofficial podcast for Tom Ravenscroft's show on BBC Radio 6, which annoyingly is only available through iPlayer",
    lastBuildDate = datetime.datetime.now(),
    items = [ item_from_file(f) for f in files ] )

output_filename = os.path.join(download_directory,"podcast.xml")
rss.write_xml(open(output_filename,"w"))
os.chmod(output_filename,file_mode)