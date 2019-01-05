# The bug in python 3.6+ was in parsing that we
# add END_IF_THEN and using that inside "return results"
def whcms_license_info(md5hash, datahash, results):
    if md5hash == datahash:
        try:
            return md5hash
        except:
            return results
