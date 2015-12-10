# Introduction

A careful reading of the Cadasta user stories and original functional
requirements seems to indicate that the idea of "user roles" as fixed
concepts in the permissions system is something of a red herring.  The
permissioning system envisaged in the functional requirements appears
to encompass both stereotyped user roles and the possibility to
control permissions at a fine-grained level, i.e. at the level of
individual users and platform entities (parties, parcels,
relationships and resources).  This indicates that we need a
permissioning system with the following characteristics:

 * It should be possible to make statements about permissions for
   individual actions or classes of actions at the level of individual
   users and individual entities.
 * It should be possible to collect user- and entity-level permissions
   statements into policies describing sets of permissions that should
   be assigned to users or classes of users.

The type of system I think we need here is has some characteristics in
common with what is normally called role-based access control (RBAC),
but is closer to the policy-based approach used by Amazon Web
Services.  By using an approach like this, we will be able to
accommodate both stereotyped user roles and future requirements for
changing the exact definitions of roles, or supporting variances to
permissions for individual users, projects, organisations and so on.

Let's look at how this could work.  (I had originally hoped to use an
existing RBAC system like `django-rbac`, but that’s not a very good
fit for our needs and hasn't been maintained for a long time, and
unfortunately there doesn’t appear to be an existing Python
implementation of this type of policy-based access control.)  This is
a bit formal, but it’s clearest this way.  If it sounds complicated,
that’s just because I’m trying to describe things explicitly enough to
avoid confusion.  The implementation shouldn’t be very complicated.

The basic requirement is that it be possible to determine whether a
given **user** is permitted to perform some **action** on some
**object**, according to a set of **permissions policies**.  We need
to define what these entities are and how we represent them, and we
need to define how policies are defined, how policies are associated
with users and how policies are composed to produce a set of
permissions.


# Policy system entities

## Users

"Agents", "subjects", i.e. entities that want to perform *actions*.
Should just be the usual Django abstraction of a "user".

Require:

 * A means of identifying a user &ndash; just pass a Django `User`
   object.

## Objects and object patterns

An *object* is a label identifying an individual entity on which
*actions* may be performed.  For example, in the Cadasta context,
labelling as `organisation/project/type/entity-id`, we might have
`H4H/Haiti-PortAuPrince/parcel/1412`,
`AsiaFoundation/Batangas/party/472`, etc.  In other contexts, objects
might correspond to files and directories or network entities.

An *object-pattern* is a way of identifying sets of objects: for the
moment, think of this as either an individual object or an object
where elements of the object can be replaced by a single-element
wildcard "`*`" (for example, `H4H/*/parcel/*` refers to all parcels in
all projects for organisation `H4H`, `AsiaFoundation/Batangas/*/*`
refers to all entities in the `Batangas` project in the
`AsiaFoundation` organisation) or a multi-element wildcard "`**`" (for
example, `H4H/**` refers to all entities within the `H4H`
organisation).  (More complex functionality for selecting sets of
entities based on their characteristics can be introduced without much
trouble, e.g. all tenure relationships of a particular type, all
parcels within a given region, etc.)

Require:

 * A means of identifying individual *objects*.
 * A means of identifying groups of *objects* by *object-patterns*.
 * A means of determining whether a given *object* is a member of a
   group of *objects* as specified by an *object-pattern*.
 * An efficient means of representing set algebra operations (union,
   intersection, difference) on groups of *objects* and
   *object-patterns*.
 * Abstraction over the representation of *objects* and
   *object-patterns*, so that it's possible to plug in different
   approaches to representing these entities.

## Actions and action patterns

An *action* is a label referring to a single operation that can be
performed on an *object*.  In the Cadasta context, these might be
things like `Parcel.create`, `Parcel.edit_geometry`,
`Party.view_details`, `Organization.manage_users`,
`Admin.invite_user`, `Project.archive`, etc.  In a file management
context, things like `Copy`, `Delete`, `Move`, `Size`, `ViewContents`,
and so on.

An *action-pattern* is a way of identifying sets of actions: an
*action-pattern* is either an individual action or an action with some
elements replaced with a single-element wildcard "`*`" (for example,
`Parcel.*` refers to all actions on parcels, `Admin.*` refers to all
administrative actions, `*.archive` refers to all actions archiving
entities, and so on) or a multi-element wildcard "`**`" (for example,
`**` refers to all possible actions).

Require:

 * A means of identifying individual *actions*.
 * A means of identifying groups of *actions* by *action-patterns*.
 * A means of determining whether a given *action* is a member of a
   group of *actions* as specified by an *action-pattern*.
 * An efficient means of representing set algebra operations (union,
   intersection, difference) on groups of *actions* and
   *action-patterns*.
 * Abstraction over the representation of *actions* and
   *action-patterns*, so that it's possible to plug in different
   approaches to representing these entities.


# Policy grammar

We can define a grammar of JSON structures representing policies like
this:

```
policy  = {
  <version_block?>
  <clause_block>
}

<version_block> = "version" : "2015-12-10"

<clause_block> = "clause" : [ <clause>, <clause>, ... ]

<clause> = {
  <effect_block>,
  <action_block>,
  <object_block>
} | {
  <include_block>
}

<effect_block> = "effect" : ("allow" | "deny")

<action_block> = ("action" | "not_action") :
    ("*" | [<action_string>, <action_string>, ...])

<object_block> = ("object" | "not_object") :
    ("*" | [<object_string>, <object_string>, ...])

<include_block> = "include" : <policy_name>
```

An `<action_string>` is a sequence of words (alphanumeric +
underscore) separated by periods, e.g. `Parcel.create`,
`Admin.invite_user`.  Any of the period-separated elements may be
replaced by a "`*`" wildcard, e.g. `Admin.*`, `*.create`.

An `<object_string>` is a sequence of identifiers (any character
except `/` or `*`) separated by slashes,
e.g. `H4H/PortAuPrince/parce/412`.  Any of the slash-separated
elements may be replaced by a "`*`" wildcard,
e.g. `AsiaFoundation/Batangas/Party/*`.


Here, a policy can be assigned a policy-name for later reference in a
`<include_block>`.

What this means is that a policy collects together a sequence of
clauses defining actions that are allowed or denied for particular
classes of entities, with the possibility of naming a policy and
including it in another policy.

Here’s an example to make this a little clearer.  The following policy

```
{
  "clause": [
  { "effect": "allow",
    "action": [ "*.view", "*.edit" ],
    "object": [ "Cadasta/*/*/*" ] },
  { "effect": "deny",
    "action": [ "*.edit" ],
    "object": [ "Cadasta/Batangas/parcel/*",
                "Cadasta/Batangas/relationship/*" ] }
  ]
}
```

allows viewing of all entities belonging to the `Cadasta` organisation
and editing of all entities belong to the `Cadasta` organisation
except for all parcels and all relationships in the `Batangas`
project.


# Policy evaluation logic

## Basics

The permissions that individual users have within the platform are
determined by the set of policies assigned to them: the clauses in all
of the policies assigned to a user are applied cumulatively to arrive
at an effective permissions set.  The policies used to determine the
effective permissions set for a user are:

1. *Empty policy*: by default, no actions are possible; all actions
   must be explicitly allowed by a policy.
2. *Platform default policy*: this determines the default permissions
   for all organisations and projects that do not assign any specific
   policies.
3. *Organisation policy*: allows an organisation to set default
   policies for all their projects.
4. *Project policy*: allows an organisation to set default policies
   for individual projects.
5. *User-level named policies*: this is the level at which the idea of
   a "role" makes most sense; an administrator could define a "project
   manager policy" that could be assigned to users to give them the
   permissions needed to perform project management actions, a "data
   collector policy" to be assigned to users to allow them to perform
   data collection actions, and so on; this is also the level at which
   "exception" policies can be set up for unusual cases (a project
   where certain classes of relationship information should only be
   visible to a subset of users, for instance?).
6. *User-level ad hoc policies*: if additional permissions or
   restrictions need to be applied to individual users and/or
   entities, this can be done by assigning additional ad hoc policies
   to a user.

The effective permissions for a user are determined by cumulatively
applying the clauses in each of these policies to produce the overall
effective permissions set.  This sounds like a heavyweight operation,
but it’s really not.  Effective permissions sets can be cached and
only need to be recalculated when policies are changed, which is a
relatively infrequent operation.  Additionally, the set of all
sequences of policies in force at any time form a tree, and
modifications at any level in the list above only affect effective
permissions sets in the policy sequence subtree rooted at the policy
being modified.

## Policy composition

The composition of policies works as follows:

 * We denote the composition of two policy effects by *a* &#x25C2;
   *b*.  (The symbology here is supposed to denote that *b* in some
   sense *overrides* *a*.)  For effects *A* (allow) and *D* (deny), we
   have that:
   * *A* &#x25C2; *A* = *A*
   * *A* &#x25C2; *D* = *D*
   * *D* &#x25C2; *A* = *A*
   * *D* &#x25C2; *D* = *D*

   (This basically means that later effects override earlier ones:
   effect composition is not commutative.)

 * We denote the opposite of a policy effect *E* by &not; *E*,
   i.e. &not; *A* = *D*, &not; *D* = *A*.

 * For composing clauses, we need to introduce the idea of a
   *permission set*.  This is the effective set of permissions in
   force after composing together a sequence of permissions clauses.
   We denote the composition of a permission set with a new clause by
   &#x25C3;, which has type &#x25C3; :: `PermissionSet` &rarr;
   `Clause` &rarr; `PermissionSet` (so obviously isn't commutative).

 * We'll denote a clause { "effect": *E*, "action": *A*, "object": *O*
   } by the tuple (*E*, *A*, *O*), and we'll denote permission sets
   that have the same permission effect as a single clause as {
   ... (*E*, *A*, *O*), ... }.

 * Then we have that:
   * The empty permission set &empty; is equivalent to the single clause (deny, [\*\*], [\*\*]).
   * { ... (*E1*, *A*, *O*) ... } &#x25C3; (*E2*, *A*, *O*) = { ... (*E1* &#x25C2; *E2*, *A*, *O*) ... }
   * { ... (*E*, *A1*, *O*) ... } &#x25C3; (*E*, *A2*, *O*) = { ... (*E*, *A1* &cup; *A2*, *O*) ... }
   * { ... (*E*, *A1*, *O*) ... } &#x25C3; (&not; *E*, *A2*, *O*) = { ... (*E*, *A1* \ *A2*, *O*), (&not; *E*, *A2*, *O*) ... }
   * { ... (*E*, *A*, *O1*) ... } &#x25C3; (*E*, *A*, *O2*) = { ... (*E*, *A*, *O1* &cup; *O2*) ... }
   * { ... (*E*, *A*, *O1*) ... } &#x25C3; (&not; *E*, *A*, *O2*) = { ... (*E*, *A*, *O1* \ *O2*), (&not; *E*, *A*, *O2*) ... }
   * { ... (*E*, *A1*, *O1*) ... } &#x25C3; (&not; *E*, *A2*, *O2*) = { ... (*E*, *A1*, *O1* \ *O2*), (*E*, *A1* \ *A2*, *O1*), (&not; *E*, *A2*, *O2*) ... }

## Permission sets as partitions

We can think of a permission set in the following way.  Denote the
"space" of actions as *A*, and the space of actions as *O*.  Then a
permission set denotes a piecewise constant function *P*: *A* &times;
*O* &rarr; {allow, deny}.  The function *P* is total, meaning that the
subsets of *A* &times; *O* on which *P* is constant form a partition
of *A* &times; *O*.  We can represent this partition as follows:
define sets *S*<sub>*i*</sub> = *A*<sub>*i*</sub> &times;
*O*<sub>*i*</sub> &sube; *A* &times; *O* with *A*<sub>*i*</sub> &sube;
*A* and *O*<sub>*i*</sub> &sube; *O* (i.e. the sets *S*<sub>*i*</sub>
are abstract "rectangles" in *A* &times; *O*).  Require that *P* is
constant on each *S*<sub>*i*</sub> and require that the
*S*<sub>*i*</sub> form a partition of *A* &times; *O*.

The disjointness conditions imposed by the above representation in
terms of "rectangles" in *A* &times; *O* are awkward since the require
us to represent arbitrary sequences of set union and set difference
operations on sets of actions and objects defined by action and object
patterns.  To see just why this is awkward, suppose we have the two
clauses

*C*<sub>1</sub> = `(allow, [parcel.*], [Cadasta/PaP/parcel/*])`

*C*<sub>2</sub> = `(deny, [parcel.edit], [Cadasta/PaP/parcel/123])`

and we compose them into a permission set as

*P* = &empty; &#x25C3; *C*<sub>1</sub> &#x25C3; *C*<sub>2</sub>

This is a permission set that says we can perform any "parcel" action
on any "Cadasta/PaP" parcel, *except* that we cannot perform the
"parcel.edit" action on parcel "Cadasta/PaP/parcel/123".  We then
calculate the permission set *P* as:

*P*<sub>1</sub> = &empty; = `{ (deny, [**], [**]) }`

*P*<sub>2</sub> = &empty; &#x25C3; *C*<sub>1</sub> =

```
       { (deny, [**], [**] \ [Cadasta/PaP/parcel/*]),
         (deny, [**] \ [parcel.*], [**]),
         (allow, [parcel.*], [Cadasta/PaP/parcel/*]) }
```

*P* = &empty; &#x25C3; *C*<sub>1</sub> &#x25C3; *C*<sub>2</sub> =

```
       { (deny, [**], [**] \ [Cadasta/PaP/parcel/*]),
         (deny, [**] \ [parcel.*], [**]),
         (allow, [parcel.*] \ [parcel.edit], [Cadasta/PaP/parcel/*]),
         (allow, [parcel.*], [Cadasta/PaP/parcel/*] \ [Cadasta/PaP/parcel/123]),
         (deny, [parcel.edit], [Cadasta/PaP/parcel/123]) }
```

Representing the differences of sets required in this "partition"
representation of the permissions set is difficult, with the potential
to quickly become very inefficient unless we are very careful.

Still, the "partition of *A* &times; *O*" view of things is
conceptually useful &ndash; we clearly need the function *P* to be
total so that it assigns an allow/deny decision to allow possible
combinations of action and object.

## An operational view of permission sets

A simple operational model for how permission sets should work can be
derived from two simple observations:

1. For an (*action*, *object*) query against a permission set, the
   (*action*, *object*) pair needs to match against the
   (*action-pattern*, *object-pattern*) of one of the clauses that
   went to make up the permission set.

2. Since later clauses override earlier ones, we could just check
   individual clauses one by one starting from the last.

We shouldn't *implement* permission sets this way, because there is
likely to be a lot of overlap between the action and object patterns
in different statements, so we would end up performing repeated
failing pattern matches as we searched through the list of clauses.

What we need is a data structure that allows us to represent a
permission set as a "tree with wildcards" against which we can match
an (*action*, *object*) pair with a minimum of comparisons between
action and object path components.

I'll get to the data structure used for this below.


# Policy queries

Once the effective permissions set has been calculated for a user, the
permissions system can answer two kinds of questions:

1. Can a given user perform a given action on a given entity?
2. What actions can a given user perform on a given entity or class of
   entities?

The first question is the authorisation question asked when a user
tries to perform an operation via the platform API.  The second
question can be used to produce a list of HATEOAS links to send in API
responses.  One aspect of a system giving the kind of fine-grained
control over permissions described here is that it’s quite difficult
to come up with a simple way of getting the information about what
actions a user is allowed to perform from the back-end to the user
interface.  Ideally, user interface elements for actions a user is not
allowed to perform should either be disabled or (best of all) not
visible at all.  Using HATEOAS hypermedia links in API responses
provides a way to deal with this problem in a completely uniform way
by following some simple rules:

 * All API responses contain a hypermedia links section giving the
   URLs of endpoints to perform actions on the entity to which the API
   response refers.
 * The `links` section of every API response contains exactly the list
   of actions that the user making the request is allowed to perform.
 * The user interface uses the `links` section of API responses to
   determine what user interface elements to render: e.g., if there is
   no `edit` action in the `links` section for a given resource, do
   not render an edit button or link.

Following these rules uniformly means that there are no special cases
to deal with and we can hopefully avoid writing a lot of brittle code
to decide what UI elements should appear where depending on user
permissions.

The reasons that I like the policy-based approach I’ve described are
that i). it’s as granular or coarse as you want it to be (you can
specify special rules for individual users and/or entities as needed,
superimposed on more general cross-project or cross-organisational
policies using wildcards to cover, for example, all parcels in a
project); ii). it works in the "natural" direction, since you specify
what actions groups of users are allowed to perform on groups of
objects; iii). it makes it very easy for administrators to manage
permissions: if you need to temporarily remove access to all users to
a certain class of object, you can do this using a cross-cutting
policy.

For the most common case where a small set of stereotypical user roles
are required, you just create one policy for each role and choose
which policy to attach to a new user when you add them to an
organisation.  (The administrative user interface for managing
permissions should have a "basic" and an "advanced" mode, where the
basic mode covers only the simplest cases of assigning a selected
role/policy to a user, and the advanced mode allows for direct
manipulation of policies.)

Unfortunately, I’ve not yet found a Django module that implements this
type of permissions system.  It wouldn’t be hard to implement one
though, and I think this type of system would give us what we need in
terms of being simple to use in its default setup, but flexible enough
to fit with the more complicated and variable cases that are
inevitably going to arise.


# Permission set representation

## Data structure

## Construction

## Queries
