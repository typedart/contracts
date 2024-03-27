import smartpy as sp

class FA2_config:
    def __init__(self,
                 debug_mode                   = False,
                 single_asset                 = False,
                 non_fungible                 = False,
                 add_mutez_transfer           = True,
                 readable                     = True,
                 force_layouts                = True,
                 support_operator             = True,
                 assume_consecutive_token_ids = True,
                 add_permissions_descriptor   = False,
                 lazy_entry_points = False,
                 lazy_entry_points_multiple = False
                 ):

        if debug_mode:
            self.my_map = sp.map
        else:
            self.my_map = sp.big_map
        self.single_asset = single_asset
        self.non_fungible = non_fungible
        self.readable = readable
        self.force_layouts = force_layouts
        self.support_operator = support_operator
        self.assume_consecutive_token_ids = assume_consecutive_token_ids
        self.add_mutez_transfer = add_mutez_transfer
        self.add_permissions_descriptor = add_permissions_descriptor
        self.lazy_entry_points = lazy_entry_points
        self.lazy_entry_points_multiple = lazy_entry_points_multiple
        if lazy_entry_points and lazy_entry_points_multiple:
            raise Exception(
                "Cannot provide lazy_entry_points and lazy_entry_points_multiple")

        name = "FA2"
        if debug_mode:
            name += "-debug"
        if single_asset:
            name += "-single_asset"
        if non_fungible:
            name += "-nft"
        if add_mutez_transfer:
            name += "-mutez"
        if not readable:
            name += "-no_readable"
        if not force_layouts:
            name += "-no_layout"
        if not support_operator:
            name += "-no_ops"
        if not assume_consecutive_token_ids:
            name += "-no_toknat"
        if add_permissions_descriptor:
            name += "-perm_desc"
        if lazy_entry_points:
            name += "-lep"
        if lazy_entry_points_multiple:
            name += "-lepm"
        self.name = name


token_id_type = sp.TNat

class Error_message:
    def __init__(self, config):
        self.config = config
        self.prefix = "FA2_"
    def make(self, s): return (self.prefix + s)
    def token_undefined(self):       return self.make("TOKEN_UNDEFINED")
    def insufficient_balance(self):  return self.make("INSUFFICIENT_BALANCE")
    def not_operator(self):          return self.make("NOT_OPERATOR")
    def not_owner(self):             return self.make("NOT_OWNER")
    def operators_unsupported(self): return self.make("OPERATORS_UNSUPPORTED")

class Batch_transfer:
    def __init__(self, config):
        self.config = config
    def get_transfer_type(self):
        tx_type = sp.TRecord(to_ = sp.TAddress,
                             token_id = token_id_type,
                             amount = sp.TNat)
        if self.config.force_layouts:
            tx_type = tx_type.layout(
                ("to_", ("token_id", "amount"))
            )
        transfer_type = sp.TRecord(from_ = sp.TAddress,
                                   txs = sp.TList(tx_type)).layout(
                                       ("from_", "txs"))
        return transfer_type
    def get_type(self):
        return sp.TList(self.get_transfer_type())
    def item(self, from_, txs):
        v = sp.record(from_ = from_, txs = txs)
        return sp.set_type_expr(v, self.get_transfer_type())

class Operator_param:
    def __init__(self, config):
        self.config = config
    def get_type(self):
        t = sp.TRecord(
            owner = sp.TAddress,
            operator = sp.TAddress,
            token_id = token_id_type)
        if self.config.force_layouts:
            t = t.layout(("owner", ("operator", "token_id")))
        return t
    def make(self, owner, operator, token_id):
        r = sp.record(owner = owner,
                      operator = operator,
                      token_id = token_id)
        return sp.set_type_expr(r, self.get_type())


class Ledger_key:
    def __init__(self, config):
        self.config = config
    def make(self, user, token):
        user = sp.set_type_expr(user, sp.TAddress)
        token = sp.set_type_expr(token, token_id_type)
        if self.config.single_asset:
            result = user
        else:
            result = sp.pair(user, token)
        if self.config.readable:
            return result
        else:
            return sp.pack(result)

class Ledger_value:
    def get_type():
        return sp.TRecord(balance = sp.TNat)
    def make(balance):
        return sp.record(balance = balance)

class Operator_set:
    def __init__(self, config):
        self.config = config
    def inner_type(self):
        return sp.TRecord(owner = sp.TAddress,
                          operator = sp.TAddress,
                          token_id = token_id_type
                          ).layout(("owner", ("operator", "token_id")))
    def key_type(self):
        if self.config.readable:
            return self.inner_type()
        else:
            return sp.TBytes
    def make(self):
        return self.config.my_map(tkey = self.key_type(), tvalue = sp.TUnit)
    def make_key(self, owner, operator, token_id):
        metakey = sp.record(owner = owner,
                            operator = operator,
                            token_id = token_id)
        metakey = sp.set_type_expr(metakey, self.inner_type())
        if self.config.readable:
            return metakey
        else:
            return sp.pack(metakey)
    def add(self, set, owner, operator, token_id):
        set[self.make_key(owner, operator, token_id)] = sp.unit
    def remove(self, set, owner, operator, token_id):
        del set[self.make_key(owner, operator, token_id)]
    def is_member(self, set, owner, operator, token_id):
        return set.contains(self.make_key(owner, operator, token_id))

class Balance_of:
    def request_type():
        return sp.TRecord(
            owner = sp.TAddress,
            token_id = token_id_type).layout(("owner", "token_id"))
    def response_type():
        return sp.TList(
            sp.TRecord(
                request = Balance_of.request_type(),
                balance = sp.TNat).layout(("request", "balance")))
    def entry_point_type():
        return sp.TRecord(
            callback = sp.TContract(Balance_of.response_type()),
            requests = sp.TList(Balance_of.request_type())
        ).layout(("requests", "callback"))

class Token_meta_data:
    def __init__(self, config):
        self.config = config
    def get_type(self):
        t = sp.TRecord(
            token_id = token_id_type,
            token_info = sp.TMap(sp.TString, sp.TBytes)
        )
        if self.config.force_layouts:
            t = t.layout(("token_id",
                          ("token_info")))
        return t
    def set_type_and_layout(self, expr):
        sp.set_type(expr, self.get_type())
    def request_type(self):
        return token_id_type

class Permissions_descriptor:
    def __init__(self, config):
        self.config = config
    def get_type(self):
        operator_transfer_policy = sp.TVariant(
            no_transfer = sp.TUnit,
            owner_transfer = sp.TUnit,
            owner_or_operator_transfer = sp.TUnit)
        if self.config.force_layouts:
            operator_transfer_policy = operator_transfer_policy.layout(
                                       ("no_transfer",
                                        ("owner_transfer",
                                         "owner_or_operator_transfer")))
        owner_transfer_policy =  sp.TVariant(
            owner_no_hook = sp.TUnit,
            optional_owner_hook = sp.TUnit,
            required_owner_hook = sp.TUnit)
        if self.config.force_layouts:
            owner_transfer_policy = owner_transfer_policy.layout(
                                       ("owner_no_hook",
                                        ("optional_owner_hook",
                                         "required_owner_hook")))
        custom_permission_policy = sp.TRecord(
            tag = sp.TString,
            config_api = sp.TOption(sp.TAddress))
        main = sp.TRecord(
            operator = operator_transfer_policy,
            receiver = owner_transfer_policy,
            sender   = owner_transfer_policy,
            custom   = sp.TOption(custom_permission_policy))
        if self.config.force_layouts:
            main = main.layout(("operator",
                                ("receiver",
                                 ("sender", "custom"))))
        return main
    def set_type_and_layout(self, expr):
        sp.set_type(expr, self.get_type())
    def make(self):
        def uv(s):
            return sp.variant(s, sp.unit)
        operator = ("owner_or_operator_transfer"
                    if self.config.support_operator
                    else "owner_transfer")
        v = sp.record(
            operator = uv(operator),
            receiver = uv("owner_no_hook"),
            sender = uv("owner_no_hook"),
            custom = sp.none
            )
        v = sp.set_type_expr(v, self.get_type())
        return v

class Token_id_set:
    def __init__(self, config):
        self.config = config
    def empty(self):
        if self.config.assume_consecutive_token_ids:
            # The "set" is its cardinal.
            return sp.nat(0)
        else:
            return sp.set(t = token_id_type)
    def add(self, metaset, v):
        if self.config.assume_consecutive_token_ids:
            metaset.set(sp.max(metaset, v + 1))
        else:
            metaset.add(v)
    def contains(self, metaset, v):
        if self.config.assume_consecutive_token_ids:
            return (v < metaset)
        else:
            metaset.contains(v)


def mutez_transfer(contract, params):
    sp.verify(sp.sender == contract.data.administrator)
    sp.set_type(params.destination, sp.TAddress)
    sp.set_type(params.amount, sp.TMutez)
    sp.send(params.destination, params.amount)

class FA2_core(sp.Contract):
    def __init__(self, config, **extra_storage):
        self.config = config
        self.error_message = Error_message(self.config)
        self.operator_set = Operator_set(self.config)
        self.operator_param = Operator_param(self.config)
        self.token_id_set = Token_id_set(self.config)
        self.ledger_key = Ledger_key(self.config)
        self.token_meta_data = Token_meta_data(self.config)
        self.permissions_descriptor_ = Permissions_descriptor(self.config)
        self.batch_transfer    = Batch_transfer(self.config)
        if  self.config.add_mutez_transfer:
            self.transfer_mutez = sp.entry_point(mutez_transfer)
        if  self.config.add_permissions_descriptor:
            def permissions_descriptor(self, params):
                sp.set_type(params, sp.TContract(self.permissions_descriptor_.get_type()))
                v = self.permissions_descriptor_.make()
                sp.transfer(v, sp.mutez(0), params)
            self.permissions_descriptor = sp.entry_point(permissions_descriptor)
        if config.lazy_entry_points:
            self.add_flag("lazy_entry_points")
        if config.lazy_entry_points_multiple:
            self.add_flag("lazy_entry_points_multiple")
        self.init(
            payout = sp.address("tz1aqMiWgnFddGZSTsEMSe8qbXkVGn7C4cg5"), #bu adres degiscek
            ledger =self.config.my_map(tvalue = Ledger_value.get_type()),
            token_metadata =self.config.my_map(tvalue = self.token_meta_data.get_type()),
            operators = self.operator_set.make(),
            all_tokens = self.token_id_set.empty(),
            **extra_storage
        )

    @sp.entry_point
    def transfer(self, params):
        sp.verify( ~self.is_paused() )
        sp.set_type(params, self.batch_transfer.get_type())
        sp.for transfer in params:
           current_from = transfer.from_
           sp.for tx in transfer.txs:
                if self.config.single_asset:
                    sp.verify(tx.token_id == 0, "single-asset: token-id <> 0")
                if self.config.support_operator:
                          sp.verify(
                              (self.is_administrator(sp.sender)) |
                              (current_from == sp.sender) |
                              self.operator_set.is_member(self.data.operators,
                                                          current_from,
                                                          sp.sender,
                                                          tx.token_id),
                              message = self.error_message.not_operator())
                else:
                          sp.verify(
                              (self.is_administrator(sp.sender)) |
                              (current_from == sp.sender),
                              message = self.error_message.not_owner())
                sp.verify(self.data.token_metadata.contains(tx.token_id),
                          message = self.error_message.token_undefined())
                sp.if (tx.amount > 0):
                    from_user = self.ledger_key.make(current_from, tx.token_id)
                    sp.verify(
                        (self.data.ledger[from_user].balance >= tx.amount),
                        message = self.error_message.insufficient_balance())
                    to_user = self.ledger_key.make(tx.to_, tx.token_id)
                    self.data.ledger[from_user].balance = sp.as_nat(
                        self.data.ledger[from_user].balance - tx.amount)
                    sp.if self.data.ledger.contains(to_user):
                        self.data.ledger[to_user].balance += tx.amount
                    sp.else:
                         self.data.ledger[to_user] = Ledger_value.make(tx.amount)
                sp.else:
                    pass
     
    @sp.entry_point
    def burn(self, params):
        sp.set_type(params, sp.TRecord(address = sp.TAddress, token_id = sp.TNat, amount = sp.TNat))
        sp.verify( ~self.is_paused())
        sp.verify((self.is_administrator(sp.sender)) |(params.address == sp.sender),message = self.error_message.not_owner())
        sp.verify(self.data.token_metadata.contains(params.token_id),message = self.error_message.token_undefined())
        sp.if (params.amount > 0):
            from_user = self.ledger_key.make(params.address, params.token_id)
            sp.verify((self.data.ledger[from_user].balance >= params.amount),message = self.error_message.insufficient_balance())
            self.data.ledger[from_user].balance = sp.as_nat(self.data.ledger[from_user].balance - params.amount)
            sp.if (self.data.ledger[from_user].balance == 0):
                del self.data.ledger[from_user]
        sp.else:
            pass
                     
    @sp.entry_point
    def balance_of(self, params):
        sp.verify( ~self.is_paused() )
        sp.set_type(params, Balance_of.entry_point_type())
        def f_process_request(req):
            user = self.ledger_key.make(req.owner, req.token_id)
            sp.verify(self.data.token_metadata.contains(req.token_id),
                      message = self.error_message.token_undefined())
            sp.if self.data.ledger.contains(user):
                balance = self.data.ledger[user].balance
                sp.result(
                    sp.record(
                        request = sp.record(
                            owner = sp.set_type_expr(req.owner, sp.TAddress),
                            token_id = sp.set_type_expr(req.token_id, sp.TNat)),
                        balance = balance))
            sp.else:
                sp.result(
                    sp.record(
                        request = sp.record(
                            owner = sp.set_type_expr(req.owner, sp.TAddress),
                            token_id = sp.set_type_expr(req.token_id, sp.TNat)),
                        balance = 0))
        res = sp.local("responses", params.requests.map(f_process_request))
        destination = sp.set_type_expr(params.callback,
                                       sp.TContract(Balance_of.response_type()))
        sp.transfer(res.value, sp.mutez(0), destination)

    @sp.entry_point
    def update_operators(self, params):
        sp.set_type(params, sp.TList(
            sp.TVariant(
                add_operator = self.operator_param.get_type(),
                remove_operator = self.operator_param.get_type())))
        if self.config.support_operator:
            sp.for update in params:
                with update.match_cases() as arg:
                    with arg.match("add_operator") as upd:
                        sp.verify((upd.owner == sp.sender) |
                                  (self.is_administrator(sp.sender)))
                        self.operator_set.add(self.data.operators,
                                              upd.owner,
                                              upd.operator,
                                              upd.token_id)
                    with arg.match("remove_operator") as upd:
                        sp.verify((upd.owner == sp.sender) |
                                  (self.is_administrator(sp.sender)))
                        self.operator_set.remove(self.data.operators,
                                                 upd.owner,
                                                 upd.operator,
                                                 upd.token_id)
        else:
            sp.failwith(self.error_message.operators_unsupported())

    @sp.entry_point
    def payout_balance(self):
        sp.verify(sp.sender == self.data.payout, message="only the admin can receive the payment from the contract")
        sp.send(self.data.payout,sp.balance)
        
    def is_paused(self):
        return sp.bool(False)

    def is_administrator(self, sender):
        return sp.bool(False)

class FA2_administrator(FA2_core):
    def is_administrator(self, sender):
        return sender == self.data.administrator

    @sp.entry_point
    def set_administrator(self, params):
        sp.verify(self.is_administrator(sp.sender))
        self.data.administrator = params

class FA2_pause(FA2_core):
    def is_paused(self):
        return self.data.paused

    @sp.entry_point
    def set_pause(self, params):
        sp.verify(self.is_administrator(sp.sender))
        self.data.paused = params

class FA2_mint(FA2_core):
    @sp.entry_point
    def mint(self, params):
        sp.verify(self.is_administrator(sp.sender))
        # We don't check for pauseness because we're the admin.
        if self.config.single_asset:
            sp.verify(params.token_id == 0, "single-asset: token-id <> 0")
        if self.config.non_fungible:
            sp.verify(params.amount == 1, "NFT-asset: amount <> 1")
            sp.verify(~ self.token_id_set.contains(self.data.all_tokens,
                                                   params.token_id),
                      "NFT-asset: cannot mint twice same token")
        user = self.ledger_key.make(params.address, params.token_id)
        self.token_id_set.add(self.data.all_tokens, params.token_id)
        sp.if self.data.ledger.contains(user):
            self.data.ledger[user].balance += params.amount
        sp.else:
            self.data.ledger[user] = Ledger_value.make(params.amount)
        sp.if self.data.token_metadata.contains(params.token_id):
             pass
        sp.else:
             self.data.token_metadata[params.token_id] = sp.record(
                 token_id=params.token_id,
                 token_info=params.token_info
                 )

class FA2_token_metadata(FA2_core):
    @sp.entry_point
    def token_metadata(self, params):
        sp.verify( ~self.is_paused() )
        sp.set_type(params,
                    sp.TRecord(
                        token_ids = sp.TList(sp.TNat),
                        handler = sp.TLambda(
                            sp.TList(self.token_meta_data.get_type()),
                            sp.TUnit)
                    ).layout(("token_ids", "handler")))
        def f_on_request(req):
            self.token_meta_data.set_type_and_layout(self.data.token_metadata[req])
            sp.result(self.data.token_metadata[req])
        sp.compute(params.handler(params.token_ids.map(f_on_request)))

def global_parameter(env_var, default):
    try:
        if os.environ[env_var] == "true" :
            return True
        if os.environ[env_var] == "false" :
            return False
        return default
    except:
        return default

def environment_config():
    return FA2_config(
        debug_mode = global_parameter("debug_mode", False),
        single_asset = global_parameter("single_asset", False),
        non_fungible = global_parameter("non_fungible", False),
        add_mutez_transfer = global_parameter("add_mutez_transfer", False),
        readable = global_parameter("readable", True),
        force_layouts = global_parameter("force_layouts", True),
        support_operator = global_parameter("support_operator", True),
        assume_consecutive_token_ids = global_parameter("assume_consecutive_token_ids", True),
        add_permissions_descriptor = global_parameter("add_permissions_descriptor", False),
        lazy_entry_points = global_parameter("lazy_entry_points", False),
        lazy_entry_points_multiple = global_parameter("lazy_entry_points_multiple", False),
    )
class FA2(FA2_token_metadata, FA2_mint, FA2_administrator, FA2_pause, FA2_core):
    def __init__(self, config, admin, meta):
        FA2_core.__init__(self, config, paused = False, administrator = admin, metadata = meta)


sp.add_compilation_target("FA2", FA2(
    config = environment_config(), 
    admin = sp.address("tz1aqMiWgnFddGZSTsEMSe8qbXkVGn7C4cg5"),
    meta=sp.utils.metadata_of_url("ipfs://QmSRJz65xXLuu5tSR1RfnGE86SaHe4qwPQamet7S1joJjC")))
