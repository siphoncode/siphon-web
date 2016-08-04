FROM python:3.4

RUN apt-get update && apt-get install -q -y --force-yes git curl wget nginx supervisor cron nodejs libpq-dev

# Set up environment vars for nvm+node
ENV NVM_DIR /usr/local/nvm
ENV NODE_VERSION 4.2.1
ENV NODE_PATH $NVM_DIR/v$NODE_VERSION/lib/node_modules
ENV PATH $NVM_DIR/versions/node/v$NODE_VERSION/bin:$PATH

# Install nvm+node
RUN curl https://raw.githubusercontent.com/creationix/nvm/v0.29.0/install.sh | bash
RUN cat $NVM_DIR/nvm.sh >> install-node.sh
RUN echo "nvm install $NODE_VERSION" >> install-node.sh
RUN echo "nvm alias default $NODE_VERSION" >> install-node.sh
RUN echo "nvm use default" >> install-node.sh
RUN echo "npm install npm@3.9.6 -g" >> install-node.sh
RUN sh install-node.sh

# Blog prerequisites
RUN gpg --keyserver pgp.mit.edu --recv-keys 409B6B1796C275462A1703113804BB82D39DC0E3
RUN curl -L https://get.rvm.io | bash -s stable
RUN mkdir -p /code/blog
ADD blog/Gemfile /code/blog/
ADD blog/Gemfile.lock /code/blog/
RUN echo "set -e" >> install-blog.sh
RUN echo "source /etc/profile.d/rvm.sh" >> install-blog.sh
RUN echo "rvm install 1.9.3 && rvm rubygems current && gem install bundler" >> install-blog.sh
RUN echo "(cd /code/blog && bundle install)" >> install-blog.sh
RUN chmod +x install-blog.sh && /bin/bash -c ./install-blog.sh

# Make the source code directory and install our main dependencies
RUN mkdir -p /code
ADD requirements.txt /code/
WORKDIR /code
RUN pip install -r requirements.txt

# Add our non-priv user for Django to run as
RUN adduser --disabled-password --gecos "" web
RUN chown -R web:web /code
USER web

# Install node dependencies
ADD package.json /code/
RUN cat $NVM_DIR/nvm.sh >> install-node-modules.sh
RUN echo "npm install --loglevel http" >> install-node-modules.sh
RUN sh install-node-modules.sh

# Add only the files we need server-side
ADD siphon /code/siphon
ADD static /code/static
ADD templates /code/templates
ADD Gruntfile.js manage.py /code/

# SSL and handshake keys
RUN mkdir -p /code/.keys
ADD deployment/keys/ /code/.keys/

# Config for nginx and supervisor (also switch back to root because supervisor
# will give up root for us)
USER root
RUN rm /etc/nginx/sites-enabled/*
ADD deployment/nginx.conf /etc/nginx/nginx.conf
ADD deployment/supervisor-web.conf /etc/supervisor/conf.d/
ADD deployment/uwsgi.ini /code/uwsgi.ini

# Cronjob for running django-drip. Note that because cron does not seem to know
# about Docker's environment variables, we have to read them in from a file
# that we write below in entrypoint.sh at runtime.
RUN echo "*/5 * * * * env - \`cat /tmp/env.sh\` /bin/bash -c '(cd /code && /usr/bin/env python manage.py send_drips) >> /volumes/logs/drip-cron.log 2>>\&1'" | crontab -

# Clone siphon-cli and checkout to a specific commit
ENV BITBUCKET_API_KEY CHANGEME
ENV CLI_COMMIT 103a749
ENV CLI_REPO /tmp/siphon-cli
RUN git clone https://getsiphon:${BITBUCKET_API_KEY}@bitbucket.org/getsiphon/siphon-cli.git ${CLI_REPO} && echo ${CLI_COMMIT} # cache breaker
WORKDIR ${CLI_REPO}
RUN git checkout ${CLI_COMMIT}

# Clone siphon-base and checkout to a specific commit
ENV BASE_COMMIT 91141e0
ENV BASE_REPO /tmp/siphon-base
RUN git clone https://getsiphon:${BITBUCKET_API_KEY}@bitbucket.org/getsiphon/siphon-base.git ${BASE_REPO} && echo ${BASE_COMMIT}
WORKDIR ${BASE_REPO}
RUN git checkout ${BASE_COMMIT}
RUN python $BASE_REPO/siphon-base-install.py
WORKDIR /code

# Generate the final blog output
ADD blog /code/blog
RUN echo "source /etc/profile.d/rvm.sh && (cd /code/blog && rake site:generate)" >> generate-blog.sh
RUN chmod +x generate-blog.sh && /bin/bash -c ./generate-blog.sh

# Generate the client installer script, but we won't run it until runtime
# because then we'll have the right environment variables set
RUN echo "#!/bin/bash" >> /tmp/generate-installer.sh
RUN echo "set -e" >> /tmp/generate-installer.sh
RUN echo "mkdir -p /code/.static/cli" >> /tmp/generate-installer.sh
RUN echo "python $CLI_REPO/generate-installer.py --platform posix \
    --version $CLI_COMMIT --host \$CLI_HOST --port \$CLI_PORT \
    --remote-path /static/cli \
    --dest /code/.static/cli/" >> /tmp/generate-installer.sh
RUN chmod +x /tmp/generate-installer.sh

# Make a script for generating the cli packages
RUN echo "#!/bin/bash" >> /tmp/generate-cli-packages.sh
RUN echo "set -e" >> /tmp/generate-cli-packages.sh
RUN echo "python $BASE_REPO/generate-cli-packages.py \
    --dest /code/.static/cli" >> /tmp/generate-cli-packages.sh

RUN mkdir /code/.static && chown -R web:web /code/.static

ADD deployment/entrypoint.sh /code/base-entrypoint.sh
RUN echo "env > /tmp/env.sh" >> entrypoint.sh # for cron
RUN echo "/bin/bash -c '. /tmp/generate-installer.sh'" >> entrypoint.sh
RUN echo "/bin/bash -c '. /tmp/generate-cli-packages.sh'" >> entrypoint.sh
RUN cat $NVM_DIR/nvm.sh base-entrypoint.sh >> entrypoint.sh
ENTRYPOINT ["sh", "entrypoint.sh"]
