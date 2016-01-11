from django import forms
from django.contrib.auth.models import User
from tutelary.models import Policy
from .models import Organisation, Project


def user_choices():
    yield (None, '--------')
    for u in User.objects.all():
        yield (u.username, u.username)


class UserSwitchForm(forms.Form):
    username = forms.ChoiceField(label='Select user',
                                 choices=user_choices)


class UserPolicyForm(forms.Form):
    MAX_POLICIES = 8

    policy = forms.ModelChoiceField(queryset=Policy.objects.all(),
                                    required=False)
    organisation = forms.ModelChoiceField(
        queryset=Organisation.objects.all(), empty_label='*', required=False
    )
    project = forms.ModelChoiceField(
        queryset=Project.objects.all(), empty_label='*', required=False
    )


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username',)
