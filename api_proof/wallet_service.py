# api_proof/services.py
from pycardano import *
from django.conf import settings
from django.utils import timezone
import json

class CardanoWalletService:
    
    def __init__(self, network="preview"):
        self.network = network
        self.network_obj = Network.TESTNET
        
        # Configuration Blockfrost pour PREVIEW
        project_id = getattr(settings, 'BLOCKFROST_PROJECT_ID_PREVIEW', 
                           getattr(settings, 'BLOCKFROST_PROJECT_ID', 'preview_project_id'))
        
        base_url = "https://cardano-preview.blockfrost.io/api"
        
        self.context = BlockFrostChainContext(
            project_id=project_id,
            base_url=base_url
        )

    def generate_wallet(self, name=None):
        
        
        try:
            print(" Génération des clés de paiement...")
            payment_signing_key = PaymentSigningKey.generate()
            payment_verification_key = PaymentVerificationKey.from_signing_key(payment_signing_key)

            print(" Génération des clés de stake...")
            stake_signing_key = StakeSigningKey.generate()
            stake_verification_key = StakeVerificationKey.from_signing_key(stake_signing_key)

            # Conversion en hash
            payment_hash = payment_verification_key.hash()
            stake_hash = stake_verification_key.hash()

            print(" Création des adresses PREVIEW...")

            # Adresse de base (payment + stake)
            base_address = Address(payment_hash, stake_hash, self.network_obj)
            
            # Adresse reward (stake seulement)
            reward_address = Address(staking_part=stake_hash, network=self.network_obj)

            wallet_data = {
                'name': name or f"Wallet_Preview_{int(timezone.now().timestamp())}",
                'payment_address': str(base_address),
                'stake_address': str(reward_address),
                
                'payment_signing_key': payment_signing_key.to_cbor(),
                'payment_verification_key': payment_verification_key.to_cbor(),
                'stake_signing_key': stake_signing_key.to_cbor(),
                'stake_verification_key': stake_verification_key.to_cbor(),
                
                'network': self.network,
                'network_type': 'testnet',
                'created_at': str(timezone.now()),
                'is_testnet': True
            }

            print(f" Wallet PREVIEW généré: {wallet_data['payment_address'][:20]}...")
            return wallet_data
            
        except Exception as e:
            print(f" Erreur génération wallet: {str(e)}")
            raise Exception(f"Erreur lors de la génération du wallet: {str(e)}")

    def get_balance(self, address):
    
        
        try:
            address_obj = Address.from_primitive(address)
            utxos = self.context.utxos(str(address_obj))
            
            balance_lovelace = sum(utxo.output.amount.coin for utxo in utxos)
            balance_ada = balance_lovelace / 1_000_000

            return {
                'address': address,
                'balance_ada': balance_ada,
                'balance_lovelace': balance_lovelace,
                'utxo_count': len(utxos),
                'network': self.network,
                'is_testnet': True
            }
        except Exception as e:
            print(f"Erreur récupération solde: {str(e)}")
            return {
                'address': address,
                'balance_ada': 0,
                'balance_lovelace': 0,
                'utxo_count': 0,
                'network': self.network,
                'is_testnet': True,
                'error': 'Adresse non trouvée ou sans fonds'
            }

    def get_test_ada(self, address):
        
        # Fournit des informations pour obtenir de l'ADA de test
    
        faucets = [
            {
                'name': 'Cardano Testnet Faucet',
                'url': 'https://docs.cardano.org/cardano-testnet/tools/faucet',
                'description': 'Faucet officiel Cardano'
            },
            {
                'name': 'Testnets Cardano',
                'url': 'https://testnets.cardano.org/en/testnets/cardano/tools/faucet/',
                'description': 'Portail testnet Cardano'
            }
        ]
        
        return {
            'address': address,
            'network': self.network,
            'faucets': faucets,
            'message': 'Utilisez un faucet pour obtenir de l\'ADA de test',
            'instructions': [
                '1. Allez sur l\'un des faucets listés',
                '2. Collez votre adresse preview',
                '3. Recevez de l\'ADA de test en quelques minutes'
            ]
        }

    def validate_address(self, address):
    
        
        try:
            address_obj = Address.from_primitive(address)
            is_testnet = address_obj.network == Network.TESTNET
            
            return {
                'address': address,
                'is_valid': True,
                'network': 'preview' if is_testnet else 'mainnet',
                'is_testnet': is_testnet,
                'address_type': str(type(address_obj).__name__)
            }
        except Exception as e:
            return {
                'address': address,
                'is_valid': False,
                'error': str(e),
                'is_testnet': False
            }

    def import_wallet_from_keys(self, payment_signing_key_cbor, stake_signing_key_cbor, name=None):
        
        
        try:
            payment_signing_key = PaymentSigningKey.from_cbor(payment_signing_key_cbor)
            payment_verification_key = PaymentVerificationKey.from_signing_key(payment_signing_key)
            
            stake_signing_key = StakeSigningKey.from_cbor(stake_signing_key_cbor)
            stake_verification_key = StakeVerificationKey.from_signing_key(stake_signing_key)
            
            # Recrer les adresses
            payment_hash = payment_verification_key.hash()
            stake_hash = stake_verification_key.hash()
            
            base_address = Address(payment_hash, stake_hash, self.network_obj)
            reward_address = Address(staking_part=stake_hash, network=self.network_obj)
            
            return {
                'name': name or f"Wallet_Importé_{int(timezone.now().timestamp())}",
                'payment_address': str(base_address),
                'stake_address': str(reward_address),
                'payment_signing_key': payment_signing_key_cbor,
                'payment_verification_key': payment_verification_key.to_cbor(),
                'stake_signing_key': stake_signing_key_cbor,
                'stake_verification_key': stake_verification_key.to_cbor(),
                'network': self.network,
                'imported': True,
                'is_testnet': True
            }
            
        except Exception as e:
            raise Exception(f"Erreur import wallet: {str(e)}")

    def get_network_info(self):
    
        
        try:
            tip = self.context.last_block_slot
            return {
                'network': self.network,
                'network_type': 'testnet',
                'last_block_slot': tip.slot,
                'last_block_number': tip.block_number,
                'era': 'Babbage',
                'is_testnet': True,
                'description': 'Réseau de test Cardano Preview'
            }
        except Exception as e:
            return {
                'network': self.network,
                'network_type': 'testnet',
                'is_testnet': True,
                'error': str(e)
            }
        
    def create_transaction(self, from_wallet_data, to_address, amount_ada, metadata=None):
       
        try:
            print(f" Préparation transaction: {amount_ada} ADA vers {to_address[:20]}...")
            
            # Reconstruction des clés
            payment_signing_key = PaymentSigningKey.from_cbor(from_wallet_data['payment_signing_key'])
            payment_verification_key = PaymentVerificationKey.from_signing_key(payment_signing_key)
        
            from_address = Address.from_primitive(from_wallet_data['payment_address'])
            
            # Montant en lovelace
            amount_lovelace = int(amount_ada * 1_000_000)
            
            # Vérifier le solde
            balance_info = self.get_balance(from_wallet_data['payment_address'])
            if balance_info['balance_ada'] < amount_ada:
                raise Exception(f"Solde insuffisant: {balance_info['balance_ada']} ADA disponibles, {amount_ada} ADA requis")
            
            print(" Construction de la transaction...")
            # Construction de la transaction
            builder = TransactionBuilder(self.context)
            
            # Ajouter les UTXOs de l'adresse source
            builder.add_input_address(str(from_address))
            
            # Ajouter la sortie vers l'adresse destination
            builder.add_output(
                TransactionOutput(
                    Address.from_primitive(to_address),
                    Value(coin=amount_lovelace)
                )
            )
            
            # Métadonnées
            if metadata:
                auxiliary_data = AuxiliaryData(metadata=Metadata(metadata))
                builder.auxiliary_data = auxiliary_data
            
            print(" Signature de la transaction...")
            
            signed_tx = builder.build_and_sign(
                [payment_signing_key],
                change_address=from_address
            )
            
            print(" Soumission de la transaction...")

            tx_id = self.context.submit_tx(signed_tx.to_cbor())
            
            transaction_data = {
                'transaction_id': str(tx_id),
                'from_address': str(from_address),
                'to_address': to_address,
                'amount_ada': amount_ada,
                'amount_lovelace': amount_lovelace,
                'fee': signed_tx.transaction_body.fee,
                'status': 'submitted',
                'network': self.network,
                'timestamp': str(timezone.now()),
                'explorer_url': f"https://preview.cexplorer.io/tx/{tx_id}"
            }
            
            print(f" Transaction soumise: {tx_id}")
            return transaction_data
            
        except Exception as e:
            print(f" Erreur transaction: {str(e)}")
            raise Exception(f"Erreur lors de la transaction: {str(e)}")

    def get_transaction_history(self, address, limit=10):
        
        try:
            print(f" Récupération historique pour: {address[:20]}...")
            
            # Utiliser l'API Blockfrost directement pour l'historique
            from blockfrost import BlockFrostApi
            import os
            
            api = BlockFrostApi(
                project_id=getattr(settings, 'BLOCKFROST_PROJECT_ID_PREVIEW', ''),
                base_url="https://cardano-preview.blockfrost.io/api"
            )
            
            # Transactions envoyées
            sent_transactions = api.address_transactions(address, count=limit, order='desc')
            
            utxos = self.context.utxos(address)
            received_transactions = []
            
            for utxo in utxos[:limit]:
                tx_hash = utxo.input.transaction_id
                try:
                    tx_details = api.transaction(tx_hash)
                    received_transactions.append({
                        'tx_hash': tx_hash,
                        'amount_ada': utxo.output.amount.coin / 1_000_000,
                        'block_height': getattr(tx_details, 'block_height', None),
                        'timestamp': getattr(tx_details, 'block_time', None),
                        'direction': 'received'
                    })
                except:
                    continue
            
            # Formater les transactions envoyées
            formatted_sent = []
            for tx in sent_transactions[:limit]:
                formatted_sent.append({
                    'tx_hash': tx.tx_hash,
                    'block_height': tx.block_height,
                    'block_time': tx.block_time,
                    'direction': 'sent'
                })
            
            all_transactions = formatted_sent + received_transactions
            all_transactions.sort(key=lambda x: x.get('block_time', 0) or 0, reverse=True)
            
            return {
                'address': address,
                'transactions': all_transactions[:limit],
                'total_count': len(all_transactions),
                'sent_count': len(formatted_sent),
                'received_count': len(received_transactions)
            }
            
        except Exception as e:
            print(f" Erreur historique: {str(e)}")

            # Retourner une réponse basique si l'API échoue
            return {
                'address': address,
                'transactions': [],
                'total_count': 0,
                'sent_count': 0,
                'received_count': 0,
                'error': 'Historique temporairement indisponible'
            }

    def get_transaction_details(self, transaction_hash):
        
        try:
            from blockfrost import BlockFrostApi
            
            api = BlockFrostApi(
                project_id=getattr(settings, 'BLOCKFROST_PROJECT_ID_PREVIEW', ''),
                base_url="https://cardano-preview.blockfrost.io/api"
            )
            
            tx = api.transaction(transaction_hash)
            utxos = api.transaction_utxos(transaction_hash)
            
            inputs = []
            outputs = []
            
            for input_tx in utxos.inputs:
                inputs.append({
                    'address': input_tx.address,
                    'amount_ada': input_tx.amount[0].quantity / 1_000_000 if input_tx.amount else 0
                })
            
            for output_tx in utxos.outputs:
                outputs.append({
                    'address': output_tx.address,
                    'amount_ada': output_tx.amount[0].quantity / 1_000_000 if output_tx.amount else 0
                })
            
            return {
                'transaction_hash': transaction_hash,
                'block_height': tx.block_height,
                'block_time': tx.block_time,
                'fees_ada': int(tx.fees) / 1_000_000,
                'inputs': inputs,
                'outputs': outputs,
                'explorer_url': f"https://preview.cexplorer.io/tx/{transaction_hash}"
            }
            
        except Exception as e:
            raise Exception(f"Erreur détails transaction: {str(e)}")
        

    def import_wallet_from_mnemonic(self, mnemonic_phrase, name=None):
        

        try:
            from pycardano import mnemonic
            
            print(" Importation depuis mnémonique...")
            
            # Générer les clés depuis le mnémonique
            payment_signing_key = mnemonic.generate_signing_key(mnemonic_phrase)
            payment_verification_key = PaymentVerificationKey.from_signing_key(payment_signing_key)
            
            stake_signing_key = mnemonic.generate_stake_signing_key(mnemonic_phrase)
            stake_verification_key = StakeVerificationKey.from_signing_key(stake_signing_key)
            
            # Créer les adresses
            payment_hash = payment_verification_key.hash()
            stake_hash = stake_verification_key.hash()
            
            base_address = Address(payment_hash, stake_hash, self.network_obj)
            stake_address = Address(staking_part=stake_hash, network=self.network_obj)

            wallet_data = {
                'name': name or f"Wallet_Importé_{int(timezone.now().timestamp())}",
                'payment_address': str(base_address),
                'stake_address': str(stake_address),
                'payment_signing_key': payment_signing_key.to_cbor(),
                'payment_verification_key': payment_verification_key.to_cbor(),
                'stake_signing_key': stake_signing_key.to_cbor(),
                'stake_verification_key': stake_verification_key.to_cbor(),
                'network': self.network,
                'imported': True,
                'import_type': 'mnemonic',
                'is_testnet': True
            }

            print(f" Wallet importé depuis mnémonique: {wallet_data['payment_address'][:20]}...")
            return wallet_data
            
        except Exception as e:
            raise Exception(f"Erreur import mnémonique: {str(e)}")

    def import_wallet_from_private_keys(self, payment_skey_cbor, stake_skey_cbor, name=None):
        
        try:
            print("Importation depuis clés privées...")
            
            
            payment_signing_key = PaymentSigningKey.from_cbor(payment_skey_cbor)
            payment_verification_key = PaymentVerificationKey.from_signing_key(payment_signing_key)
            
            stake_signing_key = StakeSigningKey.from_cbor(stake_skey_cbor)
            stake_verification_key = StakeVerificationKey.from_signing_key(stake_signing_key)
            
            # Créer les adresses
            payment_hash = payment_verification_key.hash()
            stake_hash = stake_verification_key.hash()
            
            base_address = Address(payment_hash, stake_hash, self.network_obj)
            stake_address = Address(staking_part=stake_hash, network=self.network_obj)

            wallet_data = {
                'name': name or f"Wallet_Importé_{int(timezone.now().timestamp())}",
                'payment_address': str(base_address),
                'stake_address': str(stake_address),
                'payment_signing_key': payment_skey_cbor,
                'payment_verification_key': payment_verification_key.to_cbor(),
                'stake_signing_key': stake_skey_cbor,
                'stake_verification_key': stake_verification_key.to_cbor(),
                'network': self.network,
                'imported': True,
                'import_type': 'private_keys',
                'is_testnet': True
            }

            print(f"Wallet importé depuis clés: {wallet_data['payment_address'][:20]}...")
            return wallet_data
            
        except Exception as e:
            raise Exception(f"Erreur import clés: {str(e)}")

    def import_wallet_from_public_address(self, address, name=None):
        
        try:
            print("Importation depuis adresse publique...")
            
            # Valider l'adresse
            address_obj = Address.from_primitive(address)
            is_testnet = address_obj.network == Network.TESTNET
            
            if not is_testnet and self.network == "preview":
                raise Exception("Adresse mainnet incompatible avec le réseau preview")
            
            wallet_data = {
                'name': name or f"Wallet_Lecture_{int(timezone.now().timestamp())}",
                'payment_address': address,
                'stake_address': None,  
                'payment_signing_key': None,
                'payment_verification_key': None,
                'stake_signing_key': None,
                'stake_verification_key': None,
                'network': self.network,
                'imported': True,
                'import_type': 'public_address',
                'read_only': True,
                'is_testnet': is_testnet
            }

            print(f" Wallet lecture seule importé: {address[:20]}...")
            return wallet_data
            
        except Exception as e:
            raise Exception(f"Erreur import adresse: {str(e)}")

    def validate_mnemonic(self, mnemonic_phrase):
        
        try:
            from pycardano import mnemonic
            
        
            words = mnemonic_phrase.strip().split()
            if len(words) not in [12, 15, 24]:
                return {
                    'is_valid': False,
                    'error': 'La phrase mnémonique doit contenir 12, 15 ou 24 mots'
                }
            
            test_key = mnemonic.generate_signing_key(mnemonic_phrase)
            
            return {
                'is_valid': True,
                'word_count': len(words),
                'message': 'Phrase mnémonique valide'
            }
            
        except Exception as e:
            return {
                'is_valid': False,
                'error': f'Phrase mnémonique invalide: {str(e)}'
            }