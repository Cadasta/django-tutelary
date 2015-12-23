import json
from django.db import models
from audit_log.models.managers import AuditLog
import tutelary.base as base


class Policy(models.Model):
    """
    An individual policy has a name and a JSON policy body.  Changes
    to policies are audited.

    """
    name = models.CharField(max_length=200)
    body = models.TextField()
    audit_log = AuditLog()


class PolicyInstanceManager(models.Manager):
    """
    Policy instances have a custom manager that folds all instances
    with the same hash together in the database.

    """
    def get_hashed(self, policy, vars=None):
        pol = base.Policy(json=policy.body, vars=vars)
        existing = self.filter(hash=pol.hash())
        if existing:
            return existing[0]
        else:
            return self.create(policy=policy,
                               policy_text=str(pol),
                               variables=json.dumps(vars),
                               hash=pol.hash())


class PolicyInstance(models.Model):
    """
    An instance of a policy provides fixed values for any variables
    used in the policy's body.  A hash is calculated from the
    resulting policy body instance for quick comparisons.

    """
    policy = models.ForeignKey(Policy, null=True)
    policy_text = models.TextField()
    variables = models.TextField()
    hash = models.CharField(max_length=64)

    objects = PolicyInstanceManager()


class PermissionSetManager(models.Manager):
    def get_hashed(self, policies, vars=None):
        def make_pa(p, i):
            return PolicyInstanceAssign(
                policy_instance=PolicyInstance.objects.get_hashed(p, vars),
                permission_set=self,
                index=i)

        def make_pol(p):
            return base.Policy(json=p.body, vars=vars)

        pas = map(make_pa, policies, range(len(policies)))
        pols = map(make_pol, policies)
        pset = base.PermissionSet(policies=pols, vars=vars)
        obj = self.create(data=repr(pset))
        map(lambda pa: obj.policy_assign.add(pa), pas)
        ####  STOPPED HERE!!!
        return obj


class PermissionSet(models.Model):
    """
    A permission set represents the complete set of permissions
    resulting from the composition of a sequence of policy instances.
    The permission set itself is represented as the JSON serialisation
    of a ``base.PermissionSet`` object, and the sequence of policy
    instances is recorded using the ``PolicyInstanceAssign`` model.

    """
    data = models.TextField()
    policy_assign = models.ManyToManyField(PolicyInstance,
                                           through='PolicyInstanceAssign')

    objects = PermissionSetManager()

    def policy_instances(self):
        pis = self.policy_assign.all()
        return pis


class PolicyInstanceAssign(models.Model):
    """
    Record the sequence of policy instances used to compose a
    permission set.

    """
    policy_instance = models.ForeignKey(PolicyInstance)
    permission_set = models.ForeignKey(PermissionSet)
    index = models.IntegerField()

    class Meta:
        ordering = ('index',)
