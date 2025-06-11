from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.urls import reverse_lazy

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'account/profile.html'
    login_url = reverse_lazy('account_login')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'profile'
        return context
