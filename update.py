#!/usr/bin/python2.6

import sys
import os
import stat
import urllib2
import datetime
import re
import time
import ConfigParser
from subprocess import check_call

file_mode = 0o644

sys.path.append('.')
from BeautifulSoup import BeautifulSoup

sys.path.append('PyRSS2Gen')
import PyRSS2Gen

def episode_description(f):
    # Could examine the file's ID3 tags or extract the date
    # from the filename to make this more interesting
    return ""

def is_mp3(f):
    return re.search('\.mp3$',f,re.I)

def is_aac(f):
    return re.search('\.aac$',f,re.I)

def mtime(f):
    return datetime.datetime.fromtimestamp(os.stat(f)[stat.ST_MTIME])

def iplayer_console_tag(x):
    if x.name != 'a':
        return False
    for t in x.attrs:
        if t[0] == 'href':
            if re.search('^http://www.bbc.co.uk/iplayer/console/[a-z0-9]+$',t[1]):
                return True
    return False

def iplayer_dl(url):
#    command = [ "ruby", "-I", "iplayer-dl/lib", "iplayer-dl/bin/iplayer-dl",
#                "-t", "flashaaclow",
#                "-d", download_directory, url ]
    command = [ "../get_iplayer/get_iplayer", url,
                "--modes=flashaaclow,flashaacstd",
                "--outputradio", download_directory,
                "--file-prefix", "<name>-<firstbcast>",
                "--command", "\"\"",
                "--force" ]
    print >> sys.stdout, command
    check_call(command)

def item_from_file(f):
    full = os.path.join(download_directory,f)
    extension_removed = re.sub('\.aac$','',f,re.I)
    url_for_mp3 = base_podcast_url + urllib2.quote(f)
    return PyRSS2Gen.RSSItem(
        title = extension_removed,
        link = show_url,
        description = episode_description(f),
        guid = PyRSS2Gen.Guid(url_for_mp3),
        pubDate = mtime(full),
        enclosure = PyRSS2Gen.Enclosure(url_for_mp3,
                                        os.path.getsize(full),
                                        "audio/x-aac"))




config = ConfigParser.ConfigParser()
config.read('ravenscroft.cfg')

for i,s in enumerate(config.sections()):
    podcast_title = s
    download_directory = os.path.join(config.get(s, 'destination'),config.get(s, 'subdirectory'))
    base_podcast_url = config.get(s, 'baseurl')
    number_to_keep = int(config.get(s, 'numbertokeep'))
    xml_filename = config.get(s, 'filename')
    show_url = config.get(s, 'showurl')
    podcast_description = config.get(s, 'description')
    #episode_description = config.get(s, 'episodedescription')

    print 'title:', podcast_title
    print 'download_directory:', download_directory
    print 'base_podcast_url:', base_podcast_url
    print 'number_to_keep:', number_to_keep
    print 'xml_filename:', xml_filename
    print 'show_url:', show_url
    print 'podcast_description:', podcast_description
    #print 'episode_description:', episode_description

    #try:
    #    if len(sys.argv) != 3:
    #    if len(sys.argv) != 2:
    #        raise Exception, "Wrong number of arguments"
    #    number_to_keep = int(sys.argv[1])
    #    base_podcast_url = sys.argv[2]
    #    base_podcast_url = sys.argv[1]
    #except Exception as e:
    #    print >> sys.stderr, str(e)
    #    print >> sys.stderr, "Usage: %s <NUMBER-TO-KEEP> <BASE_PODCAST_URL>"
    #    print >> sys.stderr, "Usage: %s <BASE_PODCAST_URL>"
    #    sys.exit(1)

    check_call(["mkdir","-p",download_directory])

    files = [ os.path.join(download_directory,x) for x in os.listdir(download_directory) if is_aac(x) ]

    files.sort( key = mtime )

    for f in files[0:-number_to_keep]:
        os.remove(f)

    opener = urllib2.build_opener()

    soup = BeautifulSoup(opener.open(show_url))

    a = soup.find( iplayer_console_tag )
>>>>>>    TODO!
    print 'a:', a
    iplayer_dl(a['href'])

    # Now generate the XML for the podcast:

    files = [ x for x in os.listdir(download_directory) if is_aac(x) ]
    files.sort( key = lambda x: mtime(os.path.join(download_directory,x)) )

    # Make them readable:
    for f in files:
        time.sleep(2)
        os.chmod(os.path.join(download_directory,f),file_mode)

    rss = PyRSS2Gen.RSS2(
        title = podcast_title,
        link = show_url,
        description = podcast_description,
        lastBuildDate = datetime.datetime.now(),
        items = [ item_from_file(f) for f in files ] )

    output_filename = os.path.join(download_directory,xml_filename)
    rss.write_xml(open(output_filename,"w"))
    os.chmod(output_filename,file_mode)
