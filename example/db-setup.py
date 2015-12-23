import json
from tutelary.models import Policy, PolicyInstance, PermissionSet


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


vars = {'organisation': 'Cadasta', 'project': 'TestProj'}

default_pi = PolicyInstance.objects.get_hashed(default_p, vars)
default_pi.save()
org_pi = PolicyInstance.objects.get_hashed(org_p, vars)
org_pi.save()
proj_pi = PolicyInstance.objects.get_hashed(proj_p, vars)
proj_pi.save()

pset_policies = [default_p, org_p, proj_p]
pset = PermissionSet.objects.make(policies=pset_policies, vars=vars)
