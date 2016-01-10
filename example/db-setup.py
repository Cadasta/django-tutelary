import json
from django.contrib.auth.models import User
from tutelary.models import Policy, PolicyInstance, PermissionSet
from exampleapp.models import Organisation, Project, Party, Parcel


user1 = User.objects.create(username='user1')
user1.save()
user2 = User.objects.create(username='user2')
user2.save()
user3 = User.objects.create(username='user3')
user3.save()


default_p_body = {'clause': []}
default_p = Policy(name='default', body=json.dumps(default_p_body))
default_p.save()

org_p_body = {'clause':
              [{'effect': 'allow',
                'action': ['party.*'],
                'object': ['party/$organisation/*/*']},
               {'effect': 'allow',
                'action': ['parcel.*'],
                'object': ['parcel/$organisation/*/*']}]}
org_p = Policy(name='org-default', body=json.dumps(org_p_body))
org_p.save()

proj_p_body = {'clause':
               [{'effect': 'deny',
                 'action': ['party.edit'],
                 'object': ['party/$organisation/$project/*']},
                {'effect': 'deny',
                 'action': ['parcel.edit'],
                 'object': ['parcel/$organisation/$project/*']}]}
proj_p = Policy(name='project-default', body=json.dumps(proj_p_body))
proj_p.save()


vs = {'organisation': 'Cadasta', 'project': 'TestProj'}

default_pi = PolicyInstance.objects.get_hashed(default_p, vs)
default_pi.save()
org_pi = PolicyInstance.objects.get_hashed(org_p, vs)
org_pi.save()
proj_pi = PolicyInstance.objects.get_hashed(proj_p, vs)
proj_pi.save()


pset1 = PermissionSet.objects.get_hashed(policies=[default_p],
                                         variables=vs)
pset1.users.add(user1)
pset1.save()

pset2 = PermissionSet.objects.get_hashed(policies=[default_p, org_p],
                                         variables=vs)
pset2.users.add(user2)
pset2.save()

pset3 = PermissionSet.objects.get_hashed(policies=[default_p, org_p, proj_p],
                                         variables=vs)
pset3.users.add(user3)
pset3.save()


org = Organisation(name='Cadasta')
org.save()
proj = Project(name='TestProj', organisation=org)
proj.save()

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
