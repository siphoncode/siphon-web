
import os
from django.conf import settings

def environment(request):
    return {
        'SIPHON_ENV': os.environ['SIPHON_ENV'],
        'DEBUG': settings.DEBUG
    }
