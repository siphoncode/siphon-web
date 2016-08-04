
import arrow

import json

from django.http import Http404
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from django.contrib.auth.models import User

def get_weeks(start=None):
    # Get the very first join date
    dt = User.objects.order_by('date_joined').first().date_joined
    default_start = arrow.get(dt).replace(weeks=+1)
    if start is None:
        start = default_start
    start = start.floor('week')  # make sure its a Monday
    # Protect against divide by zero
    if start < default_start:
        start = default_start
    start = start.floor('week')  # make sure its a Monday
    # Return a range of mondays
    end = arrow.now().replace(weeks=+1).floor('week')
    return arrow.Arrow.range('week', start=start, end=end)

def weekly_user_growth():
    if User.objects.count() < 1:
        return []

    # Get the weekly user counts
    user_counts = []
    weeks = get_weeks(start=arrow.Arrow(2016, 1, 11))  # avoid the crazy days
    for dt in weeks:
        x = dt.datetime
        c = User.objects.filter(date_joined__lte=x).count()
        user_counts.append(c)

    data = []
    percentages = [100.0 * a1 / a2 - 100 for a1, a2 in
                   zip(user_counts[1:], user_counts)]
    for i, perc in enumerate(percentages):
        week_name = weeks[i + 1].format('YYYY-MM-DD')
        data.append([week_name, perc, 10])
    return data

def cumulative_users():
    weeks = get_weeks()
    data = []
    for dt in weeks:
        x = dt.datetime
        c = User.objects.filter(date_joined__lte=x).count()
        data.append([dt.format('YYYY-MM-DD'), c])
    return data

@require_http_methods(['GET'])
def analytics(request):
    if not request.user or not request.user.is_staff:
        raise Http404()

    return render(request, 'analytics.html', {
        'weekly_user_growth': json.dumps(weekly_user_growth()),
        'cumulative_users': json.dumps(cumulative_users())
    })
