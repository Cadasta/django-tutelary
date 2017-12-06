import json
import re
from django.db import models
from django.conf import settings
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from audit_log.models.managers import AuditLog
import tutelary.engine as engine
from tutelary.exceptions import RoleVariableException


class Policy(models.Model):
    """An individual policy has a name and a JSON policy body.  Changes to
    policies are audited.

    """

    name = models.CharField(max_length=200)
    """Policy name field."""

    body = models.TextField()
    """Policy JSON body."""

    audit_log = AuditLog()

    def __str__(self):
        return self.name

    def variable_names(self):
        pat = re.compile(r'\$(?:([_a-z][_a-z0-9]*)|{([_a-z][_a-z0-9]*)})')
        return set([m[0] for m in re.findall(pat, self.body)])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.refresh()

    def refresh(self):
        for pset in _policy_psets([self]):
            pset.refresh()


class RolePolicyAssign(models.Model):
    """A role is defined by an ordered sequence of policies.

    """

    policy = models.ForeignKey('Policy', on_delete=models.PROTECT)

    role = models.ForeignKey('Role', on_delete=models.CASCADE)

    index = models.IntegerField()
    """Integer index used to order the sequence of policies composing a
    role.

    """

    class Meta:
        ordering = ['index']

    def __str__(self):
        return "role={} policy={}".format(self.role.name, self.policy.name)


class RoleManager(models.Manager):
    """Custom manager for roles: ensures that role variable assignments
    cover all the variables used in the role's policies.

    """
    def create(self, name, policies=None, variables=None):
        policies = policies or []
        variables = variables or {}
        role = super().create(name=name, variables=variables)
        variable_names = set().union(*[p.variable_names() for p in policies])
        if not variable_names.issubset(variables.keys()):
            raise RoleVariableException("missing variable in role definition")
        for i, policy in enumerate(policies):
            RolePolicyAssign.objects.create(role=role, policy=policy, index=i)
        return role


class Role(models.Model):
    """A policy role has a name, a sequence of policies and a set of
    variable assignments.  Changes to roles are audited.

    """

    name = models.CharField(max_length=200)
    """Role name field."""

    policies = models.ManyToManyField(Policy, through=RolePolicyAssign)

    variables = models.TextField()
    """JSON dump of dictionary giving variable assignments for role.

    """

    audit_log = AuditLog()

    objects = RoleManager()

    def __str__(self):
        return self.name

    def variable_names(self):
        return set().union(*[p.variable_names() for p in self.policies.all()])

    def delete(self, *args, **kwargs):
        RolePolicyAssign.objects.filter(role=self).delete()
        super().delete(*args, **kwargs)


class PolicyInstance(models.Model):
    """An instance of a policy provides fixed values for any variables
    used in the policy's body.  An ordered sequence of policy
    instances defines a permission set.

    """

    policy = models.ForeignKey(Policy, on_delete=models.PROTECT)

    pset = models.ForeignKey('PermissionSet', on_delete=models.CASCADE)

    index = models.IntegerField()
    """Integer index used to order the sequence of policies composing a
    permission set.

    """

    role = models.ForeignKey(Role, null=True, on_delete=models.PROTECT)
    """The role that this policy instance is associated with, if any."""

    variables = models.TextField()
    """JSON dump of dictionary giving variable assignments for policy
    instance.

    """

    class Meta:
        ordering = ['index']

    def __str__(self):
        return "policy={} pset={} index={} role={} variables={}".format(
            self.policy.name, self.pset.pk, self.index,
            self.role.name if self.role else "NULL",
            self.variables
        )


def _policy_psets(policy_instances):
    """Find all permission sets making use of all of a list of policy_instances.
    The input is an array of policy instances.

    """
    if len(policy_instances) == 0:
        # Special case: find any permission sets that don't have
        # associated policy instances.
        return PermissionSet.objects.filter(policyinstance__isnull=True)
    else:
        return PermissionSet.objects.filter(
            policyinstance__policy__in=policy_instances).distinct()


class PermissionSetManager(models.Manager):
    """Permission sets have a custom manager that folds all instances with
    the same set of policy instances together in the database.

    """

    def by_policies_and_roles(self, policies_roles):
        # Canonicalise input policy list to include empty variable
        # assignments where necessary, serialise variable assignments
        # to strings for policy instance lookup, and expand roles to
        # their corresponding lists of policies.
        canonpols = []
        for pr in policies_roles:
            vars = '{}'
            if isinstance(pr, tuple):
                vars = json.dumps(pr[1])
                pr = pr[0]
            if isinstance(pr, Role):
                vars = json.dumps(pr.variables)
                policy_assignments = RolePolicyAssign.objects.filter(
                    role=pr).select_related('policy')
                for rp in policy_assignments:
                    canonpols.append((rp.policy, vars, pr))
            else:
                canonpols.append((pr, vars, None))

        # Try to find an existing permission set using all the same
        # policies and variable assignments.
        policies = [policy for (policy, variables, role) in canonpols]
        matching_psets = _policy_psets(policies).annotate(
            num_pis=models.Count('policyinstance')
        ).filter(
            # Same number of policy instances
            num_pis=len(canonpols)
        )

        for policy, variables, role in canonpols:
            # Now, for each permission set candidate, check whether
            # the policy instance rows correspond exactly to the input
            # policy+variable assignment list.
            matching_psets = matching_psets.filter(
                policyinstance__policy=policy,
                policyinstance__variables=variables,
                policyinstance__role=role,
            )
        matched_pset = matching_psets.first()
        if matched_pset:
            return matched_pset

        # If we get here, there is not an existing permission set for
        # the exact combination of policies and variable assignments
        # used here.  So we create one.

        # The permission set model stores the JSON serialisation of
        # this tree structure.

        # Create a PermissionSet for use in building the relevant
        # PolicyInstance objects.
        obj = self.create()

        # Set up policy instance references.
        PolicyInstance.objects.bulk_create([
            PolicyInstance(
                pset=obj, policy=policy, role=role,
                index=i, variables=variables
            ) for i, (policy, variables, role) in enumerate(canonpols)
        ])

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

    def cache_key(self):
        return 'tutelary:ptree:' + str(self.pk)

    def tree(self):
        key = self.cache_key()
        cached = cache.get(key)
        if cached is None:
            ptree = engine.PermissionTree(
                policies=[engine.PolicyBody(json=pi.policy.body,
                                            variables=json.loads(pi.variables))
                          for pi in (PolicyInstance.objects
                                     .select_related('policy')
                                     .filter(pset=self))]
            )
            cache.set(key, ptree)
            cached = ptree
        return cached

    def refresh(self):
        cache.set(self.cache_key(), None)

    def __str__(self):
        return str(self.pk)


@receiver(pre_delete, sender=settings.AUTH_USER_MODEL)
def user_delete(sender, instance, **kwargs):
    """Manage policies on user deletion."""
    clear_user_policies(instance)


CACHED_PSET_PROPERTY_KEY = '__pset_tree'


def _get_permission_set_tree(user):
    """
    Helper to return cached permission set tree from user instance if set, else
    generates and returns analyzed permission set tree. Does not cache set
    automatically, that must be done explicitely.
    """
    if hasattr(user, CACHED_PSET_PROPERTY_KEY):
        return getattr(user, CACHED_PSET_PROPERTY_KEY)
    if user.is_authenticated():
        try:
            return user.permissionset.first().tree()
        except AttributeError:
            raise ObjectDoesNotExist
    return PermissionSet.objects.get(anonymous_user=True).tree()


def _del_permission_set_tree(user):
    """ Helper to clear permission set tree cached on user instance """
    if hasattr(user, CACHED_PSET_PROPERTY_KEY):
        delattr(user, CACHED_PSET_PROPERTY_KEY)


permission_set_tree_property = property(
    fget=_get_permission_set_tree,
    fset=None,
    fdel=_del_permission_set_tree,
    doc="Helper to cache Tutelary's permission_set tree on user instance"
)


def ensure_permission_set_tree_cached(user):
    """ Helper to cache permission set tree on user instance """
    if hasattr(user, CACHED_PSET_PROPERTY_KEY):
        return
    try:
        setattr(
            user, CACHED_PSET_PROPERTY_KEY, _get_permission_set_tree(user))
    except ObjectDoesNotExist:  # No permission set
        pass


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
        pset.refresh()
        if user is not None:
            pset.users.remove(user)
        if pset.users.count() == 0 and not pset.anonymous_user:
            pset.delete()


def user_cache_key(user):
    return 'tutelary:user:' + str(user.pk) if user is not None else 'anon'


def assign_user_policies(user, *policies_roles):
    """Assign a sequence of policies to a user (or the anonymous user is
    ``user`` is ``None``).  (Also installed as ``assign_policies``
    method on ``User`` model.

    """
    clear_user_policies(user)
    pset = PermissionSet.objects.by_policies_and_roles(policies_roles)
    pset.refresh()
    if user is None:
        pset.anonymous_user = True
    else:
        pset.users.add(user)
    pset.save()
    cache.set(user_cache_key(user), None)


def user_assigned_policies(user):
    """Return sequence of policies assigned to a user (or the anonymous
    user is ``user`` is ``None``).  (Also installed as
    ``assigned_policies`` method on ``User`` model.

    """
    key = user_cache_key(user)
    cached = cache.get(key)
    if cached is not None:
        return cached

    if user is None:
        pset = PermissionSet.objects.filter(anonymous_user=True).first()
    else:
        pset = user.permissionset.first()
    if pset is None:
        return []

    res = []
    skip_role_policies = False
    skip_role = None
    skip_role_variables = None
    for pi in pset.policyinstance_set.select_related('policy', 'role'):
        if skip_role_policies:
            if pi.role == skip_role and pi.variables == skip_role_variables:
                continue
            else:
                skip_role_policies = False
        if pi.role:
            res.append(pi.role)
            skip_role = pi.role
            skip_role_variables = pi.variables
            skip_role_policies = True
        else:
            if pi.variables != '{}':
                res.append((pi.policy, json.loads(pi.variables)))
            else:
                res.append(pi.policy)
    cache.set(key, res)
    return res


def check_perms(user, actions, objs, method=None):
    ensure_permission_set_tree_cached(user)
    if actions is False:
        return False
    if actions is not None:
        for a in actions:
            for o in objs:
                test_obj = None
                if o is not None:
                    test_obj = o.get_permissions_object(a)
                if not user.has_perm(a, test_obj):
                    return False
    return True
