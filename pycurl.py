"""PyCurl

Usage:
  pycurl.py (get|put|post) <url> [--headers=<headers> | -H=<headers>]... [--data=<data> | -d=<data>] [--verbose]
  pycurl.py --version

Options:
  -h --help                          Show this screen.
  --version                          Show version.
  --headers <headers>, -H <headers>  Request Headers.
  --verbose                          High Verbosity.
  --data <data>, -d <data>           Request body as json.

Example:
  pycurl.py get https://httpbin.org/get --headers='Content-Type=application/json' --data='{"id":"that"}' --verbose
  pycurl.py post https://httpbin.org/post --headers='Content-Type=application/json' --data='{"id":"that"}' --verbose
  pycurl.py put https://httpbin.org/put --headers='Content-Type=application/json' --data='{"id":"that"}' --verbose
"""

from docopt import docopt
import requests
import logging
from schema import Schema, And, Or, Use, Regex, SchemaError
import json

def get(url: str, headers: dict = {}, body: dict = {}) -> int:
  """A very simplified REST GET using python requests

  Arguments:
    url (str): A url to perform the get on
    headers (dict): An optional dictionary of headers to send with the request
    body (dict): An optional json body to send with the request

  Returns:
    success (int): 0 for success, 1 for failure to imitate shells
  """
  r = requests.get(url, headers=headers, json=body)
  return _log_response(r)

def post(url: str, headers: dict = {}, body: dict = {}) -> int:
  """A very simplified REST POST using python requests

  Arguments:
    url (str): A url to perform the get on
    headers (dict): An optional dictionary of headers to send with the request
    body (dict): An optional json body to send with the request

  Returns:
    success (int): 0 for success, 1 for failure to imitate shells
  """
  r = requests.post(url, headers=headers, json=body)
  return _log_response(r)

def put(url: str, headers: dict = {}, body: dict = {}) -> int:
  """A very simplified REST PUT using python requests

  Arguments:
    url (str): A url to perform the get on
    headers (dict): An optional dictionary of headers to send with the request
    body (dict): An optional json body to send with the request

  Returns:
    success (int): 0 for success, 1 for failure to imitate shells
  """
  r = requests.put(url, headers=headers, json=body)
  return _log_response(r)

def _log_response(r: requests.models.Response) -> int:
  """Logs the request info and returns success or failure

  Arguments:
    r (requests.models.Response): A response to check

  Returns:
    success (int): 0 for success, 1 for failure to imitate shells
  """
  if (r.ok):
    logging.info(r.text)
    return 0
  logging.error(r.text)
  return 1

def main():
  arguments = docopt(__doc__, version='pycurl 0.1.0')

  try:
    schema = Schema({
      '<url>': Regex(r"^http(s)?:\/\/", error="URL must begin with http:// or https://."),
      '--data': Or(None, json.loads, error="Body must be in json format."),
      '--headers': Or(None, And(lambda x: '=' in ''.join(x), lambda y: ''.join(y).count('=') == len(y)), error="Headers must be in KEY=VALUE format."),
      '--verbose': Or(True, False),
      '--version': Or(True, False),
      'get': Or(True, False),
      'post': Or(True, False),
      'put': Or(True, False)
    })
  except SchemaError as e:
    print(str(e))
    return 1

  arguments = schema.validate(arguments)
  log_level = logging.DEBUG if arguments['--verbose'] else logging.INFO

  logging.basicConfig(level=log_level)

  url     = arguments['<url>']
  headers = {header.split('=')[0]: header.split('=')[1] for header in arguments['--headers']}
  body    = json.loads(arguments['--data']) if arguments['--data'] else None
  rc      = 0

  logging.debug(f"Sending request to {url} with {headers} and {body}")

  if (arguments['get']):
    rc = get(url, headers, body)
  elif (arguments['post']):
    rc = post(url, headers, body)
  elif (arguments['put']):
    rc = put(url, headers, body)
  
  return rc

if __name__ == '__main__':
    exit(main())