import json
import hashlib
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
import ipfshttpclient
from eth_account import Account
from base64 import b64encode
from datetime import datetime, timedelta
from base64 import b64encode, b64decode


#dependances
import constante

def ipfs_add(json_data) :
	client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https', chunk_size=100000)
	response=client.add_json(json_data)
	response2=client.pin.add(response)
	return response

def ipfs_get(ipfs_hash) :
	client = ipfshttpclient.connect('/dns/ipfs.infura.io/tcp/5001/https')
	return(client.get_json(ipfs_hash))
	
def get_username(workspace_contract,mode) :
	for a in mode.register  :
		if mode.register[a].get('workspace_contract') == workspace_contract :
			return  mode.register[a].get('username')
	return None
 
def contracts_to_owners(workspace_contract, mode) :
	w3 = mode.w3
	contract = w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	return contract.functions.contractsToOwners(workspace_contract).call()	 
 

def owners_to_contracts(address, mode) :
	w3 = mode.w3
	contract = w3.eth.contract(mode.foundation_contract,abi=constante.foundation_ABI)
	return contract.functions.ownersToContracts(address).call()
	

def read_profil (workspace_contract, mode) :
	w3=mode.w3
	# setup constante person
	person= {'firstname' : 102105114115116110097109101,
			'lastname' : 108097115116110097109101,
			'url' : 117114108,
			'email' : 101109097105108
			}
	# setup constant company
	company = {'name' : 110097109101,
				'contact_name' : 99111110116097099116095110097109101,
				'contact_email' : 99111110116097099116095101109097105108,
				'contact_phone' : 99111110116097099116095112104111110101,
				'website' : 119101098115105116101,
				'email' : 101109097105108
				}

	profil = dict()
	# category
	contract = w3.eth.contract(workspace_contract,abi=constante.workspace_ABI)
	category = contract.functions.identityInformation().call()[1]	
	
	# if person
	if category == 1001 : 
		for topicname, topic in person.items() :
			claim = contract.functions.getClaimIdsByTopic(topic).call()
			if len(claim) == 0 :
				profil[topicname] = None			
			else :
				claimId = claim[-1].hex()
				data = contract.functions.getClaim(claimId).call()
				profil[topicname]=data[4].decode('utf-8')					
	if category == 2001 : 
		for topicname, topic in company.items() :
			claim = contract.functions.getClaimIdsByTopic(topic).call()
			if len(claim) == 0 :
				profil[topicname] = None			
			else :
				claimId = claim[-1].hex()
				data = contract.functions.getClaim(claimId).call()
				profil[topicname]=data[4].decode('utf-8')		
	return profil,category 
 	 

def create_document(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, doctype, data, mydays, privacy, mode, synchronous) :
# @data = dict	
	w3=mode.w3	
	
	# cryptage des données par le user
	if privacy != 'public' :
		encrypted_data = data
		#recuperer la cle AES cryptée
		contract = w3.eth.contract(workspace_contract_to,abi = constante.workspace_ABI)
		mydata = contract.functions.identityInformation().call()
		if privacy == 'private' :
			my_aes_encrypted = mydata[5]
		if privacy == 'secret' :
			my_aes_encrypted = mydata[6]

		# read la cle privee RSA sur le fichier
		filename = "./RSA_key/"+mode.BLOCKCHAIN + '/' + address_to + "_TalaoAsymetricEncryptionPrivateKeyAlgorithm1" + ".txt"
		with open(filename,"r") as fp :
			my_rsa_key = fp.read()	
			fp.close()   

		# decoder la cle AES128 cryptée avec la cle RSA privée
		key = RSA.importKey(my_rsa_key)
		cipher = PKCS1_OAEP.new(key)	
		my_aes = cipher.decrypt(my_aes_encrypted)
		
		# coder les datas
		bytesdatajson = bytes(json.dumps(encrypted_data), 'utf-8') # dict -> json(str) -> bytes
		header = b"header"
		cipher = AES.new(my_aes, AES.MODE_EAX) #https://pycryptodome.readthedocs.io/en/latest/src/cipher/modern.html
		cipher.update(header)
		ciphertext, tag = cipher.encrypt_and_digest(bytesdatajson)
		json_k = [ 'nonce', 'header', 'ciphertext', 'tag' ]
		json_v = [ b64encode(x).decode('utf-8') for x in [cipher.nonce, header, ciphertext, tag] ]
		data = dict(zip(json_k, json_v))
	
			
	# calcul de la date
	if mydays == 0 :
		expires = 0
	else :	
		myexpires = datetime.utcnow() + datetime.timedelta(days = mydays, seconds = 0)
		expires = int(myexpires.timestamp())	
		
	#envoyer la transaction sur le contrat
	contract = w3.eth.contract(workspace_contract_to,abi = constante.workspace_ABI)
	nonce = w3.eth.getTransactionCount(address_from)  
	
	# stocke sur ipfs les data attention on archive des bytes
	ipfs_hash = ipfs_add(data)
	
	
	
	# calcul du checksum en bytes des data, conversion du dictionnaire data en chaine str
	_data = json.dumps(data)
	checksum = hashlib.md5(bytes(_data, 'utf-8')).hexdigest()
	# la conversion inverse de bytes(data, 'utf-8') est XXX.decode('utf-8')
	
	encrypted = False if privacy == 'public' else True
	# Transaction
	txn = contract.functions.createDocument(doctype,2,expires,checksum,1, bytes(ipfs_hash, 'utf-8'), encrypted).buildTransaction({'chainId': mode.CHAIN_ID,'gas':500000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	signed_txn = w3.eth.account.signTransaction(txn,private_key_from)
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
	transaction_hash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
	if synchronous == True :
		w3.eth.waitForTransactionReceipt(transaction_hash)		
	
	# recuperer l iD du document sur le dernier event DocumentAdded
	contract = w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	myfilter = contract.events.DocumentAdded.createFilter(fromBlock= 5800000,toBlock = 'latest')
	eventlist = myfilter.get_all_entries()
	document_id = eventlist[-1]['args']['id']
	return document_id, ipfs_hash, transaction_hash
	
	
def get_document(workspace_contract_from, private_key_from, workspace_contract_user, documentId, mode) :
	w3 = mode.w3
	contract = w3.eth.contract(workspace_contract_user,abi=constante.workspace_ABI)
	try :
		(doctype, doctypeversion, expires, issuer, checksum, engine, ipfshash, encrypted, related) = contract.functions.getDocument(documentId).call()
	except :
		return None, None, None, None, None, None, None, None, None, None, None , None, None
	
	"""
	50000..... for experience
	30000..... for files
	40000..... for education
	10000..... for kbis
	15000......for kyc
	20000......for certificate
	experience and education should be always public but in case ....
	"""
	
	if doctype == 50000 or doctype == 40000 or doctype == 10000 :
		privacy = 'public'
	if doctype == 50001 or doctype == 40001 :
		privacy = 'private'
	if doctype == 50002 or doctype == 40002 :
		privacy = 'secret'
	
	# get transaction info
	contract = w3.eth.contract(workspace_contract_user, abi=constante.workspace_ABI)
	claim_filter = contract.events.DocumentAdded.createFilter(fromBlock= 5800000,toBlock = 'latest')
	event_list = claim_filter.get_all_entries()
	for doc in event_list :
		if doc['args']['id'] == documentId :
			transactionhash = doc['transactionHash']
			transaction_hash = transactionhash.hex()
			transaction = w3.eth.getTransaction(transaction_hash)
			gas_price = transaction['gasPrice']
			identity_workspace_contract = transaction['to'] 
			block_number = transaction['blockNumber']
			block = mode.w3.eth.getBlock(block_number)
			date = datetime.fromtimestamp(block['timestamp'])				
			gas_used = w3.eth.getTransactionReceipt(transaction_hash).gasUsed
			created = str(date)

	# recuperation du msg 
	data = ipfs_get(ipfshash.decode('utf-8'))
	# calcul de la date
	if expires == 0 :
		expires = 'Unlimited'
	else :	
		myexpires = datetime.fromtimestamp(expires)
		#expires = myexpires.strftime("%y/%m/%d")
		expires = str(myexpires)

	if privacy  == 'public' :
		return issuer, identity_workspace_contract, data, ipfshash.decode('utf-8'), gas_price*gas_used, transaction_hash, doctype, doctypeversion, created, expires, issuer, privacy, related
	
	if encrypted != 'public' and private_key_from == None : 
		print ("document is  encrypted and no keys has been given ")
		return None
	
	
	#recuperer la cle AES cryptée
		contract = w3.eth.contract(workspace_contract_user,abi = constante.workspace_ABI)
		mydata = contract.functions.identityInformation().call()
		if privacy == 'private' :
			his_aes_encrypted = mydata[5]
		if privacy == 'secret' :
			his_aes_encrypted = mydata[6]
		
	# read la cle privee RSA sur le fichier
	address_user = contracts_to_owners(workspace_contract_user, mode)
	filename = "./RSA_key/"+mode.BLOCKCHAIN+'/'+address_from+"_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
	with open(filename,"r") as fp :
		rsa_key=fp.read()	
		fp.close()   
					
	# decoder ma cle AES128 cryptée avec ma cle RSA privée
	key = RSA.importKey(rsa_key)
	cipher = PKCS1_OAEP.new(key)	
	his_aes=cipher.decrypt(his_aes_encrypted)
		
		# decoder les datas
	try:
		b64 = data #json.loads(json_input)
		json_k = [ 'nonce', 'header', 'ciphertext', 'tag' ]
		jv = {k:b64decode(b64[k]) for k in json_k}
		cipher = AES.new(his_aes, AES.MODE_EAX, nonce=jv['nonce'])
		cipher.update(jv['header'])
		plaintext = cipher.decrypt_and_verify(jv['ciphertext'], jv['tag'])
		msg = json.loads(plaintext.decode('utf-8'))
		return issuer, identity_workspace_contract, msg,ipfshash.decode('utf-8'), gas_price*gas_used, transaction_hash, doctype, doctypeversion, created, expires, issuer, privacy, related	
			
	except ValueError :
		print("data Decryption error")
		return None
	
				
def delete_document(address_from, workspace_contract_from, address_to, workspace_contract_to, private_key_from, documentId, mode):
	w3 = mode.w3
	contract=w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	# calcul du nonce de l envoyeur de token
	nonce = w3.eth.getTransactionCount(address_from)  
	# Build transaction
	txn = contract.functions.deleteDocument(int(documentId)).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 800000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})	
	signed_txn = w3.eth.account.signTransaction(txn,private_key_from)
	# send transaction	
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)  
	transaction_hash = w3.toHex(w3.keccak(signed_txn.rawTransaction))
	w3.eth.waitForTransactionReceipt(transaction_hash, timeout=2000, poll_latency=1)
	transaction = w3.eth.getTransaction(transaction_hash)
	gas_price = transaction['gasPrice']
	block_number = transaction['blockNumber']
	block = mode.w3.eth.getBlock(block_number)
	date = datetime.fromtimestamp(block['timestamp'])				
	#gas_used = w3.eth.getTransactionReceipt(transaction_hash).gasUsed
	gas_used = 10000
	deleted = date.strftime("%y/%m/%d")		
	return transaction_hash, gas_used*gas_price, deleted

class Document() :
	def __init__(self, topic) :		
		self.topic = topic
							
	def relay_add(self, identity_workspace_contract, data, mode, mydays=0, privacy='public', synchronous=True) :
		""" Only public data """
		if self.topic == 'Education' :
			doctype = 40000
		if self.topic == 'Experience' :
			doctype = 50000				 			
		identity_address = contracts_to_owners(identity_workspace_contract, mode)
		return create_document(mode.relay_address, mode.relay_workspace_contract, identity_address, identity_workspace_contract, mode.relay_private_key, doctype, data, mydays, privacy, mode, synchronous)
	
	def relay_get(self, identity_workspace_contract, doc_id, mode) :	
		(issuer_address, identity_workspace_contract, data, ipfshash, transaction_fee, transaction_hash, doctype, doctypeversion, created, expires, issuer, privacy, related) = get_document(mode.relay_workspace_contract, mode.relay_private_key, identity_workspace_contract, doc_id, mode)
		if issuer_address is None :
			return None
		issuer_workspace_contract = owners_to_contracts(issuer_address, mode)
		(profil, category) = read_profil(issuer_workspace_contract, mode)
		self.created = created
		self.issuer = {'address' : issuer_address,
						'workspace_contract' : issuer_workspace_contract,
						'category' : category}
		self.issuer['type'] = 'Person' if category == 1001 else 'Company'
		self.issuer['username'] = get_username(issuer_workspace_contract, mode)
		self.issuer.update(profil)
		self.transaction_hash = transaction_hash
		self.transaction_fee = transaction_fee
		self.doctypeversion = doctypeversion
		self.ipfshash = ipfshash
		self.data_location = 'https://ipfs.infura.io/ipfs/'+ ipfshash
		self.expires = expires
		self.privacy = privacy
		self.doc_id = doc_id
		self.identity= {'address' : contracts_to_owners(identity_workspace_contract, mode),
							'workspace_contract' : identity_workspace_contract}
		self.transaction_fee = transaction_fee
		return data
			
	def relay_delete(self, identity_workspace_contract, doc_id, mode) :
		identity_address = contracts_to_owners(identity_workspace_contract, mode)
		return delete_document(mode.relay_address, mode.relay_workspace_contract, identity_address, identity_workspace_contract, mode.relay_private_key, doc_id, mode)
	


class Education(Document) :
	def __init__(self) :		
		Document.__init__(self, 'Education')
		self.topic = 'Education'	
		
	def relay_get_education(self, identity_workspace_contract, doc_id, mode) :
		data = Document.relay_get(self, identity_workspace_contract, doc_id, mode)
		if data is None :
			return False
		self.topic = "Education"
		self.title = data['title']
		self.description = data['description']
		self.end_date = data['end_date']
		self.start_date = data['start_date']
		self.organization = data['organization']
		self.certificate_link = data.get('certificate_link', "") # a retirer
		self.skills = data['skills']
		return True
		
class Experience(Document) :
	def __init__(self) :	
		Document.__init__(self, 'Experience')	
		self.topic = 'Experience'	
		
	def relay_get_experience(self, identity_workspace_contract, doc_id, mode) :
		data = Document.relay_get(self, identity_workspace_contract, doc_id, mode)
		if data is None :
			return False
		self.topic = "Experience"
		self.title = data['title']
		self.description = data['description']
		self.end_date = data['end_date']
		self.start_date = data['start_date']
		self.company = data['company']
		self.certificate_link = data.get('certificate_link', "") # a retirer
		self.skills = data['skills']
		return True
		
class Kbis() :	
	def __init__(self) :	
		Document.__init__(self, 'Kbis')	
		self.topic = 'Kbis'	
	
	def talao_add(self, identity_workspace_contract, kbis, mode, mydays=0, privacy='public', synchronous=True) :
		""" Only public data """
		doctype = 10000
		identity_address = contracts_to_owners(identity_workspace_contract, mode)		 					
		return create_document(mode.owner_talao, mode.workspace_contract_talao, identity_address, identity_workspace_contract, mode.owner_talao_private_key, doctype, kbis, mydays, privacy, mode, synchronous) 
		
	def relay_get_kbis(self, identity_workspace_contract, doc_id, mode) :
		data = Document.relay_get(self, identity_workspace_contract, doc_id, mode)
		if data is None :
			return False
		self.topic = "kbis"
		self.name = data['name']
		self.siret = data['siret']
		self.date = data['date']
		self.capital = data['capital']
		self.address = data['address']
		self.legal_form = data['legal_form']
		self.activity = data['activity'] 
		self.naf = data['naf']
		self.ceo = data['ceo']
		self.managing_director = data['managing_director']
		return True


		
class Kyc() :	
	def __init__(self) :	
		Document.__init__(self, 'Kyc')	
		self.topic = 'Kyc'	
	
	def talao_add(self, identity_workspace_contract, kbis, mode, mydays=0, privacy='public', synchronous=True) :
		""" Only public data """
		doctype = 15000
		identity_address = contracts_to_owners(identity_workspace_contract, mode)		 					
		return create_document(mode.owner_talao, mode.workspace_contract_talao, identity_address, identity_workspace_contract, mode.owner_talao_private_key, doctype, kbis, mydays, privacy, mode, synchronous) 
		
	def relay_get_kyc(self, identity_workspace_contract, doc_id, mode) :
		data = Document.relay_get(self, identity_workspace_contract, doc_id, mode)
		if data is None :
			return False
		self.topic = "kyc"
		self.lastname = data['lastname']
		self.firstname = data['firstname']
		self.date_of_birth = data['date_of_birth']
		self.sex = data['sex']
		self.nationality = data['nationality']
		self.date_of_issue = data['date_of_issue']
		self.date_of_expiration = data['date_of_expiration'] 
		self.authority = data['authority']
		self.country = data['country']
		return True
	

		
class Certificate() :	
	def __init__(self) :	
		Document.__init__(self, 'Certificate')	
		self.topic = 'Certificate'	
	
	def talao_add(self, identity_workspace_contract, certificate, mode, mydays=0, privacy='public', synchronous=True) :
		""" Only public data """
		doctype = 20000
		identity_address = contracts_to_owners(identity_workspace_contract, mode)		 					
		return create_document(mode.owner_talao, mode.workspace_contract_talao, identity_address, identity_workspace_contract, mode.owner_talao_private_key, doctype, kbis, mydays, privacy, mode, synchronous) 
		
	def relay_get_certificate(self, identity_workspace_contract, doc_id, mode) :
		data = Document.relay_get(self, identity_workspace_contract, doc_id, mode)
		if data is None :
			return False
		self.topic = "certificate"
		self.type = data['type']
		self.lastname = data['lastname']
		self.firstname = data['firstname']
		self.title = data['title']
		self.description = data['description']
		self.start_date = data['start_date']
		self.end_date = data['end_date']
		self.skills = data['skills'] 
		self.score_delivery = data['score_delievery']
		self.score_recommendation = data['score_recommendation']
		self.score_schedule = data['score_schedule']
		self.score_communication = data['score_communication']
		self.logo = data['logo']
		self.signature = data['signature']
		self.company = data['company']
		self.reviewer = data['reviewer']
		self.manager = data['manager']
		
		return True
