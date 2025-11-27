from django.urls import path
from . import views

urlpatterns = [
    # ======================= Authentification =============================

     path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
     path('auth/login/', views.UserLoginView.as_view(), name='login'),
     path('auth/logout/', views.UserLogoutView.as_view(), name='logout'),
     path('auth/profil/', views.UserProfileView.as_view(), name='profile'),

     # ===================== Authentification Wallet ====================================================

    path('auth/wallets/import/mnemonic/', views.ImportWalletMnemonicView.as_view(), name='import_wallet_mnemonic'),
    path('auth/wallets/import/keys/', views.ImportWalletPrivateKeysView.as_view(), name='import_wallet_keys'),
    path('auth/wallets/import/public/', views.ImportWalletPublicView.as_view(), name='import_wallet_public'),
    path('auth/wallets/validate/address/', views.ValidateAddressView.as_view(), name='validate_address'),
    path('auth/wallets/validate/mnemonic/', views.ValidateMnemonicView.as_view(), name='validate_mnemonic'),
    
    # ===================== Wallets ====================================================

    path('wallets/create/', views.CreateWalletView.as_view(), name='create_wallet'),
    path('wallets/list_wallets/', views.UserWalletsView.as_view(), name='user_wallets'),
    path('wallets/wallets/<int:wallet_id>/balance/', views.WalletBalanceView.as_view(), name='wallet_balance'),
    path('wallets/network/info/', views.NetworkInfoView.as_view(), name='network_info'),
    # ===================== Transactions ====================================================
    
    path('api/wallets/<int:wallet_id>/envoi/', views.CreateTransactionView.as_view(), name='send_transaction'),
    path('api/wallets/<int:wallet_id>/historique/', views.TransactionHistoryView.as_view(), name='transaction_history'),
    path('api/transactions/', views.WalletTransactionsView.as_view(), name='all_transactions'),
    path('api/transactions/<str:transaction_hash>/', views.TransactionDetailsView.as_view(), name='transaction_details'),

]