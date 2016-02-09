import json
import itertools
from django.contrib.auth.models import User
from tutelary.models import Policy, assign_user_policies
from exampleapp.models import (
    Organisation, Project, Party, Parcel, UserPolicyAssignment
)


default_p_body = {
    'clause': [
        {'effect': 'allow',
         'action': ['party.list'],
         'object': ['project/*/*']},
        {'effect': 'allow',
         'action': ['party.detail'],
         'object': ['party/*/*/*']},

        {'effect': 'allow',
         'action': ['parcel.list'],
         'object': ['project/*/*']},
        {'effect': 'allow',
         'action': ['parcel.detail'],
         'object': ['parcel/*/*/*']},

        {'effect': 'allow',
         'action': ['organisation.list']},
        {'effect': 'allow',
         'action': ['organisation.detail'],
         'object': ['organisation/*']},

        {'effect': 'allow',
         'action': ['project.list'],
         'object': ['organisation/*']},
        {'effect': 'allow',
         'action': ['project.detail'],
         'object': ['project/*/*']},

        {'effect': 'allow',
         'action': ['user.list']},
        {'effect': 'allow',
         'action': ['user.detail'],
         'object': ['user/*']},

        {'effect': 'allow',
         'action': ['policy.list']},
        {'effect': 'allow',
         'action': ['policy.detail'],
         'object': ['policy/*']},

        {'effect': 'deny',
         'action': 'statistics'}
    ]
}
default_p = Policy(name='default', body=json.dumps(default_p_body))
default_p.save()

sysadmin_p_body = {
    'clause': [
        {'effect': 'allow',
         'action': ['party.detail', 'party.edit', 'party.delete'],
         'object': ['party/*/*/*']},
        {'effect': 'allow',
         'action': ['party.list', 'party.create'],
         'object': ['project/*/*']},

        {'effect': 'allow',
         'action': ['parcel.detail', 'parcel.edit', 'parcel.delete'],
         'object': ['parcel/*/*/*']},
        {'effect': 'allow',
         'action': ['parcel.list', 'parcel.create'],
         'object': ['project/*/*']},

        {'effect': 'allow',
         'action': ['organisation.delete'],
         'object': ['organisation/*']},
        {'effect': 'allow',
         'action': ['organisation.list', 'organisation.create']},

        {'effect': 'allow',
         'action': ['project.delete'],
         'object': ['project/*/*']},
        {'effect': 'allow',
         'action': ['project.list', 'project.create'],
         'object': ['organisation/*']},

        {'effect': 'allow',
         'action': ['user.detail', 'user.edit', 'user.delete'],
         'object': ['user/*']},
        {'effect': 'allow',
         'action': ['user.list', 'user.create']},

        {'effect': 'allow',
         'action': ['policy.detail', 'policy.edit', 'policy.delete'],
         'object': ['policy/*']},
        {'effect': 'allow',
         'action': ['policy.list', 'policy.create']},

        {'effect': 'allow',
         'action': 'statistics'}
    ]
}
sysadmin_p = Policy(name='sys-admin', body=json.dumps(sysadmin_p_body))
sysadmin_p.save()

org_p_body = {
    'clause': [
        {'effect': 'allow',
         'action': ['party.detail', 'party.edit', 'party.delete'],
         'object': ['party/$organisation/*/*']},
        {'effect': 'allow',
         'action': ['party.list', 'party.create'],
         'object': ['project/$organisation/*']},

        {'effect': 'allow',
         'action': ['parcel.detail', 'parcel.edit', 'parcel.delete'],
         'object': ['parcel/$organisation/*/*']},
        {'effect': 'allow',
         'action': ['parcel.list', 'parcel.create'],
         'object': ['project/$organisation/*']},

        {'effect': 'allow',
         'action': ['project.delete'],
         'object': ['project/$organisation/*']},
        {'effect': 'allow',
         'action': ['project.list', 'project.create'],
         'object': ['organisation/$organisation']}
    ]
}
org_p = Policy(name='org-default', body=json.dumps(org_p_body))
org_p.save()

proj_p_body = {
    'clause': [
        {'effect': 'deny',
         'action': ['party.edit'],
         'object': ['party/$organisation/$project/*']},
        {'effect': 'deny',
         'action': ['parcel.edit'],
         'object': ['parcel/$organisation/$project/*']},
        {'effect': 'deny',
         'action': ['project.edit', 'project.delete'],
         'object': ['project/$organisation/*']},
        {'effect': 'deny',
         'action': ['project.create'],
         'object': ['organisation/$organisation']}
    ]
}
proj_p = Policy(name='project-default', body=json.dumps(proj_p_body))
proj_p.save()


org1 = Organisation(name='Cadasta')
org1.save()
org2 = Organisation(name='H4HI')
org2.save()

proj1 = Project(name='CadastaProj1', organisation=org1)
proj1.save()
proj2 = Project(name='CadastaProj2', organisation=org1)
proj2.save()
proj3 = Project(name='H4HIProj', organisation=org2)
proj3.save()


users = [('admin', [default_p,
                    sysadmin_p],
          None, None),
         ('user1', [default_p],
          None, None),
         ('user2', [default_p,
                    (org_p, {'organisation': 'Cadasta'})],
          org1, None),
         ('user3', [default_p,
                    (org_p, {'organisation': 'Cadasta'}),
                    (proj_p, {'organisation': 'Cadasta',
                              'project': 'CadastaProj1'})],
          org1, proj1)]

for uname, pols, org, proj in users:
    u = User.objects.create(username=uname)
    u.assign_policies(*pols)
    u.save()
    for p, i in zip(pols, itertools.count()):
        if isinstance(p, tuple):
            p = p[0]
        ups = UserPolicyAssignment.objects.create(user=u, policy=p,
                                                  organisation=org,
                                                  project=proj, index=i)
        ups.save()


assign_user_policies(None, default_p)


parties = [(proj1, 'Jim Jones'),
           (proj1, 'Sally Smith'),
           (proj1, 'Bob Bennett'),
           (proj2, 'Dave Dawkins'),
           (proj2, 'Alex Adams'),
           (proj3, 'Charlie Chapo')]
for p, n in parties:
    party = Party(project=p, name=n)
    party.save()

parcels = [(proj1, '1 Beach Terrace'),
           (proj1, '5 Sandy Road'),
           (proj2, '10 Chorley Street'),
           (proj2, '7 Sidney Avenue'),
           (proj3, 'Lanser Strasse 30'),
           (proj3, 'Obexerstrasse 15')]
for p, a in parcels:
    parcel = Parcel(project=p, address=a)
    parcel.save()
