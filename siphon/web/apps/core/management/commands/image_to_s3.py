
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from uuid import uuid4
import tinys3
import os

AWS_ACCESS_KEY_ID = 'AKIAJOAPGZD2SYWXWBWQ'
AWS_SECRET_ACCESS_KEY = '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'


def key_name_for_path(p):
    s = str(uuid4())
    basename = os.path.basename(p)
    if '.' in basename:
        s += '.' + basename.split('.')[-1]
    return s


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('image_path', type=str)

    def handle(self, *args, **options):
        image_path = options['image_path']
        key_name = key_name_for_path(image_path)
        print('Uploading "%s" to "%s" on S3...' % (image_path, key_name))

        conn = tinys3.Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, default_bucket='siphon-assets')
        with open(image_path, 'rb') as fp:
            result = conn.upload(key_name, fp, public=True)

        print('Done.')
        print('\n--> %s' % result.url)
