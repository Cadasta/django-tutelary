import django.views.generic as generic
import django.views.generic.edit as edit
from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib.auth import authenticate, login, logout
from django.forms import ModelForm, ModelChoiceField
from django.shortcuts import redirect

from .models import Organisation, Project, Party, Parcel
from django.contrib.auth.models import User, AnonymousUser
from tutelary.models import Policy

from .forms import UserSwitchForm


# ----------------------------------------------------------------------
#
#  BASE CLASSES
#

class UserMixin:
    def get_context_data(self, **kwargs):
        context = super(UserMixin, self).get_context_data(**kwargs)
        context['users'] = User.objects.all()
        context['user_switch_form'] = UserSwitchForm(
            initial={'username': self.request.user.username}
        )
        return context


class ListView(UserMixin, generic.ListView):
    pass


class DetailView(UserMixin, generic.DetailView):
    pass


class CreateView(UserMixin, edit.CreateView):
    pass


class UpdateView(UserMixin, edit.UpdateView):
    pass


class DeleteView(UserMixin, edit.DeleteView):
    pass


# ----------------------------------------------------------------------
#
#  HOME PAGE
#

class IndexView(UserMixin, generic.TemplateView):
    template_name = 'exampleapp/index.html'


# ----------------------------------------------------------------------
#
#  USERS
#

class UserList(CreateView):
    model = User
    fields = ['username']
    success_url = reverse_lazy('user-list')


class UserDelete(DeleteView):
    model = User
    success_url = reverse_lazy('user-list')


class SwitchUser(generic.View):
    def post(self, request, *args, **kwargs):
        newuser = authenticate(username=request.POST['username'])
        if newuser is not None:
            login(request, newuser)
        else:
            logout(request)
        return redirect(request.META.get('HTTP_REFERER', '/'))


# ----------------------------------------------------------------------
#
#  POLICIES
#

class PolicyList(ListView):
    model = Policy


class PolicyDetail(DetailView):
    model = Policy


class PolicyCreate(CreateView):
    model = Policy
    fields = ['name', 'body']

    def get_success_url(self):
        return reverse('policy-detail', kwargs={'pk': self.object.pk})


class PolicyUpdate(UpdateView):
    model = Policy
    fields = ['name', 'body']
    template_name_suffix = '_update_form'

    def get_success_url(self):
        return reverse('policy-detail', kwargs={'pk': self.object.pk})


class PolicyDelete(DeleteView):
    model = Policy
    success_url = reverse_lazy('policy-list')


# ----------------------------------------------------------------------
#
#  ORGANISATIONS
#

class OrganisationList(ListView):
    model = Organisation


class OrganisationCreate(CreateView):
    model = Organisation
    fields = ['name']
    success_url = reverse_lazy('organisation-list')


class OrganisationDelete(DeleteView):
    model = Organisation
    success_url = reverse_lazy('organisation-list')


# ----------------------------------------------------------------------
#
#  PROJECTS
#

class ProjectList(ListView):
    model = Project


class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = ('name', 'organisation')

    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)
        self.fields['organisation'] = ModelChoiceField(
            queryset=Organisation.objects.all(), empty_label=None
        )


class ProjectCreate(CreateView):
    model = Project
    form_class = ProjectForm
    success_url = reverse_lazy('project-list')


class ProjectDelete(DeleteView):
    model = Project
    success_url = reverse_lazy('project-list')


# ----------------------------------------------------------------------
#
#  PARTIES
#

class PartyList(ListView):
    model = Party


class PartyDetail(DetailView):
    model = Party


class PartyForm(ModelForm):
    class Meta:
        model = Party
        fields = ('name', 'project')

    def __init__(self, *args, **kwargs):
        super(PartyForm, self).__init__(*args, **kwargs)
        self.fields['project'] = ModelChoiceField(
            queryset=Project.objects.all(), empty_label=None
        )


class PartyCreate(CreateView):
    model = Party
    form_class = PartyForm


class PartyUpdate(UpdateView):
    model = Party
    form_class = PartyForm
    template_name_suffix = '_update_form'


class PartyDelete(DeleteView):
    model = Party
    success_url = reverse_lazy('party-list')


# ----------------------------------------------------------------------
#
#  PARCELS
#

class ParcelList(ListView):
    model = Parcel


class ParcelDetail(DetailView):
    model = Parcel


class ParcelForm(ModelForm):
    class Meta:
        model = Parcel
        fields = ('address', 'project')

    def __init__(self, *args, **kwargs):
        super(ParcelForm, self).__init__(*args, **kwargs)
        self.fields['project'] = ModelChoiceField(
            queryset=Project.objects.all(), empty_label=None
        )


class ParcelCreate(CreateView):
    model = Parcel
    form_class = ParcelForm


class ParcelUpdate(UpdateView):
    model = Parcel
    form_class = ParcelForm
    template_name_suffix = '_update_form'


class ParcelDelete(DeleteView):
    model = Parcel
    success_url = reverse_lazy('parcel-list')
