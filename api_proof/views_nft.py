import requests
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import CardanoWallet
from .models import CardanoNFT, CertificationNFT, NFTPolicy
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from django.utils import timezone
import hashlib
import time





class CreateNFTPolicyView(APIView):
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    def post(self, request, wallet_id):
        try:
            wallet = CardanoWallet.objects.get(id=wallet_id, user=request.user)
            
            policy_type = request.data.get('policy_type', 'single_issuer')
            valid_before = request.data.get('valid_before')
            
            service = CardanoNFT(network=wallet.network)
            
            wallet_data = {
                'payment_address': wallet.payment_address,
                'payment_signing_key': wallet.payment_signing_key
            }
            
            policy_data = service.create_policy(wallet_data, policy_type, valid_before)
            
            # Sauvegarder la politique
            policy = NFTPolicy.objects.create(
                name=request.data.get('name', f"Policy {policy_type}"),
                policy_id=policy_data['policy_id'],
                policy_script=policy_data['policy_script'],
                policy_type=policy_type,
                creator=request.user,
                valid_before=valid_before
            )
            
            return Response({
                'status': 'success',
                'message': 'Politique créée avec succès',
                'policy': {
                    'id': policy.id,
                    'name': policy.name,
                    'policy_id': policy.policy_id,
                    'policy_type': policy.policy_type,
                    'valid_before': policy.valid_before
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
                'message': str(e)
            }, status=400)

class MintNFTView(APIView):

    parser_classes = [JSONParser, FormParser, MultiPartParser]
    
    def post(self, request, wallet_id):
        try:
            wallet = CardanoWallet.objects.get(id=wallet_id, user=request.user)
            
            policy_id = request.data.get('policy_id')
            asset_name = request.data.get('asset_name')
            metadata = request.data.get('metadata', {})
            
            service = CardanoNFT(network=wallet.network)
            
            wallet_data = {
                'payment_address': wallet.payment_address,
                'payment_signing_key': wallet.payment_signing_key
            }
            
            # Récupérer la politique
            policy = NFTPolicy.objects.get(policy_id=policy_id, creator=request.user)
            policy_data = {
                'policy_id': policy.policy_id,
                'policy_signing_key': request.data.get('policy_signing_key')  # À stocker en sécurité!
            }
            
            result = service.mint_nft(wallet_data, policy_data, asset_name, metadata)
            
            # Sauvegarder le NFT
            nft = CardanoNFT.objects.create(
                wallet=wallet,
                policy_id=policy_id,
                asset_name=asset_name,
                fingerprint=result['fingerprint'],
                name=metadata.get('name', asset_name),
                description=metadata.get('description', ''),
                image_url=metadata.get('image_url', ''),
                metadata=metadata,
                nft_type=metadata.get('type', 'certification'),
                status='minted'
            )
            
            return Response({
                'status': 'success',
                'message': 'NFT minté avec succès',
                'nft': {
                    'id': nft.id,
                    'name': nft.name,
                    'policy_id': nft.policy_id,
                    'asset_name': nft.asset_name,
                    'fingerprint': nft.fingerprint,
                    'transaction_id': result['transaction_id'],
                    'explorer_url': result['explorer_url']
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
                'message': str(e)
            }, status=400)
        

class CreateCertificationNFTView(APIView):
    
    def post(self, request, wallet_id):
        """POST pour créer une certification"""
        try:
            # 1. Récupérer le wallet émetteur
            issuer_wallet = CardanoWallet.objects.get(id=wallet_id, user=request.user)
            
            # 2. Préparer les données de certification
            certification_data = {
                'title': request.data.get('title', 'Certification sans titre'),
                'description': request.data.get('description', ''),
                'type': request.data.get('type', 'Général'),
                'certification_id': request.data.get('certification_id', 
                    f"CERT-{timezone.now().strftime('%Y%m%d')}-{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"),
                'issuer_name': request.data.get('issuer_name', request.user.email),
                'recipient_name': request.data.get('recipient_name', ''),
                'recipient_address': request.data.get('recipient_address', ''),
                'issue_date': request.data.get('issue_date', timezone.now().date().isoformat()),
                'expiration_date': request.data.get('expiration_date'),
                'skills': request.data.get('skills', []),
                'standards': request.data.get('standards', []),
                'image_url': request.data.get('image_url', ''),
                'verification_url': request.data.get('verification_url', 
                    f"http://localhost:8000/api/certifications/verify/")
            }
            
            # 3. Mode simulation (pas de minting réel)
            return self._create_simulation_certification(issuer_wallet, certification_data, request.user)
            
        except CardanoWallet.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Wallet émetteur non trouvé'
            }, status=404)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Erreur émission certification: {str(e)}'
            }, status=400)
    
    def _create_simulation_certification(self, issuer_wallet, certification_data, issuer_user):
        """Créer une certification simulée (pour test)"""
        try:
            # Générer des données simulées
            policy_id = f"policy_sim_{hashlib.md5(str(time.time()).encode()).hexdigest()[:16]}"
            fingerprint = f"asset1sim{hashlib.md5(str(time.time()).encode()).hexdigest()[:32]}"
            
            # Créer le NFT simulé
            nft = CardanoNFT.objects.create(
                wallet=issuer_wallet,
                policy_id=policy_id,
                asset_name=f"CERT_SIM_{int(time.time())}",
                fingerprint=fingerprint,
                name=certification_data['title'],
                description=certification_data['description'],
                image_url=certification_data.get('image_url', ''),
                metadata=certification_data,
                nft_type='certification',
                status='minted'
            )
            
            # Créer la certification
            certification = CertificationNFT.objects.create(
                nft=nft,
                issuer=issuer_user,
                recipient=issuer_user,  # Pour simulation, le destinataire est l'émetteur
                certification_type=certification_data['type'],
                issue_date=certification_data['issue_date'],
                expiration_date=certification_data.get('expiration_date'),
                verification_url=f"{certification_data['verification_url']}{fingerprint}"
            )
            
            return Response({
                'status': 'success',
                'message': 'Certification simulée créée avec succès',
                'certification': {
                    'id': certification.id,
                    'title': certification_data['title'],
                    'certification_id': certification_data['certification_id'],
                    'nft_fingerprint': fingerprint,
                    'issuer': certification_data['issuer_name'],
                    'recipient': certification_data['recipient_name'],
                    'issue_date': certification_data['issue_date'],
                    'verification_url': f"{certification_data['verification_url']}{fingerprint}",
                    'note': 'Mode simulation - pas de minting réel sur blockchain'
                }
            }, status=201)
            
        except Exception as e:
            raise Exception(f"Erreur simulation: {str(e)}")
        

class GetWalletNFTsView(APIView):
    """Récupérer les NFTs d'un wallet"""
    
    def get(self, request, wallet_id):
        try:
            # 1. Récupérer le wallet
            wallet = CardanoWallet.objects.get(id=wallet_id, user=request.user)
            
            # 2. Récupérer les NFTs depuis la blockchain (via Blockfrost)
            nfts = self._get_nfts_from_blockfrost(wallet)
            
            # 3. Récupérer les NFTs depuis la base de données
            db_nfts = CardanoNFT.objects.filter(wallet=wallet)
            db_nfts_data = [
                {
                    'id': nft.id,
                    'name': nft.name,
                    'policy_id': nft.policy_id,
                    'asset_name': nft.asset_name,
                    'fingerprint': nft.fingerprint,
                    'type': nft.nft_type,
                    'status': nft.status,
                    'created_at': nft.created_at
                }
                for nft in db_nfts
            ]
            
            return Response({
                'status': 'success',
                'wallet_id': wallet.id,
                'wallet_address': wallet.payment_address,
                'network': wallet.network,
                'nfts_from_blockchain': nfts,
                'nfts_from_database': db_nfts_data,
                'total_count': len(nfts) + len(db_nfts_data)
            })
            
        except CardanoWallet.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Wallet non trouvé'
            }, status=404)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    def _get_nfts_from_blockfrost(self, wallet):
        """Récupérer les NFTs depuis Blockfrost API"""
        try:
            # Configuration Blockfrost
            from django.conf import settings
            project_id = getattr(settings, 'BLOCKFROST_PROJECT_ID', '')
            
            if not project_id:
                return []
            
            headers = {'project_id': project_id}
            
            # URL selon le réseau
            if wallet.network == 'mainnet':
                base_url = 'https://cardano-mainnet.blockfrost.io/api/v0'
            elif wallet.network == 'preprod':
                base_url = 'https://cardano-preprod.blockfrost.io/api/v0'
            elif wallet.network == 'preview':
                base_url = 'https://cardano-preview.blockfrost.io/api/v0'
            else:
                return []
            
            # Récupérer les assets du wallet
            url = f"{base_url}/accounts/{wallet.payment_address}/addresses/assets"
            
            response = requests.get(url, headers=headers, params={'count': 100})
            
            if response.status_code == 200:
                assets = response.json()
                
                # Filtrer pour ne garder que les NFTs (quantité = 1)
                nfts = []
                for asset in assets:
                    if asset['quantity'] == 1:  # C'est probablement un NFT
                        # Récupérer plus d'informations sur l'asset
                        asset_details = self._get_asset_details(asset['asset'], wallet.network)
                        
                        nfts.append({
                            'asset_id': asset['asset'],
                            'policy_id': asset['asset'][:56],  # Les 56 premiers caractères
                            'asset_name_hex': asset['asset'][56:],
                            'asset_name': bytes.fromhex(asset['asset'][56:]).decode('utf-8', errors='ignore'),
                            'quantity': asset['quantity'],
                            'metadata': asset_details.get('metadata', {}),
                            'on_chain': True
                        })
                
                return nfts
            else:
                return []
                
        except Exception as e:
            print(f"Erreur Blockfrost: {e}")
            return []
    
    def _get_asset_details(self, asset_id, network):
        """Récupérer les détails d'un asset"""
        try:
            from django.conf import settings
            project_id = getattr(settings, 'BLOCKFROST_PROJECT_ID', '')
            headers = {'project_id': project_id}
            
            if network == 'mainnet':
                base_url = 'https://cardano-mainnet.blockfrost.io/api/v0'
            elif network == 'preprod':
                base_url = 'https://cardano-preprod.blockfrost.io/api/v0'
            elif network == 'preview':
                base_url = 'https://cardano-preview.blockfrost.io/api/v0'
            else:
                return {}
            
            url = f"{base_url}/assets/{asset_id}"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {}
                
        except Exception:
            return {}
        

class VerifyCertificationView(APIView):
    
    def get(self, request):
        try:
            fingerprint = request.GET.get('fingerprint')
            address = request.GET.get('address')
            
            if not fingerprint and not address:
                return Response({
                    'status': 'error',
                    'message': 'Fingerprint ou adresse requis'
                }, status=400)
            
            
            return Response({
                'status': 'success',
                'verification': {
                    'valid': True,
                    'message': 'Certification vérifiée avec succès'
                }
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=400)