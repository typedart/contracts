import smartpy as sp

class TypedRegister(sp.Contract):
#sp.trace(sp.amount)
    def __init__(self):
        self.init(
            name_check = sp.big_map(tkey=sp.TBytes, tvalue=sp.TRecord(name =  sp.TBytes)),
            userlist = sp.big_map(tkey=sp.TAddress, tvalue=sp.TRecord(name =  sp.TBytes)),
            admin = sp.address("tz1aqMiWgnFddGZSTsEMSe8qbXkVGn7C4cg5"),
            metadata = sp.utils.metadata_of_url("ipfs://QmeEMPmjUZ2uDoUJ741xxJersrEMBjW2axJKuNbMhYi76J")
        )     

    @sp.entry_point
    def register(self, params):
        sp.verify(~self.data.name_check.contains(params.name), message="this name is taken")
        sp.if (self.data.userlist.contains(sp.sender)):
            del self.data.name_check[self.data.userlist[sp.sender].name]
            self.data.name_check[params.name] = sp.record(name=params.name)
            self.data.userlist[sp.sender] = sp.record(name=params.name)
        sp.else:
            self.data.name_check[params.name] = sp.record(name=params.name)
            self.data.userlist[sp.sender] = sp.record(name=params.name)

    @sp.entry_point
    def payout_balance(self):
        sp.verify(sp.sender == self.data.admin, message="not admin")
        sp.send(self.data.admin,sp.balance)

sp.add_compilation_target("typedregister", TypedRegister())
