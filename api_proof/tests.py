from django.test import TestCase

# Create your tests here.


{
    "email": "test@example.com",
    "password": "Louis1234",
    "password_confirm": "Louis1234",
    "first_name": "Winner",
    "last_name": "Louis"
}

{ 
    "name": "MyCardanoWallet"
}

# POST /auth/wallets/import/mnemonic/
# {
#   "mnemonic_phrase": "word1 word2 ... word24",
#   "name": "Mon Wallet Daedalus",
#   "network": "preview"
# }

# POST /aut/wallets/import/public/
# {
#   "address": "addr_test1qqr585tvlc5yljqsv5a8d6dfxwk8w3m0v3v3v3v3v3v3v3v3v3v3v3v3v3v3v3v3v3v3v3v3v3v3v3v3v3v3vq5v4f2u",
#   "name": "Mon wallet cardano",
#   "network": "preview"
# }

# {
#             "id": 1,
#             "name": "Mon wallet cardano",
#             "payment_address": "addr_test1qp2ljh3an26yalqjp49077c5gvj637nqh4zl8agd0htdwawdj0efyj3gwq5sc343wqs33u6jm59mfu9q260mudkyyt9s9r8f20",
#             "stake_address": "stake_test1urxe8u5jfg58q2gvg6chqggc7dfd6za57zs9d8a7xmzz9jcvdg2aq",
#             "network": "preview",
#             "created_at": "2025-11-27T07:58:19.883295Z"
# }

# POST /auth/wallets/validate/address/
# {
#   "address": "addr_test1q...",
#   "network": "preview"
# }


# POST /auth/wallets/validate/address/
# {
#   "address": "addr_test1q...",
#   "network": "preview"
# }


# POST /api/wallets/validate/mnemonic/
# {
#   "mnemonic_phrase": "word1 word2 ... word24"
# }