# Blog

## Motivation

Everyone is writing command line utilities these days, whether it's for
some internal tool, some personal automation project, or something
completely different. However, how do we share these utilites?
Are you going to make a brew package for Mac users, a .deb or .rpm
for other linux users? What about hardware dependencies? As you can see,
there can be a lot of difficulties with distributing a command line utility
to fit everyone's needs.

If only there was a way to abstract all of these tiny details away from you
so you can distribute your tool with a single package? Oh wait - that sounds
a lot like docker!

That's exactly what we are going to do today. We're going to create a very simple
python CLI utility which we package up in a docker container and then can distribute
as you see fit. Like I said before, our CLI is going to be simple. It's just going to
send HTTP requests, similarly to cURL. However, this could definitely be expanded to:

* Query your AWS account for insights into your infrastructure
* Upload/transfer/manipulate files in an S3 bucket
* Connect to GCP to do some processing
* etc.

As always, any and all code referenced will be publically available on github: https://github.com/afoley587/docker-package-cli

## The CLI
So, let's start with the CLI. We are going to be using python as our language
and poetry as our virtual environment. If you are unfamiliar with either 
of those, do not worry. We will talk through all the pieces you need to be successful.

There are a lot of great python argument parsing utilities our there:

* [argparse](https://docs.python.org/3/library/argparse.html)
* [click](https://click.palletsprojects.com/en/8.1.x/)
* [docopt](http://docopt.org/)

And I chose `docopt` for today because its easy to use and takes a lot of the
heavy lifting off of the programmer. `docopt` is going to parse our docstring
and then generate the arguments based off of that. Our docstring looks something like:

```shell
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
```

So `docopt` will parse this, create a dictionary of possible arguments, and then we can act
on them accordingly.

Next, because we have established that we are building a cURL-type utility, we need some helper functions which
will send our REST calls. Lets define a function to perform an HTTP GET, POST, and PUT as well as a common
function to log our responses:

```python
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
```

You might notice that these functions could easily just be replaced by
the direct `requests` package without the need for a wrapper. However, 
I find it helpful to write wrappers around just in case we wanted to do 
any pre or post validation on our data.

With our docstring and helper functions done, we are now ready to write the 
glue that ties it all together. I've done this below with our `main` function:

```python
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
```

Let's disect this. First, we use doctopt to turn our docstring
into a usable dictionary of arguments. Next, we use the schema
package to validate all of the inputs the user provided. This helps us
catch things like:

* malformed urls
* improper data bodies
* enforcing a consistent header format

Once our arguments are validated, can begin to use them. We do that first by checking
the verbosity level provided by the user. If they requested `--verbose`, we set our log level
to DEBUG, otherwise we leave it as INFO. We then transform our headers from the `header1=val` format
that the user passed it in as to a python-usable dictionary using dictionary comprehension. We do 
something similar with the `--data` flag if the user provided it by loading into json.

Now, we're ready to execute! We can then use the helper functions we defined above to perform the 
GET, PUT, or POST and we can then exit with the proper return codes. Our CLI is done!

## Packaging
Now that our CLI is done, we can package it up nicely. For this, we are going to use docker.

Our Dockerfile isn't too big, and we are going to walk through it from top to bottom.

First, we are going to use the pre-built python slim image hosted on python's public repo:

```shell
# Using base python image
FROM docker.io/python:3.9-slim
```

Next, we're going to create a user to run the commands as. While this isn't necessary,
it is typically a good practice so that we don't have commands running as root:

```shell
# Add a new group and user for the CLI to run as
# Not required, but a good practice
RUN groupadd -g 10001 --system pycurl && \
    useradd -ms /bin/bash -u 10000 --system -g pycurl -d /home/pycurl pycurl
```

We are then just going to install poetry using `pip`, copy in our `pyproject.toml` and `poetry.lock` files,
and then install all of our python dependencies. poetry is a virtual environment
manager which I really love to use on my localhost computer. By using poetry in the container,
I dont have to maintain both a `pyproject.toml` and a `requirements.txt`:

```shell
# Install poetry for our dependency management
RUN pip install poetry==1.2.2

# Change to the home directory for remainder of
# our work
WORKDIR /home/pycurl/

# Copy in our dependencies into the container
COPY --chown=pycurl:pycurl pyproject.toml poetry.lock /home/pycurl/

# Install our dependencies onto path by using pip so we dont have
# to prefix everything with poetry run
RUN poetry export -f requirements.txt -o requirements.txt --without-hashes && \
    pip install -r requirements.txt
```

As the last piece of the puzzle, we will copy in our actual python file and set
the entrypoint to be our script:

```shell
# copy in our app
COPY --chown=pycurl:pycurl pycurl.py /home/pycurl/

# Set our entrypoint so people can run
# docker run pycurl <args...>
ENTRYPOINT ["python", "/home/pycurl/pycurl.py"]
```

A quick note is that we could have done one big `COPY` upstream. However, that would mean that
any time our script changes, docker would detect those changes and then re-build all image layers.
In essence, it might force us to redo all of our pip installs and might add a long time to our
builds!

## Running
So we now have two things:

* Our cool CLI
* A way to package it up

So let's build, run, and play with our CLI!

We can build our image by running:

```shell
prompt> docker build . -t pycurl-docker
[+] Building 0.1s (12/12) FINISHED                                                                                                                                    
 => [internal] load build definition from Dockerfile                                                                                                             0.0s
 => => transferring dockerfile: 37B                                                                                                                              0.0s
 => [internal] load .dockerignore                                                                                                                                0.0s
 => => transferring context: 2B                                                                                                                                  0.0s
 => [internal] load metadata for docker.io/library/python:3.9-slim                                                                                               0.0s
 => [1/7] FROM docker.io/library/python:3.9-slim                                                                                                                 0.0s
 => [internal] load build context                                                                                                                                0.0s
 => => transferring context: 96B                                                                                                                                 0.0s
 => CACHED [2/7] RUN groupadd -g 10001 --system pycurl &&     useradd -ms /bin/bash -u 10000 --system -g pycurl -d /home/pycurl pycurl                           0.0s
 => CACHED [3/7] RUN pip install poetry==1.2.2                                                                                                                   0.0s
 => CACHED [4/7] WORKDIR /home/pycurl/                                                                                                                           0.0s
 => CACHED [5/7] COPY --chown=pycurl:pycurl pyproject.toml poetry.lock /home/pycurl/                                                                             0.0s
 => CACHED [6/7] RUN poetry export -f requirements.txt -o requirements.txt --without-hashes &&     pip install -r requirements.txt                               0.0s
 => CACHED [7/7] COPY --chown=pycurl:pycurl pycurl.py /home/pycurl/                                                                                              0.0s
 => exporting to image                                                                                                                                           0.0s
 => => exporting layers                                                                                                                                          0.0s
 => => writing image sha256:4bb3471f91255070206d934f6830b5e5d65926c41e75736ec9a023d42d043386                                                                     0.0s
 => => naming to docker.io/library/pycurl-docker                                                                                                                 0.0s

Use 'docker scan' to run Snyk tests against images to find vulnerabilities and learn how to fix them
```

And we can now run it with:
```shell
prompt> docker run pycurl-docker put https://httpbin.org/put --headers='Content-Type=application/json' --data='{"id":"that"}' --verbose
DEBUG:root:Sending request to https://httpbin.org/put with {'Content-Type': 'application/json'} and {'id': 'that'}
DEBUG:urllib3.connectionpool:Starting new HTTPS connection (1): httpbin.org:443
DEBUG:urllib3.connectionpool:https://httpbin.org:443 "PUT /put HTTP/1.1" 200 475
INFO:root:{
  "args": {}, 
  "data": "{\"id\": \"that\"}", 
  "files": {}, 
  "form": {}, 
  "headers": {
    "Accept": "*/*", 
    "Accept-Encoding": "gzip, deflate", 
    "Content-Length": "14", 
    "Content-Type": "application/json", 
    "Host": "httpbin.org", 
    "User-Agent": "python-requests/2.28.1", 
    "X-Amzn-Trace-Id": "Root=1-6377efb8-20f592843ad2e62361db289b"
  }, 
  "json": {
    "id": "that"
  }, 
  "origin": "174.21.91.56", 
  "url": "https://httpbin.org/put"
}
```

Congratulations! You've just built and packaged a neat CLI!