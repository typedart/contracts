import smartpy as sp


class TypedMinter(sp.Contract):
    def __init__(self, objkt, manager, metadata, royal):
        self.init(
            royalties = sp.big_map(tkey=sp.TNat, tvalue=sp.TRecord(issuer=sp.TAddress, royalties=sp.TNat)),
            objkt_id = 0,
            objkt = objkt,
            manager = manager,
            metadata = metadata,
            royal=royal,
            mint_paused=False
            )
    @sp.entry_point
    def mint_TYPED(self, params):
        sp.verify((params.amount > 0) & (params.amount <= 9999))
        sp.verify(~self.data.mint_paused, message="mint paused")
        c = sp.contract(sp.TRecord(address=sp.TAddress,amount=sp.TNat,token_id=sp.TNat,token_info=sp.TMap(sp.TString, sp.TBytes)), self.data.objkt, entry_point = "mint").open_some()
        sp.transfer(sp.record(address=sp.sender,amount=params.amount,token_id=self.data.objkt_id,token_info={ '' : params.metadata }), sp.mutez(0), c)
        self.data.royalties[self.data.objkt_id] = sp.record(issuer=sp.sender, royalties=self.data.royal)
        self.data.objkt_id += 1

    @sp.entry_point
    def update_royalties(self, new_royal):
        sp.set_type(new_royal, sp.TNat)
        sp.verify(sp.sender == self.data.manager, message="MP_NOT_MANAGER")
        sp.verify(new_royal <= 250, message="MP_WRONG_ROYALTIES")
        self.data.royal = new_royal

    @sp.entry_point
    def set_pause_mint(self, pause):
        sp.set_type(pause, sp.TBool)
        sp.verify(sp.sender == self.data.manager, message="MP_NOT_MANAGER")
        self.data.mint_paused = pause

    @sp.entry_point
    def payout_balance(self):
        sp.verify(sp.sender == self.data.manager, message="only the admin can receive the payment from the contract")
        sp.send(self.data.manager,sp.balance)

sp.add_compilation_target("minter", TypedMinter(
    objkt=sp.address("KT1J6NY5AU61GzUX51n59wwiZcGJ9DrNTwbK"),
    manager=sp.address("tz1aqMiWgnFddGZSTsEMSe8qbXkVGn7C4cg5"),
    royal=sp.nat(100),
    metadata=sp.utils.metadata_of_url("ipfs://QmbguJKMRmWpp4e9eenxwmsNqCcB34gzG58QymnEPkBhU8")))
