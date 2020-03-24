import json
import constante
from eth_account.messages import encode_defunct



#################################################
#  add claim
#################################################
# @data : str
# @topicname : type str , 'contact'
# @ipfshash = str exemple  b'qlkjglgh'.decode('utf-8') 
# signature cf https://web3py.readthedocs.io/en/stable/web3.eth.account.html#sign-a-message

def addClaim(workspace_contract_to, address_from,private_key_from, topicname, issuer, data, ipfshash,mode) :
	
	w3=mode.initProvider()
	
	# on va chercher topicvalue dans le dict existant (constante.py) si il n existe pas on le calcule
	topicvalue=constante.topic.get(topicname)
	if topicvalue== None :
		topicvaluestr =''
		for i in range(0, len(topicname))  :
			a = str(ord(topicname[i]))
			if int(a) < 100 :
				a='0'+a
			topicvaluestr=topicvaluestr+a
		topicvalue=int(topicvaluestr)
	
	nonce = w3.eth.getTransactionCount(address_from)  
	
	# calcul de la signature
	msg = w3.solidityKeccak(['bytes32','address', 'bytes32', 'bytes32' ], [bytes(topicname, 'utf-8'), issuer, bytes(data, 'utf-8'), bytes(ipfshash, 'utf-8')])
	message = encode_defunct(text=msg.hex())
	signed_message = w3.eth.account.sign_message(message, private_key=private_key_from)
	signature=signed_message['signature']
	
	# Build transaction
	contract=w3.eth.contract(workspace_contract_to,abi=constante.workspace_ABI)
	txn=contract.functions.addClaim(topicvalue,1,issuer, signature, bytes(data, 'utf-8'),ipfshash ).buildTransaction({'chainId': mode.CHAIN_ID,'gas': 4000000,'gasPrice': w3.toWei(mode.GASPRICE, 'gwei'),'nonce': nonce,})
	
	#sign transaction with caller wallet
	signed_txn=w3.eth.account.signTransaction(txn,private_key_from)
	
	# send transaction	
	w3.eth.sendRawTransaction(signed_txn.rawTransaction)
	hash1= w3.toHex(w3.keccak(signed_txn.rawTransaction))
	w3.eth.waitForTransactionReceipt(hash1, timeout=2000, poll_latency=1)	
	return hash1
