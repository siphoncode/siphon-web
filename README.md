siphon-web
==========

Building
--------

Follow the instructions here to install `nvm`:

https://github.com/creationix/nvm

Then install `node`:

    $ nvm install 4.2.1
    $ nvm alias default 4.2.1
    $ nvm use default

Install the node dependencies:

    $ cd /path/to/this/cloned/repo
    $ npm install

You will also need

Ensure that Python 3.4 is installed:

    $ brew install python3

For convenience, install `virtualenvwrapper` on your machine:

    $ pip install virtualenvwrapper
    $ export WORKON_HOME=~/.virtualenv # put this in your .bash_profile too
    $ mkdir -p $WORKON_HOME

Create a virtual environment and activate it:

    $ mkvirtualenv --python=`which python3` siphon-web
    $ workon siphon-web
    $ python --version # should be Python 3.4.x

Install the Python dependencies:

    $ cd /path/to/this/cloned/repo
    $ pip install -r requirements.txt

Running locally
---------------

To run the Django development server locally (with SQLite):

    $ ./run-local.sh

To run all containers including PostgreSQL and RabbitMQ:

    $ ./run-local-containers.sh

To inspect the logs (only works while the containers are running):

    ./run-local-containers.sh --logs

To run `psql` and inspect the databse (only works while the containers are
running):

    $ ./run-local-containers.sh --psql

Deploying
---------

You should work on new features in a separate branch:

    $ git checkout -b my-new-feature

When you think it won't break, merge into the `staging` branch and the
orchestration server will deploy it for you:

    $ git checkout staging
    $ git merge my-new-feature
    $ git push origin staging

When staging looks stable, deploy to production:

    $ git checkout production
    $ git merge staging
    $ git push origin production

You will need to confirm this deploy in the `#announce` Slack channel.

Making changes to the blog
--------------------------

See `README.md` in `siphon-web/blog` for instructions.

Uploading images to S3
----------------------

To make it easy to reference images in newsletters, there is a management
command that takes a local file path and uploads it to a public
S3 key, giving back a URL:

$ SIPHON_ENV=dev ./manage.py image_to_s3 /some/path/to/image.png
