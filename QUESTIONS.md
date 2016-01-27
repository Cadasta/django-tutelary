* What about making the `name` field in `tutelary.models.Policy` the
  primary key?

* Permissions objects for collective actions.

* Support function views.

* Caching:
   - The JSON body of the relevant policy is interpreted every time
     `PolicyInstanceManager.get_hashed` is called.  The result of the
     JSON parsing (which is a `tutelary.base.Policy` object) should be
     cached on the `tutelary.models.Policy` model instance.  (It's
     actually a tiny bit trickier than that because the `base.Policy`
     object instantiates all the policy variables.  If the policy name
     was the primary key, we could have a dictionary here keyed on the
     policy name and a canonical representation of the variable
     values.)
   - In `PolicyInstanceManager.get_hashed`, we could use an LRU cache
     for policy instance lookups (based on the policy instance hash).
   - In `PermissionSet.get_hashed`, we could use an LRU cache for
     permission set lookups (based on the composite hash built from
     the hashes of the policy instances used to build the permission
     set).
   - As long as the above issues are dealt with, the only remaining
     cacheable queries are those associating users and permission
     sets: this is just a many-to-many field linking users to
     permission sets.  I don't know if there's an easy way to force
     more extensive caching for queries for that.
