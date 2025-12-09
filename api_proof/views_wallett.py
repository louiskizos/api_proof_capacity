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
from django.utils import timezone
import hashlib



class ConnectWalletView(APIView):
    
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    
    def post(self, request):
        try:
            if not request.user.is_authenticated:
                return Response({
                    'status': 'error',
                    'message': 'Utilisateur non authentifié'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            data = request.data
            wallet_connection_data = data.get('wallet_connection_data')
            provider = data.get('provider', 'unknown')
            
            if not wallet_connection_data:
                return Response({
                    'status': 'error',
                    'message': 'Données de connexion au wallet manquantes'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Extraire les données du wallet
            payment_address = wallet_connection_data.get('payment_address')
            stake_address = wallet_connection_data.get('stake_address')
            network_id = wallet_connection_data.get('network_id')
            wallet_name = wallet_connection_data.get('name', f'Wallet {provider}')
            
            if not payment_address:
                return Response({
                    'status': 'error',
                    'message': 'Adresse de paiement requise'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Mapper network_id au nom du réseau
            network_mapping = {
                0: 'mainnet',
                1: 'testnet',
                2: 'preview',
                3: 'preprod'
            }
            
            network = network_mapping.get(network_id, 'preview')
            
            # Vérifier si le wallet est déjà connecté pour cet utilisateur
            existing_wallet = CardanoWallet.objects.filter(
                payment_address=payment_address,
                user=request.user
            ).first()
            
            if existing_wallet:
                # Mettre à jour les informations si nécessaire
                existing_wallet.name = wallet_name
                existing_wallet.network = network
                existing_wallet.last_connected = timezone.now()
                existing_wallet.save()
                
                return Response({
                    'status': 'success',
                    'message': 'Wallet déjà connecté, informations mises à jour',
                    'wallet': {
                        'id': existing_wallet.id,
                        'name': existing_wallet.name,
                        'payment_address': existing_wallet.payment_address,
                        'stake_address': existing_wallet.stake_address,
                        'network': existing_wallet.network,
                        'is_connected': True,
                        'provider': provider,
                        'type': 'external_wallet'
                    }
                }, status=status.HTTP_200_OK)
            
            # Créer un nouveau wallet connecté
            wallet = CardanoWallet.objects.create(
                user=request.user,
                name=wallet_name,
                payment_address=payment_address,
                stake_address=stake_address or '',
                payment_signing_key='',  # Pas stocké pour les wallets externes
                payment_verification_key='',
                stake_signing_key='',
                stake_verification_key='',
                network=network,
                wallet_type='external',
                provider=provider,
                is_connected=True,
                last_connected=timezone.now()
            )
            
            return Response({
                'status': 'success',
                'message': 'Wallet externe connecté avec succès',
                'wallet': {
                    'id': wallet.id,
                    'name': wallet.name,
                    'payment_address': wallet.payment_address,
                    'stake_address': wallet.stake_address,
                    'network': wallet.network,
                    'is_connected': True,
                    'provider': provider,
                    'type': 'external_wallet',
                    'created_at': wallet.created_at
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Erreur lors de la connexion du wallet: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, wallet_id=None):
        """
        Déconnecter un wallet externe
        """
        try:
            if wallet_id:
                # Déconnecter un wallet spécifique
                wallet = CardanoWallet.objects.get(
                    id=wallet_id,
                    user=request.user,
                    wallet_type='external'
                )
                wallet.is_connected = False
                wallet.last_connected = timezone.now()
                wallet.save()
                
                return Response({
                    'status': 'success',
                    'message': 'Wallet déconnecté avec succès',
                    'wallet_id': wallet_id
                }, status=status.HTTP_200_OK)
            else:
                # Déconnecter tous les wallets externes
                wallets = CardanoWallet.objects.filter(
                    user=request.user,
                    wallet_type='external',
                    is_connected=True
                )
                
                for wallet in wallets:
                    wallet.is_connected = False
                    wallet.last_connected = timezone.now()
                    wallet.save()
                
                return Response({
                    'status': 'success',
                    'message': f'Tous les wallets externes déconnectés ({wallets.count()})'
                }, status=status.HTTP_200_OK)
                
        except CardanoWallet.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Wallet non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Erreur lors de la déconnexion: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class ExternalWalletBalanceView(APIView):
    """
    Obtenir le solde d'un wallet externe connecté
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, wallet_id):
        try:
            wallet = CardanoWallet.objects.get(
                id=wallet_id,
                user=request.user,
                wallet_type='external'
            )
            
            # Utiliser le service pour obtenir le solde
            service = CardanoWalletService(network=wallet.network)
            balance_info = service.get_balance(wallet.payment_address)
            
            return Response({
                'status': 'success',
                'wallet_id': wallet.id,
                'wallet_name': wallet.name,
                'payment_address': wallet.payment_address,
                'balance': balance_info,
                'last_updated': timezone.now()
            })
            
        except CardanoWallet.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Wallet externe non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Erreur lors de la récupération du solde: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class GetConnectedWalletsView(APIView):
    """
    Obtenir la liste des wallets externes connectés
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            connected_wallets = CardanoWallet.objects.filter(
                user=request.user,
                wallet_type='external',
                is_connected=True
            ).order_by('-last_connected')
            
            wallets_data = []
            for wallet in connected_wallets:
                wallets_data.append({
                    'id': wallet.id,
                    'name': wallet.name,
                    'payment_address': wallet.payment_address,
                    'stake_address': wallet.stake_address,
                    'network': wallet.network,
                    'provider': wallet.provider,
                    'is_connected': wallet.is_connected,
                    'last_connected': wallet.last_connected,
                    'created_at': wallet.created_at,
                    'type': 'external_wallet'
                })
            
            return Response({
                'status': 'success',
                'connected_wallets': wallets_data,
                'count': len(wallets_data)
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Erreur: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class SignMessageView(APIView):
    """
    Signer un message avec un wallet externe connecté
    (Dans un vrai scénario, cette signature se ferait côté client)
    """
    
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser]
    
    def post(self, request, wallet_id):
        try:
            wallet = CardanoWallet.objects.get(
                id=wallet_id,
                user=request.user,
                wallet_type='external'
            )
            
            message = request.data.get('message')
            if not message:
                return Response({
                    'status': 'error',
                    'message': 'Message à signer requis'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Dans une vraie implémentation, cette signature se ferait côté client
            # via l'API de navigateur Cardano. Ici, nous simulons l'idée.
            
            # Générer un hash du message pour la simulation
            message_hash = hashlib.sha256(message.encode()).hexdigest()
            
            # Pour un wallet externe, nous ne pouvons pas signer côté serveur
            # Nous retournons donc les informations nécessaires pour signer côté client
            return Response({
                'status': 'success',
                'message': 'Signature à effectuer côté client avec le wallet externe',
                'signing_info': {
                    'wallet_address': wallet.payment_address,
                    'message': message,
                    'message_hash': message_hash,
                    'network': wallet.network,
                    'provider': wallet.provider,
                    'instructions': {
                        'nami': 'Utiliser window.cardano.nami.signMessage()',
                        'eternl': 'Utiliser window.cardano.eternl.signMessage()',
                        'flint': 'Utiliser window.cardano.flint.signMessage()'
                    }
                }
            })
            
        except CardanoWallet.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Wallet externe non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Erreur lors de la préparation de la signature: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class VerifyWalletOwnershipView(APIView):
    """
    Vérifier la possession d'un wallet externe via signature
    """
    
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser]
    
    def post(self, request):
        try:
            data = request.data
            wallet_address = data.get('wallet_address')
            signature = data.get('signature')
            signed_message = data.get('signed_message')
            original_message = data.get('original_message')
            
            if not all([wallet_address, signature, signed_message, original_message]):
                return Response({
                    'status': 'error',
                    'message': 'Tous les champs sont requis pour la vérification'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Ici, vous intégreriez une logique de vérification de signature réelle
            # Pour l'exemple, nous simulons une vérification réussie
            
            # Récupérer le wallet correspondant
            wallet = CardanoWallet.objects.filter(
                payment_address=wallet_address,
                user=request.user,
                wallet_type='external'
            ).first()
            
            if not wallet:
                return Response({
                    'status': 'error',
                    'message': 'Wallet non trouvé pour cet utilisateur'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Simulation de vérification (à remplacer par une vraie vérification)
            is_verified = True  # Cette valeur serait déterminée par la vérification réelle
            
            if is_verified:
                wallet.is_verified = True
                wallet.verified_at = timezone.now()
                wallet.save()
                
                return Response({
                    'status': 'success',
                    'message': 'Propriété du wallet vérifiée avec succès',
                    'wallet': {
                        'id': wallet.id,
                        'name': wallet.name,
                        'address': wallet.payment_address,
                        'is_verified': True,
                        'verified_at': wallet.verified_at
                    }
                })
            else:
                return Response({
                    'status': 'error',
                    'message': 'Échec de la vérification de la signature'
                }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Erreur lors de la vérification: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)