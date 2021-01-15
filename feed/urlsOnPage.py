import requests
from bs4 import BeautifulSoup, SoupStrainer
from urllib.parse import urljoin, urlparse
# constants from https://github.com/postlight/mercury-parser/blob/15f7fa1e27fe6b47c87da40ba4fce9b2db7934ec/src/extractors/generic/content/scoring/constants.js
UNLIKELY_CANDIDATES_BLACKLIST = [
  'ad-break',
  'adbox',
  'advert',
  'addthis',
  'agegate',
  'aux',
  'blogger-labels',
  'combx',
  'comment',
  'conversation',
  'disqus',
  'entry-unrelated',
  'extra',
  'foot',
  'form',
  'header',
  'hidden',
  'loader',
  'login', # Note: This can hit 'blogindex'.
  'menu',
  'meta',
  'nav',
  'pager',
  'pagination',
  'predicta', #// readwriteweb inline ad box
  'presence_control_external', #// lifehacker.com container full of false positives
  'popup',
  'printfriendly',
  'related',
  'remove',
  'remark',
  'rss',
  'share',
  'shoutbox',
  'sidebar',
  'sociable',
  'sponsor',
  'tools',
]
# if in unliklu candidates but in whitelist then keep its ok
UNLIKELY_CANDIDATES_WHITELIST = [
  'and',
  'article',
  'body',
  'blogindex',
  'column',
  'content',
  'entry-content-asset',
  'format', 
  'hfeed',
  'hentry',
  'hatom',
  'main',
  'page',
  'posts',
  'shadow',
]
HNEWS_CONTENT_SELECTORS = [
  ['.hentry', '.entry-content'],
  ['entry', '.entry-content'],
  ['.entry', '.entry_content'],
  ['.post', '.postbody'],
  ['.post', '.post_body'],
  ['.post', '.post-body'],
]
NEGATIVE_SCORE_HINTS = [
  'adbox',
  'advert',
  'author',
  'bio',
  'bookmark',
  'bottom',
  'byline',
  'clear',
  'com-',
  'combx',
  'comment',
  'comment\\B',
  'contact',
  'copy',
  'credit',
  'crumb',
  'date',
  'deck',
  'excerpt',
  'featured',# // tnr.com has a featured_content which throws us off
  'foot',
  'footer',
  'footnote',
  'graf',
  'head',
  'info',
  'infotext', #// newscientist.com copyright
  'instapaper_ignore',
  'jump',
  'linebreak',
  'link',
  'masthead',
  'media',
  'meta',
  'modal',
  'outbrain',# // slate.com junk
  'promo',
  'pr_', #// autoblog - press release
  'related',
  'respond',
  'roundcontent',# // lifehacker restricted content warning
  'scroll',
  'secondary',
  'share',
  'shopping',
  'shoutbox',
  'side',
  'sidebar',
  'sponsor',
  'stamp',
  'sub',
  'summary',
  'tags',
  'tools',
  'widget',
]
POSITIVE_SCORE_HINTS = [
  'article',
  'articlecontent',
  'instapaper_body',
  'blog',
  'body',
  'content',
  'entry-content-asset',
  'entry',
  'hentry',
  'main',
  'Normal',
  'page',
  'pagination',
  'permalink',
  'post',
  'story',
  'text',
  '[-_]copy', #// usatoday
  '\\Bcopy',
]
def getUrls(url):
    urls = []
    try:
      r = requests.get(url)
      soup = BeautifulSoup(r.text)
    except:
      raise ValueError("URL does not exist. Error accessing URL.")
    soup.prettify()
    for anchor in soup.findAll('a', href=True):
        parentClasses = anchor.parent.attrs.get('class')
        noComment = True
        if parentClasses:
            for className in parentClasses:
                if className:
                    className.lower()
                    noComment = any(className in s for s in UNLIKELY_CANDIDATES_BLACKLIST)

        if noComment:
            absolute_url = urljoin(url,anchor['href'])
            urls.append(absolute_url)

    return urls
def urlsOnPage(url):
    url_data = urlparse(url)
    if "." not in url_data.netloc and (url_data.scheme == 'http' or url_data.scheme == "https"):
      raise ValueError('Not a url.')
    articleUrls = getUrls(url)
    return articleUrls