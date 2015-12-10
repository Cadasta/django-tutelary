{-# LANGUAGE MultiParamTypeClasses #-}
module Tutelary where

import Data.List
import qualified Data.Map as M


-- Composition for:
--
--  * Effects: Effect <+ Effect => Effect;
--  * Permission sets and statements: Permissions <+ Clause => Permissions.

class Composable a b where
  (<+) :: a -> b -> a


-- Effects and their composition.

data Effect = Allow | Deny deriving (Eq, Ord, Show, Read)

instance Composable Effect Effect where
  Allow <+ Allow = Allow
  Allow <+ Deny  = Deny
  Deny  <+ Allow = Allow
  Deny  <+ Deny  = Deny


-- Patterns for actions and objects.

data Pattern = Wild | Fix String deriving (Eq, Ord)

instance Show Pattern where
  show (Fix s) = s
  show Wild = "*"

instance Read Pattern where
  readsPrec _ ('*':ss) = [(Wild, ss)]
  readsPrec _ s = [(Fix s, "")]

showPattern :: Char -> [Pattern] -> String
showPattern sep ps = intercalate (sep:[]) $ map show ps

readPattern :: Char -> String -> [Pattern]
readPattern sep s = map read $ split sep s

showFixed :: Char -> [String] -> String
showFixed sep = intercalate (sep:[])

readFixed :: Char -> String -> [String]
readFixed sep s = split sep s

readAction = readFixed '.'
readObject = readFixed '/'
readActionP = readPattern '.'
readObjectP = readPattern '/'


(#==) :: String -> Pattern -> Bool
s #== (Fix s') = s == s'
s #== Wild     = True


-- Actions, objects and patterns.

type Action = [String]
type ActionP = [Pattern]
type Object = [String]
type ObjectP = [Pattern]


-- Clauses and searching in statements.

data Clause = Clause Effect [ActionP] [ObjectP]

instance Show Clause where
  show (Clause eff as os) = show eff ++ " " ++ show as ++ " " ++ show os

match :: (Action, Object) -> Clause -> Maybe Effect
match (act, obj) (Clause eff aps ops) =
  if (null aps || any (act `repMatch`) aps) &&
     (null ops || any (obj `repMatch`) ops)
  then Just eff else Nothing
  where repMatch ss ps = and $ zipWith (#==) ss ps


-- Permission sets.

class PermissionSet ps where
  check :: ps -> Action -> Object -> Effect


-- Permission sets as functions.

data FuncPS = FuncPS (Action -> Object -> Effect)

instance Composable FuncPS Clause where
  (FuncPS ps) <+ c = FuncPS $ \act obj ->
    case (act, obj) `match` c of
      Just eff -> eff
      Nothing  -> ps act obj

instance PermissionSet FuncPS where
  check (FuncPS f) = f

emptyFuncPS :: FuncPS
emptyFuncPS = FuncPS $ \_ _ -> Deny


-- Permission sets as lists of clauses.

data ListPS = ListPS [Clause]

instance Show ListPS where
  show (ListPS cs) = show cs

instance Composable ListPS Clause where
  (ListPS ss) <+ s = ListPS $ s : ss

instance PermissionSet ListPS where
  check (ListPS cs) act obj = loop cs
    where loop [] = Deny
          loop (c:cs) = case (act, obj) `match` c of
            Just eff -> eff
            Nothing  -> loop cs

emptyListPS :: ListPS
emptyListPS = ListPS []


-- Permission sets as dictionary trees of clauses.

data Tree = Node { perm :: Maybe Effect
                 , subs :: M.Map Pattern Tree
                 , wildFirst :: Bool }
          deriving Show

emptyTree :: Effect -> Tree
emptyTree e0 = Node (Just e0) M.empty False

tinsert :: Tree -> [Pattern] -> Effect -> Tree
tinsert root search val = go root search
  where go (Node _  nm wf) [] = Node (Just val) nm wf
        go (Node nv nm wf) (k:ks) = case M.lookup k nm of
          Nothing -> Node nv (M.insert k (makeNew ks) nm) (k == Wild)
          Just n' -> Node nv (M.insert k (go n' ks) nm) (k == Wild)
        makeNew = makeNew' . dropWhileEnd (== Wild)
        makeNew' [] = Node (Just val) M.empty False
        makeNew' (k:ks) = Node Nothing (M.singleton k $ makeNew ks) (k == Wild)

tfind :: Tree -> [String] -> Effect
tfind root@(Node (Just e0) _ _) search = case go root search of
  Nothing -> e0
  Just e -> e
  where go (Node v _ _) [] = v
        go (Node v m wf) (k:ks)
          | M.null m = v
          | otherwise = case M.lookup p1 m of
            Nothing -> case M.lookup p2 m of
              Nothing -> Nothing
              Just n' -> go n' ks
            Just n' -> case go n' ks of
              Just e -> Just e
              Nothing -> case M.lookup p2 m of
                Nothing -> Nothing
                Just n'' -> go n'' ks
          where (p1, p2) = if wf then (Wild, Fix k) else (Fix k, Wild)

data DictTreePS = DictTreePS Tree

instance Show DictTreePS where
  show (DictTreePS t) = show t

instance Composable DictTreePS Clause where
  (DictTreePS t) <+ (Clause eff acts objs) =
    DictTreePS $ foldl' (\tt sc -> tinsert tt sc eff) t $
      [act ++ obj | act <- acts, obj <- objs]

instance PermissionSet DictTreePS where
  check (DictTreePS t) act obj = tfind t $ act ++ obj

emptyDictTreePS :: DictTreePS
emptyDictTreePS = DictTreePS (emptyTree Deny)


-- Examples.

parcel_view, parcel_edit, party_view, party_edit, admin_invite :: Action
parcel_view = readAction "parcel.view"
parcel_edit = readAction "parcel.edit"
party_view = readAction "party.view"
party_edit = readAction "party.edit"
admin_invite = readAction "admin.invite"

parcel_edit_p, admin_invite_p :: ActionP
parcel_actions_p, invite_actions_p :: ActionP
parcel_edit_p = readActionP "parcel.edit"
admin_invite_p = readActionP "admin.invite"
parcel_actions_p = readActionP "parcel.*"
invite_actions_p = readActionP "*.invite"

h4h_parcel_100, h4h_parcel_123, h4h_party_12 :: Object
h4h_parcel_100 = readObject "H4H/PortAuPrince/parcel/100"
h4h_parcel_123 = readObject "H4H/PortAuPrince/parcel/123"
h4h_party_12 = readObject "H4H/PortAuPrince/party/12"

h4h_parcels_p, h4h_parcel_123_p, af_batangas_p, any_obj :: ObjectP
h4h_parcels_p = readObjectP "H4H/*/parcel/*"
h4h_parcel_123_p = readObjectP "H4H/*/parcel/123"
af_batangas_p = readObjectP "AsiaFoundation/Batangas/*/*"
any_obj = []

s1, s2, s3 :: Clause
s1 = Clause Allow [parcel_actions_p] [h4h_parcels_p]
s2 = Clause Deny [parcel_edit_p] [h4h_parcel_123_p]
s3 = Clause Allow [admin_invite_p] [any_obj]

fperms :: FuncPS
fperms = emptyFuncPS <+ s1 <+ s2 <+ s3

lperms :: ListPS
lperms = emptyListPS <+ s1 <+ s2 <+ s3

tperms :: DictTreePS
tperms = emptyDictTreePS <+ s1 <+ s2 <+ s3

tst :: PermissionSet ps => ps -> IO ()
tst ps = do
  print $ check ps parcel_edit h4h_parcel_100
  print $ check ps parcel_edit h4h_parcel_123
  print $ check ps parcel_view h4h_parcel_100
  print $ check ps parcel_view h4h_parcel_123
  print $ check ps admin_invite []


-- Utilities.

-- Break a string into a list of elements, delimited by a given
-- character.
split :: Char -> String -> [String]
split c s =  case dropWhile (== c) s of
  "" -> []
  s' -> w : split c s''
    where (w, s'') = break (== c) s'
