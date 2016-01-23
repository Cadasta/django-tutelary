import json
import itertools
import django.views.generic as generic
import django.views.generic.edit as edit
from django.db import transaction
from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib.auth import authenticate, login, logout, get_backends
from django.contrib import messages
from django.forms import ModelForm, ModelChoiceField
from django.shortcuts import redirect, render
from django.http import HttpResponseRedirect

from .models import (
    Organisation, Project, Party, Parcel, UserPolicyAssignment,
    set_user_policies
)
from django.contrib.auth.models import User
from tutelary.base import Action
from tutelary.models import Policy
import tutelary.mixins

from .forms import UserSwitchForm, UserForm, UserPolicyForm


# ----------------------------------------------------------------------
#
#  BASE CLASSES
#

class UserMixin:
    """
    Mixin to add a user list and a form for switching users to all
    views: we're using a custom authentication backend that allows for
    switching between users without any authentication for demonstration
    purposes.

    """
    def get_context_data(self, **kwargs):
        context = super(UserMixin, self).get_context_data(**kwargs)
        context['users'] = User.objects.all()
        context['user_switch_form'] = UserSwitchForm(
            initial={'username': self.request.user.username}
        )
        return context


class PermissionInfoMixin:
    """
    Mixin to add the permissions path of objects being displayed to
    any view, along with list of permitted actions.

    """
    def get_context_data(self, **kwargs):
        context = super(PermissionInfoMixin, self).get_context_data(**kwargs)
        if 'object' in context:
            obj = context['object']
            if hasattr(obj, 'get_permissions_object'):
                obj.permissions_path = str(obj.get_permissions_object())
                acts = list(map(str, get_backends()[0].permitted_actions(
                    self.request.user, obj.get_permissions_object()
                )))
        elif 'object_list' in context:
            actcnts = {}
            for obj in context['object_list']:
                if hasattr(obj, 'get_permissions_object'):
                    obj.permissions_path = str(obj.get_permissions_object())
                    objacts = get_backends()[0].permitted_actions(
                        self.request.user, obj.get_permissions_object()
                    )
                    for a in objacts:
                        if a in actcnts:
                            actcnts[a] += 1
                        else:
                            actcnts[a] = 1
            acts = []
            for act, cnt in actcnts.items():
                if cnt == len(context['object_list']):
                    acts.append(str(act))
                else:
                    acts.append('(' + str(act) + ')')
        context['actions'] = acts
        return context


class PermissionRequiredMixin(tutelary.mixins.PermissionRequiredMixin):
    def handle_no_permission(self):
        # Stop a redirect loop here.
        if len(messages.get_messages(self.request)) > 0:
            return redirect('/')
        messages.add_message(self.request, messages.ERROR, "PERMISSION DENIED")
        return redirect(self.request.META.get('HTTP_REFERER', '/'))


class ListView(UserMixin, PermissionInfoMixin, PermissionRequiredMixin,
               generic.ListView):
    """
    Generic list view with user list, object permission paths and
    permission handling.

    """
    pass


class DetailView(UserMixin, PermissionInfoMixin, PermissionRequiredMixin,
                 generic.DetailView):
    """
    Generic detail view with user list, object permission paths and
    permission handling.

    """
    pass


class FormView(UserMixin, PermissionInfoMixin, PermissionRequiredMixin,
               generic.FormView):
    """
    Generic form view with user list, object permission paths and
    permission handling.

    """
    pass


class CreateView(UserMixin, PermissionRequiredMixin, edit.CreateView):
    """
    Generic create view with user list and permission handling.

    """
    pass


class UpdateView(UserMixin, PermissionRequiredMixin, edit.UpdateView):
    """
    Generic update view with user list and permission handling.

    """
    pass


class DeleteView(UserMixin, PermissionRequiredMixin, edit.DeleteView):
    """
    Generic delete view with user list and permission handling.

    """
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
    permission_required = 'user.list'


class UserDetail(DetailView):
    model = User
    permission_required = 'user.detail'

    def get_context_data(self, **kwargs):
        context = super(UserDetail, self).get_context_data(**kwargs)
        context['policies'] = UserPolicyAssignment.objects.filter(
            user=context['user']
        )
        return context


class UserEdit(FormView):
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
                set_user_policies(self.object)
            return HttpResponseRedirect(self.get_success_url())
        return render(request, self.template_name,
                      {'main_form': main_form,
                       'policy_forms': policy_forms})


class UserCreate(UserEdit):
    template_name = 'auth/user_form.html'
    permission_required = 'user.create'

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
    template_name = 'auth/user_update_form.html'
    permission_required = 'user.edit'

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
    permission_required = 'user.delete'


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
    permission_required = 'policy.list'


class PolicyDetail(DetailView):
    model = Policy
    permission_required = 'policy.detail'

    def get_context_data(self, **kwargs):
        context = super(PolicyDetail, self).get_context_data(**kwargs)
        context['pretty_body'] = json.dumps(json.loads(context['object'].body),
                                            indent=2)
        return context


class PolicyCreate(CreateView):
    model = Policy
    fields = ['name', 'body']
    permission_required = 'policy.create'

    def get_success_url(self):
        return reverse('policy-detail', kwargs={'pk': self.object.pk})


class PolicyUpdate(UpdateView):
    model = Policy
    fields = ['name', 'body']
    template_name_suffix = '_update_form'
    permission_required = 'policy.edit'

    def get_success_url(self):
        return reverse('policy-detail', kwargs={'pk': self.object.pk})


class PolicyDelete(DeleteView):
    model = Policy
    success_url = reverse_lazy('policy-list')
    permission_required = 'policy.delete'


# ----------------------------------------------------------------------
#
#  ORGANISATIONS
#

class OrganisationList(ListView):
    model = Organisation
    permission_required = 'org.list'


class OrganisationCreate(CreateView):
    model = Organisation
    fields = ['name']
    success_url = reverse_lazy('organisation-list')
    permission_required = 'org.create'


class OrganisationDelete(DeleteView):
    model = Organisation
    success_url = reverse_lazy('organisation-list')
    permission_required = 'org.delete'


# ----------------------------------------------------------------------
#
#  PROJECTS
#

class ProjectList(ListView):
    model = Project
    permission_required = 'project.list'


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
    permission_required = 'project.create'


class ProjectDelete(DeleteView):
    model = Project
    success_url = reverse_lazy('project-list')
    permission_required = 'project.delete'


# ----------------------------------------------------------------------
#
#  PARTIES
#

class PartyList(ListView):
    model = Party
    permission_required = 'party.list'


class PartyDetail(DetailView):
    model = Party
    permission_required = 'party.detail'


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
    permission_required = 'party.create'


class PartyUpdate(UpdateView):
    model = Party
    form_class = PartyForm
    template_name_suffix = '_update_form'
    permission_required = 'party.edit'


class PartyDelete(DeleteView):
    model = Party
    success_url = reverse_lazy('party-list')
    permission_required = 'party.delete'


# ----------------------------------------------------------------------
#
#  PARCELS
#

class ParcelList(ListView):
    model = Parcel
    permission_required = 'parcel.list'


class ParcelDetail(DetailView):
    model = Parcel
    permission_required = 'parcel.detail'


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
    permission_required = 'parcel.create'


class ParcelUpdate(UpdateView):
    model = Parcel
    form_class = ParcelForm
    template_name_suffix = '_update_form'
    permission_required = 'parcel.edit'


class ParcelDelete(DeleteView):
    model = Parcel
    success_url = reverse_lazy('parcel-list')
    permission_required = 'parcel.delete'


# ----------------------------------------------------------------------
#
#  STATISTICS
#

def segregate(zs):
    allres = []
    curlab = zs[0][0]
    curres = [zs[0][1]]
    for i in range(1, len(zs)):
        if zs[i][0] != curlab:
            allres.append({'label': curlab, 'actions': curres})
            curlab = zs[i][0]
            curres = [zs[i][1]]
        else:
            curres.append(zs[i][1])
    allres.append({'label': curlab, 'actions': curres})
    return allres


class StatisticsView(UserMixin, PermissionRequiredMixin, generic.TemplateView):
    template_name = 'exampleapp/statistics.html'
    permission_required = 'statistics'

    def get_context_data(self, **kwargs):
        context = super(StatisticsView, self).get_context_data(**kwargs)
        context['counts'] = {'users': User.objects.count(),
                             'policies': Policy.objects.count(),
                             'organisations': Organisation.objects.count(),
                             'projects': Project.objects.count(),
                             'parties': Party.objects.count(),
                             'parcels': Parcel.objects.count()}
        acts = sorted(list(map(str, list(Action.registered))))
        acts = zip(map(lambda a: a.split('.')[0], acts), acts)
        context['action_groups'] = segregate(list(acts))
        return context
