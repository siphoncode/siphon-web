#/bin/env python

echo "Checking for local postgres..."
if brew services list | grep "postgresql\s*started" > /dev/null; then
    echo "OK."
else
    echo "ERROR: local postgres not found!"
    echo
    echo "Please make sure postgres is installed and running locally:"
    echo "  $ brew install postgresql"
    echo "  $ brew services start postgresql"
    exit 1
fi

#SIPHON_ENV=dev python -Wall manage.py test siphon.web
if [ "$#" -eq 0 ]; then
  SIPHON_ENV=dev python manage.py test siphon.web
elif [ "$#" -eq 1 ]; then
  SIPHON_ENV=dev python manage.py test siphon.web.$@
else
  echo "Provide no arguments to run all tests or a single argument to run a specific test case"
fi
