# From python 3.4 asyncio/base_events.py
# Needs a forelselast grammar rule

def create_connection(self, infos, f2, laddr_infos, protocol):
    for family in infos:
        try:
            if f2:
                for laddr in laddr_infos:
                    try:
                        break
                    except OSError:
                        protocol = 'foo'
                else:
                    continue
        except OSError:
            protocol = 'bar'
        else:
            break
    else:
        raise

    return protocol
