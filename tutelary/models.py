import json
import hashlib
import itertools
from django.db import models
from django.conf import settings
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

    def __str__(self):
        return self.name


class PolicyInstanceManager(models.Manager):
    """
    Policy instances have a custom manager that folds all instances
    with the same hash together in the database.

    """
    def get_hashed(self, policy, variables=None):
        pol = base.Policy(json=policy.body, variables=variables)
        existing = self.filter(hash=pol.hash())
        if existing:
            return existing[0]
        else:
            return self.create(policy=policy,
                               policy_text=str(pol),
                               variables=json.dumps(variables),
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

    # Hash field and custom manager to deal with folding together
    # permission sets generated from identical sequences of policies.
    hash = models.CharField(max_length=64)
    objects = PolicyInstanceManager()


class PolicyInstanceAssign(models.Model):
    """
    Record the sequence of policy instances used to compose a
    permission set.

    """
    policy_instance = models.ForeignKey('PolicyInstance',
                                        on_delete=models.CASCADE)
    permission_set = models.ForeignKey('PermissionSet',
                                       on_delete=models.CASCADE)
    index = models.IntegerField()

    class Meta:
        ordering = ['index']


class PermissionSetManager(models.Manager):
    def get_hashed(self, policies):
        def make_pi(p):
            if isinstance(p, tuple):
                return PolicyInstance.objects.get_hashed(p[0], p[1])
            else:
                return PolicyInstance.objects.get_hashed(p)

        def make_pol(p):
            if isinstance(p, tuple):
                return base.Policy(json=p[0].body, variables=p[1])
            else:
                return base.Policy(json=p[0].body)

        # Make policy instances for each of the sequence of policies
        # on which this permission set is based, and extract their
        # hashes.
        pis = list(map(make_pi, policies))
        pi_hashes = list(map(lambda pi: pi.hash, pis))

        # Make a "big hash" of all the hashes from the individual
        # policy assignment hashes in the order that they're used.
        # This is used to identify the permission set in the database
        # for quick access.
        pset_hash = hashlib.md5(':'.join(pi_hashes).encode()).hexdigest()

        # Look up by hash.
        existing = self.filter(hash=pset_hash)
        if existing:
            return existing[0]
        else:
            # Make a new base permission set object: this merges the
            # policy instances into a wild card tree for fast lookup.
            pset = base.PermissionSet(policies=list(map(make_pol, policies)))

            # The permission set model stores the JSON serialisation
            # of this tree structure.
            obj = self.create(data=repr(pset), hash=pset_hash)
            obj.save()

            # Record the policy instance assigments.
            for pi, i in zip(pis, itertools.count()):
                pa = PolicyInstanceAssign(policy_instance=pi,
                                          permission_set=obj,
                                          index=i)
                pa.save()

            return obj


class PermissionSet(models.Model):
    """
    A permission set represents the complete set of permissions
    resulting from the composition of a sequence of policy instances.
    The permission set itself is represented as the JSON serialisation
    of a ``base.PermissionSet`` object, and the sequence of policy
    instances is recorded using the ``PolicyInstanceAssign`` model.

    """
    # JSON serialisation of wildcard tree representation of permission
    # set.
    data = models.TextField()

    # Ordered set of policies used to generate this permission set.
    policy_assign = models.ManyToManyField(PolicyInstance,
                                           through=PolicyInstanceAssign)

    # Users to which this permission set is attached: a user has only
    # one permission set, so this is really an 1:m relation, not an
    # n:m relation.
    users = models.ManyToManyField(settings.AUTH_USER_MODEL)

    # Hash field and custom manager to deal with folding together
    # permission sets generated from identical sequences of policies.
    hash = models.CharField(max_length=64)
    objects = PermissionSetManager()

    def policy_instances(self):
        pis = self.policy_assign.all()
        return pis


def assign_user_policies(user, *policies):
    pset = PermissionSet.objects.get_hashed(policies)
    pset.user.add(user)
