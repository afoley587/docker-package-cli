# Using base python image
FROM docker.io/python:3.9-slim

# Add a new group and user for the CLI to run as
# Not required, but a good practice
RUN groupadd -g 10001 --system pycurl && \
    useradd -ms /bin/bash -u 10000 --system -g pycurl -d /home/pycurl pycurl

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

# copy in our app
COPY --chown=pycurl:pycurl pycurl.py /home/pycurl/

# Set our entrypoint so people can run
# docker run pycurl <args...>
ENTRYPOINT ["python", "/home/pycurl/pycurl.py"]