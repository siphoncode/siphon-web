set -e # stop if any of these commands fail

touch /volumes/logs/django.log /volumes/logs/uwsgi.log
chown web:web /volumes/logs/*.log

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Building/minifying bundles..."
./node_modules/grunt-cli/bin/grunt --gruntfile Gruntfile.js production

echo "Running migrations..."
python manage.py migrate

echo "Starting the app..."
supervisord -n
