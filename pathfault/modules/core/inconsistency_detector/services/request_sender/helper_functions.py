import sys
import linecache


def _parse_url(url):
    """ This function extracts certain 
        components from a given URL.
    """
    authority = url.split('/')[2]
    uri = '/'.join(url.split('/')[3:])

    if ':' not in authority:
        if 'https://' in url:
            port = 443
        else:
            port = 80
        host = authority
    else:
        host, port = authority.split(':')

    return host, port, authority, uri


def _print_exception(extra_details=None):
    """ This function prints exception details
        including the line number where the exception
        is raised, which is helpful in most cases.
    """
    if extra_details is None:
        extra_details = []
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print('EXCEPTION IN ({}, LINE {} "{}"): {}, {}'.format(filename, lineno, line.strip(), exc_obj, extra_details))
