import smtplib
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText 
from email.mime.base import MIMEBase 
from email import encoders 

import constante

def messageAuth (email_to, random) :


	# debut de la fonction
	fromaddr = "thierry.thevenet1963@gmail.com"
	toaddr = [email_to]
#	toaddr = ['thierry.thevenet@talao.io' , 'thevenet_thierry@yahoo.fr']

	# instance of MIMEMultipart 
	msg = MIMEMultipart() 

	# storing the senders email address 
	msg['From'] = fromaddr 

	# storing the receivers email address 
	msg['To'] = ", ".join(toaddr)

	# storing the subject 
	msg['Subject'] = 'Talao : Authentification par email  '  #+firstname+' '+ name + ' - '+ constante.BLOCKCHAIN

	# string to store the body of the mail 
	body = 'Code a saisir : '+ random  #firstname+' '+name+'\r\n\r\nEmail : '+email+ '\r\nChain : '+ constante.BLOCKCHAIN + '\r\nAddress : ' + str(eth_a) + '\r\nPrivate Key : '+ str(eth_p)+ '\r\nWorkspace Address : '+str(workspace_contract_address)+'\r\nStatus : '+status+'\r\nBackend Id : '+str(backend_Id) +'\r\nBackend Login : ' + login +'\r\nBackend Password : ' + SECRET +'\r\nAES key : ' + str(AES_key) + constante.DAPP_LINK + str(workspace_contract_address)

	# attach the body with the msg instance 
	msg.attach(MIMEText(body, 'plain')) 

	# open the file to be sent
	#path = "./RSA_key/"+constante.BLOCKCHAIN+'/'+eth_a+"_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
	#filename = eth_a+"_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
	#attachment = open(path, "rb") 

	# instance of MIMEBase and named as p 
	p = MIMEBase('application', 'octet-stream') 

	# To change the payload into encoded form 
	#p.set_payload((attachment).read()) 

	# encode into base64 
	#encoders.encode_base64(p) 

	#p.add_header('Content-Disposition', "attachment; filename= %s" % filename) 

	# attach the instance 'p' to instance 'msg' 
	#msg.attach(p) 

	# creates SMTP session 
	s = smtplib.SMTP('smtp.gmail.com', 587) 

	# start TLS for security 
	s.starttls() 

	# Authentication 
	s.login(fromaddr, "Mishoosh2") 

	# Converts the Multipart msg into a string 
	text = msg.as_string() 

	# sending the mail 
	try:
		s.sendmail(msg['from'],  msg["To"].split(","), text) 
		print ('email sent')
	except:
		print ('error sending mail')
	s.quit()
	return





def messageLog(name, firstname, email,status,eth_a, eth_p, workspace_contract_address, backend_Id, login, SECRET, AES_key)  :


	# debut de la fonction
	fromaddr = "thierry.thevenet1963@gmail.com"
	toaddr = ['thierry.thevenet@talao.io']
#	toaddr = ['thierry.thevenet@talao.io' , 'thevenet_thierry@yahoo.fr']

	# instance of MIMEMultipart 
	msg = MIMEMultipart() 

	# storing the senders email address 
	msg['From'] = fromaddr 

	# storing the receivers email address 
	msg['To'] = ", ".join(toaddr)

	# storing the subject 
	msg['Subject'] = 'Workspace Log : '+firstname+' '+ name + ' - '+ constante.BLOCKCHAIN

	# string to store the body of the mail 
	body = 'A new Talao workspace has been deployed for '+ firstname+' '+name+'\r\n\r\nEmail : '+email+ '\r\nChain : '+ constante.BLOCKCHAIN + '\r\nAddress : ' + str(eth_a) + '\r\nPrivate Key : '+ str(eth_p)+ '\r\nWorkspace Address : '+str(workspace_contract_address)+'\r\nStatus : '+status+'\r\nBackend Id : '+str(backend_Id) +'\r\nBackend Login : ' + login +'\r\nBackend Password : ' + SECRET +'\r\nAES key : ' + str(AES_key) + constante.DAPP_LINK + str(workspace_contract_address)

	# attach the body with the msg instance 
	msg.attach(MIMEText(body, 'plain')) 

	# open the file to be sent
	path = "./RSA_key/"+constante.BLOCKCHAIN+'/'+eth_a+"_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
	filename = eth_a+"_TalaoAsymetricEncryptionPrivateKeyAlgorithm1"+".txt"
	attachment = open(path, "rb") 

	# instance of MIMEBase and named as p 
	p = MIMEBase('application', 'octet-stream') 

	# To change the payload into encoded form 
	p.set_payload((attachment).read()) 

	# encode into base64 
	encoders.encode_base64(p) 

	p.add_header('Content-Disposition', "attachment; filename= %s" % filename) 

	# attach the instance 'p' to instance 'msg' 
	msg.attach(p) 

	# creates SMTP session 
	s = smtplib.SMTP('smtp.gmail.com', 587) 

	# start TLS for security 
	s.starttls() 

	# Authentication 
	s.login(fromaddr, "Mishoosh2") 

	# Converts the Multipart msg into a string 
	text = msg.as_string() 

	# sending the mail 
	try:
		s.sendmail(msg['from'],  msg["To"].split(","), text) 
		print ('email sent')
	except:
		print ('error sending mail')
	s.quit()
	return


