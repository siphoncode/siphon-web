
from django.views.generic.base import TemplateView
from siphon.web.apps.apps.models import BaseVersion


class BaseVersionView(TemplateView):
    template_name = 'docs/base-version.html'

    def get_context_data(self, **kwargs):
        context = super(BaseVersionView, self).get_context_data(**kwargs)
        context['base_versions'] = BaseVersion.objects.all().order_by('-name')
        return context
