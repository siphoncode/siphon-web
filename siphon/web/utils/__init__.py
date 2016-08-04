
import json
from django.http import HttpResponse

def make_error(s, status=400):
    return HttpResponse(json.dumps({'detail': s}), status=status,
        content_type='application/json')
