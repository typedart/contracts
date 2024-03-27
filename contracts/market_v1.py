import smartpy as sp

class TypedMarket(sp.Contract):
    SWAP_TYPE = sp.TRecord(
        issuer=sp.TAddress,
        fa2=sp.TAddress,
        objkt_id=sp.TNat,
        objkt_amount=sp.TNat,
        xtz_per_objkt=sp.TMutez,
        royalties=sp.TNat,
        creator=sp.TAddress).layout(
            ("issuer", ("fa2", ("objkt_id", ("objkt_amount", ("xtz_per_objkt", ("royalties", "creator")))))))

    def __init__(self, manager, metadata, allowed_fa2s, fee, royalties):
        self.init_type(sp.TRecord(
            manager=sp.TAddress,
            metadata=sp.TBigMap(sp.TString, sp.TBytes),
            allowed_fa2s=sp.TBigMap(sp.TAddress, sp.TUnit),
            swaps=sp.TBigMap(sp.TNat, TypedMarket.SWAP_TYPE),
            fee=sp.TNat,
            royalties=sp.TNat,
            fee_recipient=sp.TAddress,
            counter=sp.TNat,
            swaps_paused=sp.TBool,
            collects_paused=sp.TBool))

        self.init(
            manager=manager,
            metadata=metadata,
            allowed_fa2s=allowed_fa2s,
            swaps=sp.big_map(),
            fee=fee,
            royalties=royalties,
            fee_recipient=manager,
            counter=0,
            swaps_paused=False,
            collects_paused=False)

    def check_is_manager(self):
        sp.verify(sp.sender == self.data.manager, message="MP_NOT_MANAGER")

    def check_no_tez_transfer(self):
        sp.verify(sp.amount == sp.tez(0), message="MP_TEZ_TRANSFER")

    @sp.entry_point
    def swap(self, params):
        sp.set_type(params, sp.TRecord(fa2=sp.TAddress,objkt_id=sp.TNat,objkt_amount=sp.TNat,xtz_per_objkt=sp.TMutez,royalties=sp.TNat,creator=sp.TAddress).layout(("fa2", ("objkt_id", ("objkt_amount", ("xtz_per_objkt", ("royalties", "creator")))))))
        sp.verify(~self.data.swaps_paused, message="MP_SWAPS_PAUSED")
        self.check_no_tez_transfer()
        sp.verify(self.data.allowed_fa2s.contains(params.fa2),message="MP_FA2_NOT_ALLOWED")
        sp.verify(params.objkt_amount > 0, message="MP_NO_SWAPPED_EDITIONS")
        self.fa2_transfer(fa2=params.fa2,from_=sp.sender,to_=sp.self_address,token_id=params.objkt_id,token_amount=params.objkt_amount)
        self.data.swaps[self.data.counter] = sp.record(issuer=sp.sender,fa2=params.fa2,objkt_id=params.objkt_id,objkt_amount=params.objkt_amount,xtz_per_objkt=params.xtz_per_objkt,royalties= self.data.royalties,creator=params.creator)
        self.data.counter += 1

    @sp.entry_point
    def collect(self, swap_id):
        sp.set_type(swap_id, sp.TNat)
        sp.verify(~self.data.collects_paused, message="MP_COLLECTS_PAUSED")
        sp.verify(self.data.swaps.contains(swap_id), message="MP_WRONG_SWAP_ID")
        swap = sp.local("swap", self.data.swaps[swap_id])
        sp.verify(sp.sender != swap.value.issuer, message="MP_IS_SWAP_ISSUER")
        sp.verify(sp.amount == swap.value.xtz_per_objkt,message="MP_WRONG_TEZ_AMOUNT")
        sp.verify(swap.value.objkt_amount > 0, message="MP_SWAP_COLLECTED")
        with sp.if_(swap.value.xtz_per_objkt != sp.tez(0)):
            royalties_amount = sp.local("royalties_amount", sp.split_tokens(swap.value.xtz_per_objkt, swap.value.royalties, 1000))
            with sp.if_(royalties_amount.value > sp.mutez(0)):
                sp.send(swap.value.creator, royalties_amount.value)
            fee_amount = sp.local("fee_amount", sp.split_tokens(swap.value.xtz_per_objkt, self.data.fee, 1000))
            with sp.if_(fee_amount.value > sp.mutez(0)):
                sp.send(self.data.fee_recipient, fee_amount.value)
            sp.send(swap.value.issuer, sp.amount - royalties_amount.value - fee_amount.value)
        self.fa2_transfer(fa2=swap.value.fa2,from_=sp.self_address,to_=sp.sender,token_id=swap.value.objkt_id,token_amount=1)
        self.data.swaps[swap_id].objkt_amount = sp.as_nat(swap.value.objkt_amount - 1)
        with sp.if_(self.data.swaps[swap_id].objkt_amount == 0):
            del self.data.swaps[swap_id]
            
    @sp.entry_point
    def cancel_swap(self, swap_id):
        sp.set_type(swap_id, sp.TNat)
        self.check_no_tez_transfer()
        sp.verify(self.data.swaps.contains(swap_id), message="MP_WRONG_SWAP_ID")
        swap = sp.local("swap", self.data.swaps[swap_id])
        sp.verify(sp.sender == swap.value.issuer, message="MP_NOT_SWAP_ISSUER")
        sp.verify(swap.value.objkt_amount > 0, message="MP_SWAP_COLLECTED")
        self.fa2_transfer(fa2=swap.value.fa2,from_=sp.self_address,to_=sp.sender,token_id=swap.value.objkt_id,token_amount=swap.value.objkt_amount)
        del self.data.swaps[swap_id]

    @sp.entry_point
    def update_fee(self, new_fee):
        sp.set_type(new_fee, sp.TNat)
        self.check_is_manager()
        self.check_no_tez_transfer()
        sp.verify(new_fee <= 250, message="MP_WRONG_FEES")
        self.data.fee = new_fee

    @sp.entry_point
    def update_royalties(self, new_royalties):
        sp.set_type(new_royalties, sp.TNat)
        self.check_is_manager()
        self.check_no_tez_transfer()
        sp.verify(new_royalties <= 250, message="MP_WRONG_ROYALTIES")
        self.data.royalties = new_royalties

    @sp.entry_point
    def set_pause_swaps(self, pause):
        sp.set_type(pause, sp.TBool)
        self.check_is_manager()
        self.check_no_tez_transfer()
        self.data.swaps_paused = pause

    @sp.entry_point
    def set_pause_collects(self, pause):
        sp.set_type(pause, sp.TBool)
        self.check_is_manager()
        self.check_no_tez_transfer()
        self.data.collects_paused = pause

    @sp.entry_point
    def payout_balance(self):
        sp.verify(sp.sender == self.data.manager, message="only the admin can receive the payment from the contract")
        sp.send(self.data.manager,sp.balance)
        
    def fa2_transfer(self, fa2, from_, to_, token_id, token_amount):
        c = sp.contract(t=sp.TList(sp.TRecord(from_=sp.TAddress,txs=sp.TList(sp.TRecord(to_=sp.TAddress,token_id=sp.TNat,amount=sp.TNat).layout(("to_", ("token_id", "amount")))))),address=fa2,entry_point="transfer").open_some()
        sp.transfer(arg=sp.list([sp.record(from_=from_,txs=sp.list([sp.record(to_=to_,token_id=token_id,amount=token_amount)]))]),amount=sp.mutez(0),destination=c)

sp.add_compilation_target("typedmarket", TypedMarket(
    manager=sp.address("tz1aqMiWgnFddGZSTsEMSe8qbXkVGn7C4cg5"),
    metadata=sp.utils.metadata_of_url("ipfs://QmNoYCy8RA2FEjpb6kzQbmo4w8nVuWkNEJRoQhsV7VBEun"),
    allowed_fa2s=sp.big_map({sp.address("KT1J6NY5AU61GzUX51n59wwiZcGJ9DrNTwbK"): sp.unit}),
    royalties=sp.nat(100),
    fee=sp.nat(50)))

