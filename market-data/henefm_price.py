#!/usr/bin/env python3
"""On-demand personal HeneFM price lookup. No polling or saved API responses."""
import argparse
import getpass
import json
import re
import sys
import urllib.request
import urllib.error

BASE = 'https://henefm.com/api/v2/'

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def lookup(key, path):
    if not re.fullmatch(r'(?:me|market|items/[1-9][0-9]{0,8}/price)', path):
        raise ValueError('Unsupported personal API endpoint')
    req = urllib.request.Request(BASE + path, headers={
        'Authorization': 'Bearer ' + key,
        'User-Agent': 'PersonalMarketPriceResearch/1.0',
        'Accept': 'application/json',
    })
    opener = urllib.request.build_opener(NoRedirect())
    with opener.open(req, timeout=20) as response:
        return json.load(response)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('item_id', nargs='?', type=int, help='One item ID to look up')
    parser.add_argument('--market', action='store_true', help='Show market activity summary instead')
    args = parser.parse_args()
    if args.market and args.item_id is not None:
        parser.error('Choose a single item or --market')
    if args.item_id is not None and not 1 <= args.item_id <= 999999999:
        parser.error('Invalid item ID')
    key = getpass.getpass('HeneFM personal API key (hidden): ').strip()
    if not re.fullmatch(r'hfm_(?!app_)[A-Za-z0-9_-]+', key):
        sys.exit('Expected a personal hfm_ API key.')
    try:
        me = lookup(key, 'me')
        # Do not print even the masked key or account details.
        print(json.dumps({k: me.get(k) for k in ('kind','status','limits','today')}, indent=2))
        if args.market or args.item_id is not None:
            path = 'market' if args.market else f'items/{args.item_id}/price'
            print('Prices from HeneFM: https://henefm.com')
            print(json.dumps(lookup(key, path), indent=2))
    except urllib.error.HTTPError as e:
        print(f'HTTP {e.code}; Retry-After: {e.headers.get("Retry-After", "not supplied")}.', file=sys.stderr)
        return 1
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        print(f'Request failed ({type(e).__name__}); check connection or response format.', file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
