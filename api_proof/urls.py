from django.urls import path
from . import views, views_nft, views_video_certification, views_wallett

urlpatterns = [

    path('', views.UserWalletsView.as_view(), name='user_wallets'),
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
    path('wallets/wallets/<int:wallet_id>/balance/', views.WalletBalanceView.as_view(), name='wallet_balance'),
    path('wallets/network/info/', views.NetworkInfoView.as_view(), name='network_info'),
    # ===================== Transactions ====================================================
    
    path('api/wallets/<int:wallet_id>/envoi/', views.CreateTransactionView.as_view(), name='send_transaction'),
    path('api/wallets/<int:wallet_id>/historique/', views.TransactionHistoryView.as_view(), name='transaction_history'),
    path('api/transactions/', views.WalletTransactionsView.as_view(), name='all_transactions'),
    path('api/transactions/<str:transaction_hash>/', views.TransactionDetailsView.as_view(), name='transaction_details'),
    # ===================== NFT ====================================================
    path('nft/<int:wallet_id>/nfts/policy/', views_nft.CreateNFTPolicyView.as_view(), name='create-policy'),
    path('nft/<int:wallet_id>/nfts/mint/', views_nft.MintNFTView.as_view(), name='mint-nft'),
    path('nft/<int:wallet_id>/nfts/certification/', views_nft.CreateCertificationNFTView.as_view(), name='create-certification'),
    path('nft/<int:wallet_id>/nfts/', views_nft.GetWalletNFTsView.as_view(), name='get-nfts'),
    path('nft/certifications/verify/', views_nft.VerifyCertificationView.as_view(), name='verify-certification'),

    # ===================== Video Courses ====================================================
    
    path('video/track/', views_video_certification.TrackVideoViewAPI.as_view(), name='track-video'),
    path('courses/<int:course_id>/progress/', views_video_certification.GetCourseProgressAPI.as_view(), name='course-progress'),
    path('quizzes/<int:quiz_id>/take/', views_video_certification.TakeQuizAPI.as_view(), name='take-quiz'),
    path('courses/<int:course_id>/check-eligibility/', views_video_certification.CheckCertificationEligibilityAPI.as_view(), name='check-cert-eligibility'),
    path('courses/<int:course_id>/request-certification/', views_video_certification.RequestCertificationAPI.as_view(), name='request-certification'),
    path('my-certificates/', views_video_certification.MyCertificatesAPI.as_view(), name='my-certificates'),
    path('courses/catalog/', views_video_certification.CourseCatalogAPI.as_view(), name='course-catalog'),

]