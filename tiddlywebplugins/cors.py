"""
CORS preflight OPTIONS checks for TiddlyWeb.
"""

class PreFlightCheck(object):
    pass

def init(config):
    if 'selector' in config:
        if PreFlightCheck not in config['server_request_filters']:
            config['server_request_filters'].append(PreFlightCheck)
