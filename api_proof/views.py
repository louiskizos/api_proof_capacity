from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth import get_user_model
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserSerializer
from .wallet_service import CardanoWalletService
from .models import CardanoWallet, CardanoTransaction
from .models import CardanoNFT, CertificationNFT, NFTPolicy
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser



User = get_user_model()

class UserRegistrationView(APIView):

    permission_classes = [permissions.AllowAny]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Connecter l'utilisateur automatiquement
            login(request, user)
            
            return Response({
                'status': 'success',
                'message': 'Utilisateur créé avec succès',
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'status': 'error',
            'message': 'Erreur de validation',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class UserLoginView(APIView):

    permission_classes = [permissions.AllowAny]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            
            return Response({
                'status': 'success',
                'message': 'Connexion réussie',
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'status': 'error',
            'message': 'Identifiants invalides',
            'errors': serializer.errors
        }, status=status.HTTP_401_UNAUTHORIZED)

class UserLogoutView(APIView):

    parser_classes = [JSONParser, FormParser, MultiPartParser]
    def post(self, request):
        logout(request)
        return Response({
            'status': 'success',
            'message': 'Déconnexion réussie'
        }, status=status.HTTP_200_OK)

class UserProfileView(APIView):
    def get(self, request):
        return Response({
            'status': 'success',
            'user': UserSerializer(request.user).data
        })

class CreateWalletView(APIView):
    
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    def post(self, request):
        try:
            if not request.user.is_authenticated:
                return Response({
                    'status': 'error',
                    'message': 'Utilisateur non authentifié'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            data = request.data
            name = data.get('name')
            
            wallet_service = CardanoWalletService()
            wallet_data = wallet_service.generate_wallet(name=name)
            
            wallet = CardanoWallet.objects.create(
                user=request.user,
                name=wallet_data['name'],
                payment_address=wallet_data['payment_address'],
                stake_address=wallet_data['stake_address'],
                payment_signing_key=wallet_data['payment_signing_key'],
                payment_verification_key=wallet_data['payment_verification_key'],
                stake_signing_key=wallet_data['stake_signing_key'],
                stake_verification_key=wallet_data['stake_verification_key'],
                network=wallet_data['network']
            )
            
            return Response({
                'status': 'success',
                'message': 'Wallet créé avec succès',
                'wallet': {
                    'id': wallet.id,
                    'name': wallet.name,
                    'payment_address': wallet.payment_address,
                    'stake_address': wallet.stake_address,
                    'network': wallet.network
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Erreur lors de la création du wallet: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)



class WalletBalanceView(APIView):

    
    def get(self, request, wallet_id):
        try:
            wallet = CardanoWallet.objects.get(id=wallet_id, user=request.user)
            service = CardanoWalletService(network=wallet.network)
            balance = service.get_balance(wallet.payment_address)
            
            return Response({
                'status': 'success',
                'wallet_id': wallet.id,
                'balance': balance
            })
        except CardanoWallet.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Wallet non trouvé'
            }, status=404)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Erreur: {str(e)}'
            }, status=400)

class UserWalletsView(APIView):
    
    def get(self, request):

        wallets = CardanoWallet.objects.filter(user=request.user)
        wallets_data = []
        
        for wallet in wallets:
            wallets_data.append({
                'id': wallet.id,
                'name': wallet.name,
                'payment_address': wallet.payment_address,
                'stake_address': wallet.stake_address,
                'network': wallet.network,
                'created_at': wallet.created_at
            })
        
        return Response({
            'status': 'success',
            'wallets': wallets_data,
            'count': len(wallets_data)
        })

class NetworkInfoView(APIView):

    def get(self, request):
        try:
            service = CardanoWalletService()
            network_info = service.get_network_info()
            
            return Response({
                'status': 'success',
                'network_info': network_info
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Erreur: {str(e)}'
            }, status=400)
        

class CreateTransactionView(APIView):
    
    # Crée et envoie une transaction
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    def post(self, request, wallet_id):
        try:
            
            wallet = CardanoWallet.objects.get(id=wallet_id, user=request.user)
            
            to_address = request.data.get('to_address')
            amount_ada = float(request.data.get('amount_ada'))
            metadata = request.data.get('metadata')
            
            if not to_address or amount_ada <= 0:
                return Response({
                    'status': 'error',
                    'message': 'Adresse destination et montant valide requis'
                }, status=400)
            
            
            wallet_data = {
                'payment_address': wallet.payment_address,
                'payment_signing_key': wallet.payment_signing_key,
                'stake_signing_key': wallet.stake_signing_key
            }
            

            service = CardanoWalletService(network=wallet.network)
            transaction_result = service.create_transaction(
                from_wallet_data=wallet_data,
                to_address=to_address,
                amount_ada=amount_ada,
                metadata=metadata
            )
            
            transaction = CardanoTransaction.objects.create(
                wallet=wallet,
                transaction_hash=transaction_result['transaction_id'],
                from_address=transaction_result['from_address'],
                to_address=transaction_result['to_address'],
                amount_ada=transaction_result['amount_ada'],
                amount_lovelace=transaction_result['amount_lovelace'],
                fee_lovelace=transaction_result['fee'],
                metadata=metadata,
                status='submitted'
            )
            
            return Response({
                'status': 'success',
                'message': 'Transaction créée avec succès',
                'transaction': {
                    'id': transaction.id,
                    'transaction_hash': transaction.transaction_hash,
                    'from_address': transaction.from_address,
                    'to_address': transaction.to_address,
                    'amount_ada': float(transaction.amount_ada),
                    'fee_ada': transaction.fee_lovelace / 1_000_000,
                    'status': transaction.status,
                    'explorer_url': transaction_result['explorer_url'],
                    'created_at': transaction.created_at
                }
            }, status=201)
            
        except CardanoWallet.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Wallet non trouvé'
            }, status=404)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Erreur lors de la transaction: {str(e)}'
            }, status=400)



class TransactionHistoryView(APIView):
    

    def get(self, request, wallet_id):
        try:
            wallet = CardanoWallet.objects.get(id=wallet_id, user=request.user)
            limit = int(request.GET.get('limit', 10))
            
            service = CardanoWalletService(network=wallet.network)
            history = service.get_transaction_history(wallet.payment_address, limit=limit)
            
            return Response({
                'status': 'success',
                'wallet_id': wallet.id,
                'history': history
            })
            
        except CardanoWallet.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Wallet non trouvé'
            }, status=404)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Erreur historique: {str(e)}'
            }, status=400)

class TransactionDetailsView(APIView):
    
    def get(self, request, transaction_hash):

        try:
            # Trouver la transaction dans la base
            transaction = CardanoTransaction.objects.get(
                transaction_hash=transaction_hash,
                wallet__user=request.user
            )
            
            service = CardanoWalletService(network=transaction.wallet.network)
            details = service.get_transaction_details(transaction_hash)
            
            return Response({
                'status': 'success',
                'transaction': {
                    'id': transaction.id,
                    'details': details
                }
            })
            
        except CardanoTransaction.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Transaction non trouvée'
            }, status=404)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Erreur détails: {str(e)}'
            }, status=400)

class WalletTransactionsView(APIView):
    
    def get(self, request):
        try:
            wallets = CardanoWallet.objects.filter(user=request.user)
            transactions = CardanoTransaction.objects.filter(wallet__in=wallets).order_by('-created_at')
            
            transactions_data = []
            for tx in transactions:
                transactions_data.append({
                    'id': tx.id,
                    'transaction_hash': tx.transaction_hash,
                    'wallet_name': tx.wallet.name,
                    'from_address': tx.from_address,
                    'to_address': tx.to_address,
                    'amount_ada': float(tx.amount_ada),
                    'status': tx.status,
                    'created_at': tx.created_at,
                    'explorer_url': f"https://preview.cexplorer.io/tx/{tx.transaction_hash}"
                })
            
            return Response({
                'status': 'success',
                'transactions': transactions_data,
                'total_count': len(transactions_data)
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Erreur: {str(e)}'
            }, status=400)
        

# debut de la connexion wallet

class ImportWalletMnemonicView(APIView):
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    def post(self, request):
        try:
            if not request.user.is_authenticated:
                return Response({
                    'status': 'error',
                    'message': 'Utilisateur non authentifié'
                }, status=401)
            
            mnemonic_phrase = request.data.get('mnemonic_phrase')
            name = request.data.get('name', 'Wallet Importé')
            network = request.data.get('network', 'preview')
            
            if not mnemonic_phrase:
                return Response({
                    'status': 'error',
                    'message': 'Phrase mnémonique requise'
                }, status=400)
            
            # Valider la phrase mnémonique
            service = CardanoWalletService(network=network)
            validation = service.validate_mnemonic(mnemonic_phrase)
            
            if not validation['is_valid']:
                return Response({
                    'status': 'error',
                    'message': validation['error']
                }, status=400)
            

            wallet_data = service.import_wallet_from_mnemonic(mnemonic_phrase, name=name)
            
            wallet = CardanoWallet.objects.create(
                user=request.user,
                name=wallet_data['name'],
                payment_address=wallet_data['payment_address'],
                stake_address=wallet_data['stake_address'],
                payment_signing_key=wallet_data['payment_signing_key'],
                payment_verification_key=wallet_data['payment_verification_key'],
                stake_signing_key=wallet_data['stake_signing_key'],
                stake_verification_key=wallet_data['stake_verification_key'],
                network=wallet_data['network']
            )
            
            return Response({
                'status': 'success',
                'message': 'Wallet importé avec succès depuis mnémonique',
                'wallet': {
                    'id': wallet.id,
                    'name': wallet.name,
                    'payment_address': wallet.payment_address,
                    'stake_address': wallet.stake_address,
                    'network': wallet.network,
                    'imported': True,
                    'import_type': 'mnemonic'
                }
            }, status=201)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Erreur import mnémonique: {str(e)}'
            }, status=400)

class ImportWalletPrivateKeysView(APIView):
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    def post(self, request):
        try:
            if not request.user.is_authenticated:
                return Response({
                    'status': 'error',
                    'message': 'Utilisateur non authentifié'
                }, status=401)
            
            payment_skey = request.data.get('payment_signing_key')
            stake_skey = request.data.get('stake_signing_key')
            name = request.data.get('name', 'Wallet Importé')
            network = request.data.get('network', 'preview')
            
            if not payment_skey or not stake_skey:
                return Response({
                    'status': 'error',
                    'message': 'Clés de signature requises'
                }, status=400)
            
            service = CardanoWalletService(network=network)
            wallet_data = service.import_wallet_from_private_keys(
                payment_skey_cbor=payment_skey,
                stake_skey_cbor=stake_skey,
                name=name
            )
            
            wallet = CardanoWallet.objects.create(
                user=request.user,
                name=wallet_data['name'],
                payment_address=wallet_data['payment_address'],
                stake_address=wallet_data['stake_address'],
                payment_signing_key=wallet_data['payment_signing_key'],
                payment_verification_key=wallet_data['payment_verification_key'],
                stake_signing_key=wallet_data['stake_signing_key'],
                stake_verification_key=wallet_data['stake_verification_key'],
                network=wallet_data['network']
            )
            
            return Response({
                'status': 'success',
                'message': 'Wallet importé avec succès depuis clés privées',
                'wallet': {
                    'id': wallet.id,
                    'name': wallet.name,
                    'payment_address': wallet.payment_address,
                    'stake_address': wallet.stake_address,
                    'network': wallet.network,
                    'imported': True,
                    'import_type': 'private_keys'
                }
            }, status=201)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Erreur import clés: {str(e)}'
            }, status=400)



class ImportWalletPublicView(APIView):
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    def post(self, request):
        try:
            if not request.user.is_authenticated:
                return Response({
                    'status': 'error',
                    'message': 'Utilisateur non authentifié'
                }, status=401)
            
            address = request.data.get('address')
            name = request.data.get('name', 'Wallet Lecture')
            network = request.data.get('network', 'preview')
            
            if not address:
                return Response({
                    'status': 'error',
                    'message': 'Adresse requise'
                }, status=400)
            
            existing_wallet = CardanoWallet.objects.filter(
                payment_address=address,
                user=request.user
            ).first()
            
            if existing_wallet:
                return Response({
                    'status': 'error',
                    'message': 'Cette adresse est déjà importée dans votre compte',
                    'existing_wallet': {
                        'id': existing_wallet.id,
                        'name': existing_wallet.name,
                        'payment_address': existing_wallet.payment_address
                    }
                }, status=400)
            
            service = CardanoWalletService(network=network)
            wallet_data = service.import_wallet_from_public_address(address, name=name)
            
            wallet = CardanoWallet.objects.create(
                user=request.user,
                name=wallet_data['name'],
                payment_address=wallet_data['payment_address'],
                stake_address=wallet_data['stake_address'] or '',
                payment_signing_key='',
                payment_verification_key='',
                stake_signing_key='',
                stake_verification_key='',
                network=wallet_data['network']
            )
            
            return Response({
                'status': 'success',
                'message': 'Wallet importé en mode lecture seule',
                'wallet': {
                    'id': wallet.id,
                    'name': wallet.name,
                    'payment_address': wallet.payment_address,
                    'stake_address': wallet.stake_address,
                    'network': wallet.network,
                    'imported': True,
                    'read_only': True,
                    'import_type': 'public_address'
                }
            }, status=201)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Erreur import adresse: {str(e)}'
            }, status=400)        

class ValidateAddressView(APIView):
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    def post(self, request):
        try:
            address = request.data.get('address')
            network = request.data.get('network', 'preview')
            
            if not address:
                return Response({
                    'status': 'error',
                    'message': 'Adresse requise'
                }, status=400)
            
            service = CardanoWalletService(network=network)
            validation = service.validate_address(address)
            
            return Response({
                'status': 'success',
                'validation': validation
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Erreur validation: {str(e)}'
            }, status=400)

class ValidateMnemonicView(APIView):
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    def post(self, request):
        try:
            mnemonic_phrase = request.data.get('mnemonic_phrase')
            
            if not mnemonic_phrase:
                return Response({
                    'status': 'error',
                    'message': 'Phrase mnémonique requise'
                }, status=400)
            
            service = CardanoWalletService()
            validation = service.validate_mnemonic(mnemonic_phrase)
            
            return Response({
                'status': 'success' if validation['is_valid'] else 'error',
                'validation': validation
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Erreur validation: {str(e)}'
            }, status=400)
        

