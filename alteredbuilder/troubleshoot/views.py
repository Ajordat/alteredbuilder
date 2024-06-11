from typing import Any

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.http import HttpResponse, HttpResponseForbidden
from django.urls import reverse
from django.views import View
from django.views.generic.edit import FormView

from .forms import SubmitSessionForm

# Create your views here.

class SubmitSessionFormView(PermissionRequiredMixin, FormView):
    permission_required = "sessions.view_session"
    template_name = "troubleshoot/sessions.html"
    form_class = SubmitSessionForm

    def get_initial(self) -> dict[str, Any]:
        initial = super().get_initial()
        initial["session_key"] = self.request.session.session_key

        return initial
    
    def post(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseForbidden()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid()

    def form_valid(self, form: SubmitSessionForm) -> HttpResponse:
        session_key = form.cleaned_data["session_key"]
        session = Session.objects.get(session_key=session_key)
        uid = session.get_decoded().get("_auth_user_id")
        self.session_user = User.objects.get(id=uid)
        print(uid)
        return self.render_to_response(self.get_context_data(form=form))
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        try:
            context["session_user"] = self.session_user
        except AttributeError:
            pass
        return context
    
    def get_success_url(self) -> str:
        return reverse("troubleshoot:session")



class SessionView(View):
    def get(self, request, *args, **kwargs):
        view = None
        return view(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        view = SubmitSessionFormView.as_view()
        return view(request, *args, **kwargs)