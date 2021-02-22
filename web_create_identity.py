"""
Just a process to create user.


"""

from flask import request, redirect, render_template, session, flash
import random
import unidecode
import time
from datetime import timedelta, datetime

# dependances
import Talao_message

from factory import ssi_createidentity

import sms
import directory
import ns


"""
# route /register/
def register(mode) :
	if request.method == 'GET' :
		session.clear()
		session['is_active'] = True
		message = request.args.get('message', "")
		return render_template("register.html",message=message, )
	if request.method == 'POST' :
		session['email'] = request.form['email']
		session['firstname'] = request.form['firstname']
		session['lastname'] = request.form['lastname']
		session['username'] = ns.build_username(session['firstname'], session['lastname'], mode)
		session['phone'] = request.form['phone']
		session['search'] = request.form.get('CheckBox')
		try :
			if not sms.check_phone(session['phone'], mode) :
				return render_template("register.html", message='Incorrect phone number.',
												firstname=session['firstname'],
												lastname=session['lastname'],
												email=session['email'])
			else :
				return redirect (mode.server + 'register/password/')
		except :
			return render_template("register.html",message='SMS connexion problem.', )
"""


# register ID with your wallet as owner in Talao Identity
#@app.route('/wc_register/', methods = ['GET', 'POST'])
def wc_register(mode) :
	if request.method == 'GET' :
		session.clear()
		message = request.args.get('message', "")
		# wrong call
		session['wallet_address']= request.args.get('wallet_address')
		if not session['wallet_address'] :
			return redirect(mode.server + '/login')
		return render_template('wc_register.html', message=message, wallet_address=session['wallet_address'])

	if 'status' not in session :
		session['email'] = request.form['email']
		session['phone'] = request.form['phone']
		session['firstname'] = request.form['firstname']
		session['lastname'] = request.form['lastname']
		session['username'] = ns.build_username(session['firstname'], session['lastname'], mode)
		session['transfer'] = True if request.form.get('CheckBox2') == 'digital_identity' else False
		# if CGU not accepted
		if not request.form.get('CheckBox1') :
			return render_template('wc_register.html', message="CGU has not been accepted", wallet_address=session['wallet_address'])
		session['status'] = 'email_checking'
		session['code'] = str(random.randint(10000, 99999))
		session['code_delay'] = datetime.now() + timedelta(seconds= 300)
		subject = 'Talao : Email authentification  '
		Talao_message.messageHTML(subject, session['email'], 'code_auth', {'code' : session['code']}, mode)
		return render_template("wc_register_email.html",message='' )

	elif session['status'] == 'email_checking':
		mycode = request.form.get('mycode')
		if mycode == session['code'] and datetime.now() < session['code_delay']  :
			session['status'] = 'phone_checking'
			session['code'] = str(random.randint(10000, 99999))
			session['code_delay'] = datetime.now() + timedelta(seconds= 300)
			try :
				sms.send_code(session['phone'], session['code'], mode)
			except :
				del session['status']
				return render_template("wc_register.html",message='Wrong phone number,country code needed' )
			return render_template("wc_register_phone.html",message='' )
		else :
			del session['status']
			return render_template("wc_register.html",message='This code is incorrect.' )

	elif session['status'] == 'phone_checking':
		mycode = request.form.get('mycode')
		if mycode == session['code'] and datetime.now() < session['code_delay']  :
			del session['status'] # test
			return redirect(mode.server + '/login') # test

			if not ssi_createidentity.create_user(session['wallet_address'],session['username'],
											request.form['email'],
											mode,
											user_aes_encrypted_with_talao_key=request.form.get("user_aes_encrypted_with_talao_key"),
											firstname=session['firstname'],
											lastname=session['lastname'],
											rsa=request.form.get('public_rsa'),
											private=request.form.get('aes_private'),
											secret=request.form.get('aes_secret'),
											transfer = session['transfer'],
											)[2] :
				print('Error : createidentity failed')
				return render_template("wc_register.html",message='Connexion problem.', )
			else :
				if request.form.get('CheckBox') :
					directory.add_user(mode, session['username'], session['firstname']+ ' ' + session['lastname'], None)
					print('Warning : directory updated with firstname and lastname')
			return render_template("create3.html", username=session['username'])
		else :
			del session['status']
			return render_template("wc_register.html",message='Wrong code.', )

"""
# route /register/password/
def register_password(mode):
	if not session.get('is_active') :
		return redirect(mode.server + 'register/?message=Session+expired.')
	if request.method == 'GET' :
		return render_template("create_password.html")
	if request.method == 'POST' :
		session['password'] = request.form['password']
		session['code'] = str(random.randint(10000, 99999))
		session['code_delay'] = datetime.now() + timedelta(seconds= 180)
		session['try_number'] = 0
		sms.send_code(session['phone'], session['code'], mode)
		print('Info : secret code = ', session['code'])
		return render_template("register_code.html")

# route /register/code/
def register_code(mode) :
	if not session.get('is_active') or 'try_number' not in session :
		return redirect(mode.server + 'register/?message=session+expired.')
	mycode = request.form['mycode']
	session['try_number'] +=1
	print('Warning : code received = ', mycode)
	authorized_codes = [session['code'], '123456'] if mode.test else [session['code']]
	if mycode in authorized_codes and datetime.now() < session['code_delay'] and session['try_number'] < 4 :
		print("Warning : call createidentity")
		workspace_contract = createidentity.create_user(session['username'],
											session['email'],
											mode,
											firstname=session['firstname'],
											lastname=session['lastname'],
											phone=session['phone'],
											password=session['password'])[2]
		if not workspace_contract :
			print('Error : createidentity failed')
			return render_template("register.html",message='Connexion problem.', )
		if session['search'] :
			directory.add_user(mode, session['username'], session['firstname']+ ' ' + session['lastname'], None)
			print('Warning : directory updated with firstname and lastname')
		session['is_active'] = False
		return render_template("create3.html", username=session['username'])
	elif session['try_number'] == 3 :
		session['is_active'] = False
		return render_template("create4.html", message="Code is incorrect. Too many trials.")
	elif datetime.now() > session['code_delay'] :
		session['is_active'] = False
		return render_template("create4.html",  message="Code expired.")
	else :
		if session['try_number'] == 1 :
			message = 'Code is incorrect, 2 trials left.'
		if session['try_number'] == 2 :
			message = 'Code is incorrect, last trial.'
		return render_template("register_code.html", message=message)

# route register/post_code/
def register_post_code(mode) :
	return redirect (mode.server + 'login/?username=' + session['username'])
"""