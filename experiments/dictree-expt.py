from dictree import Dictree, WILDCARD

d1 = Dictree()
d1['parcel', 'edit',   'Cadasta', 'PaP',    'parcel', '123'] = 'deny'
d1['parcel', 'edit',   'Cadasta', 'PaP',    'parcel', WILDCARD] = 'allow'
d1['parcel', WILDCARD, 'Cadasta', 'PaP',    'parcel', WILDCARD] = 'allow'
d1['parcel', WILDCARD, WILDCARD,  WILDCARD, WILDCARD, WILDCARD] = 'allow'
d1['parcel', WILDCARD, 'Cadasta', 'PaP',    'parcel', WILDCARD] = 'allow'
d1[WILDCARD, WILDCARD, WILDCARD,  WILDCARD, WILDCARD, WILDCARD] = 'deny'

d2 = Dictree()
d2[WILDCARD, WILDCARD, WILDCARD,  WILDCARD, WILDCARD, WILDCARD] = 'deny'
d2[WILDCARD, 'view',   WILDCARD,  WILDCARD, WILDCARD, WILDCARD] = 'allow'
d2['parcel', WILDCARD, 'Cadasta', 'PaP',    'parcel', WILDCARD] = 'allow'
d2['parcel', 'edit',   'Cadasta', 'PaP',    'parcel', '123'] = 'deny'
d2['parcel', WILDCARD, 'Cadasta', 'PaP',    'parcel', '100'] = 'deny'


print('[WILDCARD, WILDCARD, WILDCARD, WILDCARD, WILDCARD, WILDCARD] = deny')
print('[WILDCARD, view,     WILDCARD, WILDCARD, WILDCARD, WILDCARD] = allow')
print('[parcel,   WILDCARD, Cadasta,  PaP,      parcel,   WILDCARD] = allow')
print('[parcel,   edit,     Cadasta,  PaP,      parcel,   123]      = deny')
print('[parcel,   WILDCARD, Cadasta,  PaP,      parcel,   100]      = deny')
print()

print('[parcel, edit, Cadasta, PaP, parcel, 123]',
      d2['parcel', 'edit',   'Cadasta', 'PaP',    'parcel', '123'])
print('[parcel, view, Cadasta, PaP, parcel, 123]',
      d2['parcel', 'view',   'Cadasta', 'PaP',    'parcel', '123'])
print('[parcel, edit, Cadasta, PaP, parcel, 100]',
      d2['parcel', 'edit',   'Cadasta', 'PaP',    'parcel', '100'])
print('[parcel, view, Cadasta, PaP, parcel, 100]',
      d2['parcel', 'view',   'Cadasta', 'PaP',    'parcel', '100'])
print('[parcel, edit, Cadasta, PaP, parcel, 95]',
      d2['parcel', 'edit',   'Cadasta', 'PaP',    'parcel', '95'])
print('[parcel, view, Cadasta, PaP, parcel, 95]',
      d2['parcel', 'view',   'Cadasta', 'PaP',    'parcel', '95'])
print('[admin, invite, iross@cadasta.org]',
      d2['admin',  'invite', 'iross@cadasta.org'])
