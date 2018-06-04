# Python 1.4 cgi.py
# Bug was in "continue" detection.
# 1.4 doesn't have lnotab and our CONTINUE detection is off.
def parse_multipart(params, pdict):
    while params:
	if params.has_key('name'):
	   params = None
	else:
	    continue

    return None
