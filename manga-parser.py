#!/usr/bin/env python2

import sys
import re
import os
import argparse
from getpass import getuser

import urllib2

try:
    from BeautifulSoup import BeautifulSoup
    from BeautifulSoup import SoupStrainer
except ImportError, e:
    print e
    print "This script requires the BeautifulSoup module, install and run again"
    sys.exit(2)

# defaults
_url = "http://www.mangafox.com/manga/"
_script = 'manga-parser'
_username = getuser()
_tmp = '/tmp'
cache_folder = '-'.join((_script, _username))
cache_path = os.path.join(_tmp, cache_folder)


def die(msg="unknown error", ecode=1):
    if args.suppress is False:
        print msg
    sys.exit(ecode)


def normalize_title(manga):
    """format manga title in url friendly format"""
    norm_manga = re.sub('[ .:,?!()]+', '_', manga)
    norm_manga = norm_manga.strip('_').lower()
    return re.sub('_+' ,'_', norm_manga)


def get_from_url(manga_url):
    try:
        contents = urllib2.urlopen(manga_url).read()
    except urllib2.HTTPError, e:
        die(e)

    return contents


def get_from_cache(cache_file):
    if os.stat(cache_file).st_size == 0:
        return None

    try:
        cache = open(cache_file, 'r')
        try:
            contents = cache.read()
        except:
            contents = None
        finally:
            cache.close()
    except:
        contents = None

    return contents


def get_manga(manga_title):
    """return manga page from cache or from url"""
    manga = normalize_title(manga_title)
    cache_file = os.path.join(cache_path, manga)
    manga_url = ''.join((_url, manga))
    contents = None

    if args.verbose:
        print "=> Retrieving page source"

    if os.path.isfile(cache_file):
        contents = get_from_cache(cache_file)
    else:
        contents = get_from_url(manga_url)

    if contents is None:
        os.remove(cache_file)
        contents = get_from_url(manga_url)

    return contents


def cache_page(manga_title):
    """cache manga page in /tmp"""
    cache_filepath = os.path.join(cache_path, manga_title)
    manga = normalize_title(manga_title)
    manga_url = ''.join((_url, manga))

    if os.path.isfile(cache_filepath):
        return False

    if not os.path.exists(cache_path):
        os.mkdir(cache_path)

    if args.verbose:
        print "=> Caching page source"

    cache = open(cache_filepath, 'w')
    contents = get_from_url(manga_url)
    cache.write(contents)
    cache.close()

    return True


def parse_manga(manga):
    """parse the manga html list to a list of dictionaries"""
    html = get_manga(manga)

    if args.verbose:
        print "=> Parsing manga page"

    # set parse filter
    listing = SoupStrainer('table', id="listing")
    table = BeautifulSoup(html, parseOnlyThese=listing)

    # parse and populate manga list
    manga_list = []
    for tr in table.findAll('tr'):
        manga_dic = { }

        t = tr.findAll('td', text=re.compile('^:'))
        if len(t):
            manga_dic['title'] = t[0].strip()[2:]

        for a in tr.findAll('a', { 'class': 'ch' }):
            manga_dic['link'] = a['href']
            manga_dic['volume'] = a['title']
            manga_dic['chapter'] = a.string

        manga_list.append(manga_dic)

    return manga_list


def print_list(mlist, separator='::', width=4, reverse=False):
    """print a manga list"""
    # build header
    header_titles = ('Volume', 'Chapter', 'Title')
    sep = '%s%s%s' % (' ' * width, separator, ' ' * width)
    header = sep.join(header_titles)
    hr = '=' * len(header)

    print header
    print hr

    if reverse is True:
        mlist = reversed(mlist)

    for manga in mlist:
        # ditch empty dictionaries
        try:
            print sep.join((manga['volume'], manga['chapter'], manga['title']))
        except KeyError:
            pass



# parse command line
parser = argparse.ArgumentParser(description='Parse MangaFox for manga information.')

parser.add_argument('-v', '--verbose', action='store_true', default=False, help='verbose output')
parser.add_argument('-s', '--suppress', action='store_true', default=False, help='suppress error messages')
parser.add_argument('manga', help='manga title')
args = parser.parse_args()


cache_page(args.manga)
manga_list = parse_manga(args.manga)
print_list(manga_list, reverse=True)


# vim: set sw=4 ts=4 sts=4 et:
