import sys

if sys.version_info.major >= 3:
    from io import StringIO
    from urllib.parse import parse_qs
else:
    from cStringIO import StringIO
    from urlparse import parse_qs
