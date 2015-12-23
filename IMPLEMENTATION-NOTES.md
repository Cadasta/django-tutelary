## Registration of actions and object patterns

Pick up possible actions from `permissions` in model `Meta`?

`Action.register` can take object patterns, like:

```
Action.register(
  (('parcel.view', 'parcel.edit', 'parcel.delete'), 'parcel/\*/\*/\*'),
  (('parcel.list', 'parcel.create'), 'parcel/\*/\*')
)
Action.register(
  ('admin.invite-user', 'user/*'),
  ('admin.create-user', 'user')
)
Action.register(('statistics.global', ''))

```


## User model

Need to associate an ordered sequence of policy instances and the
associated permissions set with a user.  (A "policy instance" here
means a policy with any `$blah` variables instantiated with fixed
values.)

Models:
 - `Policy`: basic representation of a policy -- globally unique name,
   policy text, audit trail fields (user reference and timestamp).
 - `PolicyInstance`: policy with variables filled in -- reference to
   `Policy`, stringified JSON dictionary of variable assignments,
   policy hash.
 - `PermissionSet`: representation of composed sequence of policies
   (as stringified JSON representation of `base.PermissionSet`
   object), information about sequence of policy instances from which
   it's derived.

`PolicySequence` model?

Constraints:

 - A policy may appear in multiple policy sequences.
 - A policy sequence may be used for multiple users.
