import urllib.parse

def schemeify_url(url):
    p = urllib.parse.urlparse(url)
    if p.scheme == '':
        p = list(p)
        # p[0] is the schema, p[1] is the netloc which should eb the base url, then i set the p[2] which is the path to nothing
        if p[0] != '' and p[0] != 'http' and p[0] != 'https':
            raise ValueError("Invalid URL scheme.")
        p[0] = 'http'
        p[1] = p[2]
        p[2] = ''
        p = urllib.parse.urlunparse(p)
    else:
        p = p.geturl()
    return p