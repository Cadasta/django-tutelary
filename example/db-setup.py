import json
from django.contrib.auth.models import User
from tutelary.models import Policy, assign_user_policies
from exampleapp.models import (
    Organisation, Project, Party, Parcel, UserPolicyAssignment
)


default_p_body = {'clause':
                  [{'effect': 'allow',
                    'action': ['party.list', 'party.detail'],
                    'object': ['party/*/*/*']},
                   {'effect': 'allow',
                    'action': ['parcel.list', 'parcel.detail'],
                    'object': ['parcel/*/*/*']},
                   {'effect': 'allow',
                    'action': ['organisation.list', 'organisation.detail'],
                    'object': ['organisation/*']},
                   {'effect': 'allow',
                    'action': ['project.list', 'project.detail'],
                    'object': ['project/*/*']},
                   {'effect': 'allow',
                    'action': ['user.list', 'user.detail'],
                    'object': ['user/*']},
                   {'effect': 'allow',
                    'action': ['policy.list', 'policy.detail'],
                    'object': ['policy/*']},
                   {'effect': 'deny',
                    'action': 'statistics'}]}
default_p = Policy(name='default', body=json.dumps(default_p_body))
default_p.save()

sysadmin_p_body = {'clause':
                   [{'effect': 'allow',
                     'action': ['party.*'],
                     'object': ['party/*/*/*']},
                    {'effect': 'allow',
                     'action': ['parcel.*'],
                     'object': ['parcel/*/*/*']},
                    {'effect': 'allow',
                     'action': ['organisation.*'],
                     'object': ['organisation/*']},
                    {'effect': 'allow',
                     'action': ['project.*'],
                     'object': ['project/*/*']},
                    {'effect': 'allow',
                     'action': ['user.*'],
                     'object': ['user/*']},
                    {'effect': 'allow',
                     'action': ['policy.*'],
                     'object': ['policy/*']},
                    {'effect': 'allow',
                     'action': 'statistics'}]}
sysadmin_p = Policy(name='sys-admin', body=json.dumps(sysadmin_p_body))
sysadmin_p.save()

org_p_body = {'clause':
              [{'effect': 'allow',
                'action': ['party.*'],
                'object': ['party/$organisation/*/*']},
               {'effect': 'allow',
                'action': ['parcel.*'],
                'object': ['parcel/$organisation/*/*']},
               {'effect': 'allow',
                'action': ['project.*'],
                'object': ['project/$organisation/*']}]}
org_p = Policy(name='org-default', body=json.dumps(org_p_body))
org_p.save()

proj_p_body = {'clause':
               [{'effect': 'deny',
                 'action': ['party.edit'],
                 'object': ['party/$organisation/$project/*']},
                {'effect': 'deny',
                 'action': ['parcel.edit'],
                 'object': ['parcel/$organisation/$project/*']},
                {'effect': 'deny',
                 'action': ['project.create',
                            'project.edit',
                            'project.delete'],
                 'object': ['project/$organisation/*']}]}
proj_p = Policy(name='project-default', body=json.dumps(proj_p_body))
proj_p.save()


org = Organisation(name='Cadasta')
org.save()
proj = Project(name='TestProj', organisation=org)
proj.save()


sysadmin = User.objects.create(username='admin')
sysadmin.assign_policies(default_p, sysadmin_p)
sysadmin.save()
ups_0 = UserPolicyAssignment.objects.create(user=sysadmin, policy=default_p,
                                            index=0)
ups_0.save()
ups_1 = UserPolicyAssignment.objects.create(user=sysadmin, policy=sysadmin_p,
                                            index=1)
ups_1.save()

user1 = User.objects.create(username='user1')
user1.assign_policies(default_p)
user1.save()
up1_0 = UserPolicyAssignment.objects.create(user=user1, policy=default_p,
                                            index=0)
up1_0.save()

user2 = User.objects.create(username='user2')
user2.assign_policies(default_p,
                      (org_p, {'organisation': 'Cadasta'}))
user2.save()
up2_0 = UserPolicyAssignment.objects.create(user=user2, policy=default_p,
                                            index=0)
up2_0.save()
up2_1 = UserPolicyAssignment.objects.create(user=user2, policy=org_p,
                                            organisation=org,
                                            index=1)
up2_1.save()

user3 = User.objects.create(username='user3')
user3.save()
user3.assign_policies(default_p,
                      (org_p, {'organisation': 'Cadasta'}),
                      (proj_p, {'organisation': 'Cadasta',
                                'project': 'TestProj'}))
up3_0 = UserPolicyAssignment.objects.create(user=user3, policy=default_p,
                                            index=0)
up3_0.save()
up3_1 = UserPolicyAssignment.objects.create(user=user3, policy=org_p,
                                            organisation=org,
                                            index=1)
up3_1.save()
up3_2 = UserPolicyAssignment.objects.create(user=user3, policy=proj_p,
                                            organisation=org, project=proj,
                                            index=2)
up3_2.save()


assign_user_policies(None, default_p)


party1 = Party(project=proj, name='Jim Jones')
party1.save()
party2 = Party(project=proj, name='Sally Smith')
party2.save()
party3 = Party(project=proj, name='Bob Bennett')
party3.save()

parcel1 = Parcel(project=proj, address='1 Beach Terrace')
parcel1.save()
parcel2 = Parcel(project=proj, address='5 Sandy Road')
parcel2.save()
parcel3 = Parcel(project=proj, address='10 Chorley Street')
parcel3.save()
