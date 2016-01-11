import json
import itertools
import django.views.generic as generic
import django.views.generic.edit as edit
from django.db import transaction
from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib.auth import authenticate, login, logout
from django.forms import ModelForm, ModelChoiceField
from django.shortcuts import redirect, render
from django.http import HttpResponseRedirect

from .models import Organisation, Project, Party, Parcel, UserPolicyAssignment
from django.contrib.auth.models import User
from tutelary.models import Policy

from .forms import UserSwitchForm, UserForm, UserPolicyForm


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


class PermissionPathMixin:
    def get_context_data(self, **kwargs):
        context = super(PermissionPathMixin, self).get_context_data(**kwargs)
        if 'object' in context:
            obj = context['object']
            if hasattr(obj, 'get_permissions_object'):
                obj.permissions_path = str(obj.get_permissions_object())
        elif 'object_list' in context:
            for obj in context['object_list']:
                if hasattr(obj, 'get_permissions_object'):
                    obj.permissions_path = str(obj.get_permissions_object())
        return context


class ListView(UserMixin, PermissionPathMixin, generic.ListView):
    pass


class DetailView(UserMixin, PermissionPathMixin, generic.DetailView):
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

class UserList(ListView):
    model = User


class UserDetail(DetailView):
    model = User

    def get_context_data(self, **kwargs):
        context = super(UserDetail, self).get_context_data(**kwargs)
        context['policies'] = UserPolicyAssignment.objects.filter(
            user=context['user']
        )
        return context


class UserEdit(generic.FormView):
    model = User
    form_class = UserForm

    def get_success_url(self):
        return reverse('user-detail', kwargs={'pk': self.object.pk})

    def process(self, request, action, user=None):
        main_form = UserForm(request.POST, instance=user)
        policy_forms = [UserPolicyForm(request.POST, prefix=str(i))
                        for i in range(UserPolicyForm.MAX_POLICIES)]
        if main_form.is_valid() and all([pf.is_valid()
                                         for pf in policy_forms]):
            with transaction.atomic():
                self.object = main_form.save()
                if action == 'update':
                    UserPolicyAssignment.objects.filter(
                        user=self.object
                    ).delete()
                for pf, i in zip(policy_forms, itertools.count()):
                    if pf.cleaned_data['policy'] is None:
                        break
                    user_policy = UserPolicyAssignment.objects.create(
                        user=self.object,
                        policy=pf.cleaned_data['policy'],
                        organisation=pf.cleaned_data['organisation'],
                        project=pf.cleaned_data['project'],
                        index=i)
                    user_policy.save()
            print('REDIRECTING:', self.get_success_url())
            return HttpResponseRedirect(self.get_success_url())
        print('RENDERING')
        return render(request, self.template_name,
                      {'main_form': main_form,
                       'policy_forms': policy_forms})


class UserCreate(UserEdit):
    template_name = 'auth/user_form.html'

    def get(self, request, *args, **kwargs):
        main_form = UserForm()
        policy_forms = [UserPolicyForm(prefix=str(i))
                        for i in range(UserPolicyForm.MAX_POLICIES)]
        return render(request, self.template_name,
                      {'main_form': main_form,
                       'policy_forms': policy_forms})

    def post(self, request, *args, **kwargs):
        return self.process(request, 'create')


class UserUpdate(edit.SingleObjectMixin, UserEdit):
    model = User
    template_name = 'auth/user_update_form.html'

    def get(self, request, *args, **kwargs):
        def init_data(p, i):
            r = dict()
            r[str(i) + '-policy'] = p.policy if p else None
            r[str(i) + '-organisation'] = p.organisation if p else None
            r[str(i) + '-project'] = p.project if p else None
            return r
        user = self.get_object()
        pols = list(UserPolicyAssignment.objects.filter(user=user))
        pols += [None] * (UserPolicyForm.MAX_POLICIES - len(pols))
        pols = list(map(init_data, pols, itertools.count()))
        main_form = UserForm(instance=user)
        policy_forms = [UserPolicyForm(pols[i], prefix=str(i))
                        for i in range(UserPolicyForm.MAX_POLICIES)]
        return render(request, self.template_name,
                      {'main_form': main_form,
                       'policy_forms': policy_forms})

    def post(self, request, *args, **kwargs):
        return self.process(request, 'update', self.get_object())


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

    def get_context_data(self, **kwargs):
        context = super(PolicyDetail, self).get_context_data(**kwargs)
        context['pretty_body'] = json.dumps(json.loads(context['object'].body),
                                            indent=2)
        return context


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
