import json
import itertools
from django.db import models
from django.conf import settings
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
from audit_log.models.managers import AuditLog
import tutelary.engine as engine


class Policy(models.Model):
    """An individual policy has a name and a JSON policy body.  Changes to
    policies are audited.

    """

    name = models.CharField(max_length=200)

    body = models.TextField()
    """Policy body, possibly including variables."""

    audit_log = AuditLog()

    def __str__(self):
        return self.name


class PolicyInstance(models.Model):
    """An instance of a policy provides fixed values for any variables
    used in the policy's body.  An ordered sequence of policy
    instances defines a permission set.

    """

    policy = models.ForeignKey('Policy', on_delete=models.PROTECT)

    pset = models.ForeignKey('PermissionSet', on_delete=models.CASCADE)

    index = models.IntegerField()
    """Integer index used to order the sequence of policies composing a
    permission set.

    """

    variables = models.TextField()
    """JSON dump of dictionary giving variable assignments for policy
    instance.

    """

    class Meta:
        ordering = ['index']


def _policy_psets(policies):
    """Find the IDs of all permission sets making use of all of a list of
    policies.  The input is a list of (policy, variables) pairs.

    """
    if len(policies) == 0:
        # Special case: find any permission sets that don't have
        # associated policy instances.
        pipsets = set([pi.pset.id for pi in PolicyInstance.objects.all()])
        allpsets = set([pset.id for pset in PermissionSet.objects.all()])
        return list(allpsets - pipsets)
    else:
        psetids = None
        for p in policies:
            pis = PolicyInstance.objects.filter(policy=p[0])
            ppsetids = set([pi.pset.id for pi in pis])
            if psetids is None:
                psetids = ppsetids
            else:
                psetids &= ppsetids
        return [] if psetids is None else list(psetids)


class PermissionSetManager(models.Manager):
    """Permission sets have a custom manager that folds all instances
    with the same set of policy instances (as determined by the hashes
    of the policy instances) together in the database.

    """

    def by_policies(self, policies):
        # Canonicalise input policy list to include empty variable
        # assignments where necessary, and serialise variable
        # assignments to strings for policy instance lookup.
        canonpols = [(p[0], json.dumps(p[1]))
                     if isinstance(p, tuple) else (p, '{}')
                     for p in policies]

        # Try to find an existing permission set using all the same
        # policies and variable assignments.  First step is to find a
        # list of permission set IDs using all the same policies as
        # appear in the supplied policy list.
        for psetid in _policy_psets(canonpols):
            # Now, for each permission set candidate, check whether
            # the policy instance rows correspond exactly to the input
            # policy+variable assignment list.
            pset = self.get(id=psetid)
            pis = PolicyInstance.objects.filter(pset=pset)
            if len(pis) == len(canonpols):
                same = True
                for pi, canonpol in zip(pis, canonpols):
                    if pi.policy != canonpol[0] or pi.variables != canonpol[1]:
                        same = False
                        break
                if same:
                    return pset

        # If we get here, there is not an existing permission set for
        # the exact combination of policies and variable assignments
        # used here.  So we create one.

        # The permission set model stores the JSON serialisation of
        # this tree structure.

        # Make a temporary object and save it for use in building the
        # relevant PolicyInstance objects.
        obj = self.create()
        obj.save()

        # Set up policy instance references.
        for p, i in zip(canonpols, itertools.count()):
            PolicyInstance.objects.create(pset=obj, policy=p[0],
                                          index=i, variables=p[1])

        # The construction of the permission tree for this permission
        # set happens lazily when needed, so at this point we just
        # return the newly constructed object.
        return obj


class PermissionSet(models.Model):
    """A permission set represents the complete set of permissions
    resulting from the composition of a sequence of policy instances.
    The sequence of policy instances is recorded using the
    ``PolicyInstance`` model and the permission tree is constructed
    lazily from this information when the permission set is read from
    the database.

    """
    # Ordered set of policies used to generate this permission set.
    policy_assign = models.ManyToManyField(Policy, through=PolicyInstance)

    # Users to which this permission set is attached: a user has only
    # one permission set, so this is really an 1:m relation, not an
    # n:m relation.
    users = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                   related_name='permissionset')
    anonymous_user = models.BooleanField(default=False)

    # Custom manager to deal with folding together permission sets
    # generated from identical sequences of policies.
    objects = PermissionSetManager()

    def tree(self):
        if not hasattr(self, 'ptree'):
            self.ptree = engine.PermissionTree(
                policies=[engine.PolicyBody(json=pi.policy.body,
                                            variables=json.loads(pi.variables))
                          for pi in PolicyInstance.objects.filter(pset=self)]
            )
        return self.ptree


@receiver(pre_delete, sender=settings.AUTH_USER_MODEL)
def user_delete(sender, instance, **kwargs):
    """Manage policies on user deletion."""
    clear_user_policies(instance)


def clear_user_policies(user):
    """Remove all policies assigned to a user (or the anonymous user if
    ``user`` is ``None``).

    """
    if user is None:
        try:
            pset = PermissionSet.objects.get(anonymous_user=True)
            pset.anonymous_user = False
            pset.save()
        except ObjectDoesNotExist:
            return
    else:
        pset = user.permissionset.first()
    if pset:
        if user is not None:
            pset.users.remove(user)
        if pset.users.count() == 0:
            pset.delete()


def assign_user_policies(user, *policies):
    """Assign a sequence of policies to a user (or the anonymous user is
    ``user`` is ``None``).  (Also installed as ``assign_policies``
    method on ``User`` model.

    """
    clear_user_policies(user)
    pset = PermissionSet.objects.by_policies(policies)
    if user is None:
        pset.anonymous_user = True
    else:
        pset.users.add(user)
    pset.save()


def check_perms(user, actions, objs, get_allowed=None, method=None):
    for a in actions:
        for o in objs:
            test_obj = None
            if o is not None:
                test_obj = o.get_permissions_object(a)
            if not user.has_perm(a, test_obj):
                if (get_allowed is None or
                   not (a in get_allowed and method == 'GET')):
                    return False
    return True
