from enum import Enum

class UserRoles(Enum):
    SELLER = 'seller'
    CUSTOMER = 'customer'


    @classmethod
    def values(cls):
        return [role.value for role in cls]

    @classmethod
    def has_value(cls, value):
        return value in cls.values()
    