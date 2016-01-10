from django import forms
from django.contrib.auth.models import User


def user_choices():
    yield (None, '--------')
    for u in User.objects.all():
        yield (u.username, u.username)


class UserSwitchForm(forms.Form):
    username = forms.ChoiceField(label='Select user',
                                 choices=user_choices)
