# load settings
# test_gpg()
# select_currency()

import os
import subprocess
import json
# import mylibs.helpers as helpers
import mylibs.ioprocessing as iop
import mylibs.wallet_commands as wallet_commands
import datetime
import traceback


def encrypt_wallet(data_dir_path,wal_encr_pass):

	orig_w=os.path.join(data_dir_path,'wallet.dat')
	if not os.path.exists(orig_w):
		return 'Wallet path not correct: '+data_dir_path
	
	encr_w=os.path.join(data_dir_path,'wallet.encr')
	
	if os.path.exists(encr_w):
		os.remove(encr_w)
		
	encr_str='gpg --cipher-algo AES256 --pinentry loopback --passphrase "'+wal_encr_pass+'" -o '+encr_w+" -c "+orig_w
	# print(encr_str)
	
	str_rep=subprocess.getoutput(encr_str)
	os.remove(orig_w)
	
	return 'Wallet encrypted '+str_rep
	

def decrypt_wallet(data_dir_path,wal_encr_pass):

	orig_w=os.path.join(data_dir_path,'wallet.dat')
	if os.path.exists(orig_w):
		return 'Wallet already derypted! '
	
	encr_w=os.path.join(data_dir_path,'wallet.encr')
	
	if not os.path.exists(encr_w):
		return 'Encrypted wallet missing! !!!'
		
		
	decr_str='gpg --pinentry loopback --passphrase "'+wal_encr_pass+'" -o '+orig_w +" -d "+encr_w
	str_rep=subprocess.getoutput(decr_str)
	os.remove(encr_w)
	
	return 'Wallet decrypted '+str_rep



def print_cur_addr_book(cab):

	ret_str='\n\nAddress book: \n[Alias][Full address]'
	# print("\nAddress book \n[Alias][Full address]")
	if len(cab)<1:
		# print("[EMPTY]")
		ret_str+='\n[EMPTY]\n'
		
	for k,v in cab.items():
		# print("["+k+"]["+v+"]")
		ret_str+='\n'+"["+k+"]["+v+"]"
	ret_str+='\n\n'
	return ret_str


def get_addr_book(cur_path,pp):
	
	json_conf=json.loads('{}')
	
	if os.path.exists(cur_path): 
		try:
			str_rep=iop.decrypt_cred(pp,cur_path) 
			
			if 'failed' in str_rep:
				strtmp="Your password didn't match the address book file [encrypted]. Delete it or change the config file to previous one."
				print(strtmp)
			else:
				decr_str=str_rep.split(iop.lorem_ipsum())
				decr_str=decr_str[1]
				
				json_conf=json.loads(decr_str)			
		except:
			strtmp="Your password didn't match the address book file [encrypted]. Delete it or change the config file to previous one. Exception..."
			print(strtmp)
	else: 
		iop.saving_encr_cred( json.dumps(json_conf) , cur_path, pp)
	
	return json_conf
	
	
	
def external_addr_book( internal_addr_list, cur_path,pp,CLI_STR,print_only=False):

	json_conf=get_addr_book(cur_path,pp) #json.loads('{}')
	
	if print_only:
		return print_cur_addr_book(json_conf)
		
	act=["add","del"]
	print("Actions: "+str(act))
	
	while True:
	
		change=False
		
		print(print_cur_addr_book(json_conf))
		sela=iop.optional_input('Select action or quit [q]: ', options_list=act, soft_quite=True)
		
		if sela in ['','q']:
			break
			
		elif sela=="add":
			newa=''
			while True:
				newa=iop.input_prompt('Enter new address: ', confirm=False, soft_quite=True)
				
				if newa in ['','q']:
					break
					
				isv,isz=wallet_commands.isaddrvalid(CLI_STR,newa)
				if isv:
					break
				else:
					print('Addresss not valid - enter correct address...')
			
			if newa in ['','q']:
				continue
			
			addrnick=''
			while True:
				addrnick=iop.input_prompt('Enter unique address owner nick/name: ', confirm=True, soft_quite=True)
				
				# print('internal_addr_list',internal_addr_list)
				# print('internal_addr_list.keys()',internal_addr_list.keys())
				
				if len(addrnick)<1:
					print("Minimum 1 character required...")
					
				elif addrnick in internal_addr_list.values():
					print("This name is already taken [internal wallet alias], enter a different one...")
					
				elif addrnick in json_conf:
					print("This name is already taken, enter a different one...")
				else:
					break
					
			if addrnick!='' and newa!='':
				json_conf[addrnick]=newa
				change=True
				
		elif sela=="del":
			
			addrnick=iop.optional_input('Enter address owner nick/name from the book to DELETE it: ', options_list=json_conf.keys(), soft_quite=True)
			if addrnick!='':
				del json_conf[addrnick]
				change=True
		
		if change:
			iop.saving_encr_cred( json.dumps(json_conf) , cur_path, pp)
		
	
	
	
	


def alias_mapping(allist): # address_aliases(get_wallet(True))
	alias_map={}
	for aa in allist:
		# if value contains '_' split
		xx=aa.split('_')
		
		tmpa=''
		if len(xx)>1:
			lll=3
			if len(xx)>2:
				lll=2
				
			for xi in xx:
				tmpa+=xi[:min([len(xi), lll])]
		else:
			tmpa=aa[:max([len(aa), 5])] 
			
		while len(tmpa)<5: # safer
			tmpa+=tmpa
			
		iter=1
		while tmpa in alias_map.values():
			tmpa+=str(iter)
			iter+=1
		
		alias_map[aa]=tmpa #.append([aa, tmpa])
		
	return alias_map	


def print_current_settings(set_name,json_conf,set_name_alia=[]):
	# print(str(json_conf))
	if len(set_name_alia)>0:
		print('\nCurrent app settings [Alias][Name][Value]:')
	else:
		print('\nCurrent app settings [Name][Value]:')
		
	for kkk in set_name: #jct,vv in json_conf.items():
		if kkk in json_conf:
			vv=json_conf[kkk]
			jct=kkk
			if len(set_name_alia)>0:
				print('['+set_name_alia[jct]+']['+jct+']['+vv+']')
			else:
				print('['+jct+']['+vv+']')
			

def save_app_settings_new_password(json_conf,pswd):

	print('Enter new password for config file encryption.')
	newpp=iop.ask_password()
	
	if len(newpp)<2:
		print('Password too short - quit')
		return

	newest_date, newest_file, filed = iop.get_config_file()	
	old_file=newest_file
	ddate=datetime.datetime.now()
	newest_file=os.path.join('config',"gnupg_deamon_cfg_"+ddate.strftime('%Y-%m-%dh%Hm%Ms%S')+".txt")
	
	print('Encrypting config with new password ['+newpp+'] to file ['+newest_file+']')
	print('Previous config file with old password ['+old_file+'] - delete it if it is unnecessary.')
		
	iop.saving_encr_cred( json.dumps(json_conf) , newest_file, newpp)
	print('App settings changed - exiting. Please start the app again.')
	exit()
			

def edit_app_settings(json_conf,pswd):

	set_name=['email_addr',"email_password","imap_addr","smtp_addr","tx_amount_limit","tx_time_limit_hours","outgoing_encryption_type","outgoing_encryption_key","incoming_encryption_type","incoming_encryption_key","incoming_mail_sender_email","incoming_mail_title","wallet_secret_key","gpg_password","incoming_tx_notification","staking_summary_notification","wallet_encryption","active_consolidation_address"]
	
	set_name_alia=alias_mapping(set_name)
	
	newest_date, newest_file, filed = iop.get_config_file()	
	
	toedit=''
	
	while True:
		print_current_settings(set_name,json_conf,set_name_alia)
		
		toedit=iop.optional_input('Enter alias to edit value or quite [q] or quite and save [S]: ', options_list=list(set_name_alia.values())+['S'], soft_quite=True)
		if toedit=='S':
			iop.saving_encr_cred( json.dumps(json_conf) , newest_file, pswd)
			print('App settings changed - exiting. Please start the app again.')
			exit()
		elif toedit in ['q','']:
			print('\n! Exit editing without saving, current setup:')
			print_current_settings(set_name,json_conf,set_name_alia)
			break
			
		nameii = [key  for (key, value) in set_name_alia.items() if value == toedit]
		print('Editing '+nameii[0]+', current value = '+json_conf[nameii[0]])
		newvv=''
		if "encryption_type" in nameii[0]:
			newvv=iop.optional_input('Enter new value [aes256/pgp]: ', options_list=['aes256','pgp'], soft_quite=True)
			
		elif nameii[0] in ["incoming_tx_notification","staking_summary_notification"]:
			# "incoming_tx_notification","staking_summary_notification"
			newvv=iop.optional_input('Select status for ['+nameii[0]+'] or quit [q]: ', options_list=['on','off'], soft_quite=True)
		elif nameii[0]=="wallet_encryption":
			newvv=iop.input_prompt('Enter wallet encryption password (min. length 16, max. 32): ', confirm=True, soft_quite=True)
			while (len(newvv)<16  or '"' in newvv or "'" in newvv ) and newvv.lower() not in ['q','']:
				if len(newvv)<16:
					print('Password ['+newvv+'] length is '+str(len(newvv))+' < 16, try again or quit...')
				else:
					print('Password ['+newvv+'] contains forbidden character [",\'], try again or quit...')
					
				newvv=iop.input_prompt('Enter wallet encryption password (min. length 16, max. 32): ', confirm=True, soft_quite=True)
			
			if newvv.lower() in ['q','']:
				newvv=''
			
		else:				
			newvv=iop.input_prompt('Enter new value (enter for empty): ', confirm=True, soft_quite=True)
			
			while nameii[0] in ["outgoing_encryption_key","incoming_encryption_key","gpg_password"] and ('"' in newvv or "'" in newvv):
				print('Password  or key ['+newvv+'] contains forbidden character [",\'], try again or quit...')
				newvv=iop.input_prompt('Enter new value (enter for empty): ', confirm=True, soft_quite=True)
			
		json_conf[nameii[0]]=newvv

	# if toedit=='':
		# print('\n! Exit editing without saving, current setup:')
		# print_current_settings(set_name,json_conf,set_name_alia)
	# else:
		# json_conf=json.dumps(json_conf)
		# iop.saving_encr_cred( json_conf, newest_file, pswd)
		# print('App settings changed - exiting. Please start the app again.')
		# exit()
		
		

def read_app_settings(selected_mode,init_pass=''):

	if not os.path.exists('tmp'):
		os.mkdir('tmp')
		
	
	set_name=['email_addr',"email_password","imap_addr","smtp_addr","tx_amount_limit","tx_time_limit_hours","outgoing_encryption_type","outgoing_encryption_key","incoming_encryption_type","incoming_encryption_key","incoming_mail_sender_email","incoming_mail_title","wallet_secret_key","gpg_password","incoming_tx_notification","staking_summary_notification","wallet_encryption","active_consolidation_address"]
	
	# set_name=['email_addr',"email_password","imap_addr","smtp_addr","tx_amount_limit","tx_time_limit_hours","outgoing_encryption_type","outgoing_encryption_key","incoming_encryption_type","incoming_encryption_key","incoming_mail_sender_email","incoming_mail_title","wallet_secret_key","gpg_password","incoming_tx_notification","staking_summary_notification"]
	
	set_value=["my@email","*****","imap.gmail.com","smtp.gmail.com","1","24","aes256,pgp","keyin","aes256,pgp","keyout","optional","optional","optional","semioptional","off","off","",""]
	
	musthave=['email_addr',"email_password","imap_addr","smtp_addr","tx_amount_limit","tx_time_limit_hours","outgoing_encryption_type","outgoing_encryption_key","incoming_encryption_type","incoming_encryption_key"]
	
	DEAMON_DEFAULTS={}
	for ij,sn in enumerate(set_name):
		DEAMON_DEFAULTS[sn]=set_value[ij].replace("optional","").replace("semioptional","")
		
	json_conf=''	
		
		
	
	newest_date, newest_file, filed = iop.get_config_file()	
	pswd=''
	
	# print(newest_date, newest_file, filed)
	# exit()

	if newest_file!='':
		# print('read file - edit in options then exit and force enter again ... ')
		
		try_decr=True
		decr_str=''
		
		while try_decr:
		
			pp=init_pass
			if pp=='':
				pp=iop.ask_password(newest_file)
			
			try:
				str_rep=iop.decrypt_cred(pp,newest_file) 
				if 'failed' in str_rep:
					print("Your password didn't match the config file ... Try another password or quit [q]")
					if init_pass!='':
						print('Wrong password for config file '+newest_file)
						exit()
					continue
				else:
					decr_str=str_rep.split(iop.lorem_ipsum())
					if len(decr_str)<2:
						print("Your password didn't match the config file ... Try another password or quit [q]")
						if init_pass!='':
							print('Wrong password for config file '+newest_file)
							exit()
						continue
						
					decr_str=decr_str[1]
					try_decr=False
					pswd=pp
			except:
				err_track = traceback.format_exc()
				print(err_track)
				if init_pass!='':
					print('Wrong password for config file '+newest_file)
					exit()
					
				print("Your password didn't match the config file ... Try another password or quit [q]")
				init_pass=''
			
		if try_decr==False:
			json_conf=json.loads(json.dumps(DEAMON_DEFAULTS))
			json_conf_tmp=json.loads(decr_str)
			for jct,vv in json_conf_tmp.items():
				# print(jct,jct in hidden_par)
				
				if jct in json_conf: # and jct not in ["consumer_key",	"consumer_secret"]:
					json_conf[jct]=vv
					if jct in musthave:
						musthave.remove(jct)
					
			if len(musthave)>0:
				print('Elements missing in config file ',str(musthave))
				exit()
	else:
		
		pp=iop.ask_password()
		pswd=pp
		
		json_obj=json.loads(json.dumps(DEAMON_DEFAULTS))
		print('\nCreating new generic config ... ') 
		
		if selected_mode=='deamon':
		
			outuids=[]
			inuids=[]
			for kk in set_name: #json_obj.keys():
				
				if "encryption_type" in kk:
					json_obj[kk]=iop.optional_input('> Enter '+str(kk)+' : ', ['aes256','pgp'], soft_quite=False)
					if json_obj[kk]=='pgp':
						musthave.append("gpg_password")
						if "outgoing" in kk:
							outuids=iop.gpg_uids(False,True)
						else:
							inuids=iop.gpg_uids(True,True)
							
				elif kk == "outgoing_encryption_key" and json_obj["outgoing_encryption_type"]=='pgp':
					json_obj[kk]=iop.optional_input('> Enter '+str(kk)+' : ', outuids, soft_quite=False)
				elif kk == "incoming_encryption_key" and json_obj["incoming_encryption_type"]=='pgp':
					json_obj[kk]=iop.optional_input('> Enter '+str(kk)+' : ', inuids, soft_quite=False)
				# check must have fields are not empty !!! 
				elif kk in musthave:
					strtmp=''
					
					while strtmp=='':
						strtmp=iop.input_prompt('> Enter '+str(kk)+' : ',True,True)
						if strtmp=='':
							print('This value cannot be empty - try again...')
						elif kk=="tx_amount_limit" and not iop.is_float(strtmp):
							print('This value must be numeric - try again...')
						elif kk=="tx_time_limit_hours" and not iop.is_int(strtmp):
							print('This value must be integer - try again...')
								
						else:
							json_obj[kk]=strtmp
				else:
					json_obj[kk]=iop.input_prompt('> Enter value for '+str(kk)+' or hit enter for empty: ',True,True) 
			
			
			print('Creating done, accepted values:\n'+str(json_obj) )
		
		newest_file=list(filed.keys())
		newest_file=newest_file[0]
		
		json_conf=json.dumps(json_obj)
		iop.saving_encr_cred( json_conf, newest_file, pswd)
		
		# encr_str=iop.lorem_ipsum()
		# iop.createtmpfile(encr_str)
	
	return json_conf, pswd
	







# return currency config and deamon config 
def select_currency(autodetect=''):
	
	deamon_list, deamons = available_deamons()
	cur_list, currencies = available_currencies(deamon_list)
	
	if autodetect!='':
		if autodetect in cur_list: #manual input
			return currencies[autodetect], deamons[currencies[autodetect]["deamon-name"]], autodetect
	
		for cl in cur_list: #cc in currencies:
			if currencies[cl]["currency-conf"]["ac_name"]==autodetect:
				print('Autodetected currency ',cl)
				return currencies[cl], deamons[currencies[cl]["deamon-name"]], cl
	
	
	selected_currency=iop.optional_input(propmtstr='Select currency name or quit app:', options_list=cur_list, soft_quite=False)

	return currencies[selected_currency], deamons[currencies[selected_currency]["deamon-name"]], selected_currency



def available_deamons():
	deamons={}
	deamon_list=[]
	deamon_path=os.path.join('config','deamons')
	filelist=os.listdir(deamon_path)

	print('Available deamons:')
	for ff in filelist:

		curf=os.path.join(deamon_path,ff) 
		if os.path.isdir(curf ): # test path is folder
			continue
			
		try:
			fcont=iop.readfile(curf).replace('\\','\\\\')
			# print(fcont)
			tmp_dict=json.loads(fcont)
			
			if not os.path.exists(tmp_dict["deamon-path"]):
				print('Wrong deamon path ['+tmp_dict["deamon-path"]+'] for '+curf)
				continue
			
			if not os.path.exists(tmp_dict["cli-path"]):
				print('Wrong cli path ['+tmp_dict["cli-path"]+'] for '+curf)
				continue
			
			
			tmp_name=ff.replace('.json','').lower()
			deamons[tmp_name]={"path":curf, "deamon-conf":tmp_dict}
			deamon_list.append(tmp_name)
			print(' - '+tmp_name)
		
		except:
			print('Exception with ',curf,os.path.exists(curf))
			
	if len(deamons)==0:
		print('No deamons defined - exit')
		
	return deamon_list, deamons
	
	
	
	
def available_currencies(av_deamons):
	currencies={}
	cur_list=[]
	cur_path=os.path.join('config','currencies')
	filelist=os.listdir(cur_path)

	print('Available currencies:')
	for ff in filelist:

		curf=os.path.join(cur_path,ff) 
		if os.path.isdir(curf ): # test path is folder
			continue
			
		try:
			fcont=iop.readfile(curf).replace('\\','\\\\')
			# print(fcont)
			tmp_dict=json.loads(fcont)
			tmp_name=ff.replace('.json','').lower()
			
			for avd in av_deamons:
				if avd==tmp_dict['deamon'].replace('.json',''):
			
					currencies[tmp_name]={"path":curf, "currency-conf":tmp_dict, "deamon-name":avd}
					cur_list.append(tmp_name)
					print(' - '+tmp_name)
		
		except:
			print('Exception with ',curf,os.path.exists(curf))
			
		
	if len(currencies)==0:
		print('No currencies defined - exit')
		
	return cur_list, currencies
	
	
	
	
def test_gpg():
	try:
		zxc=subprocess.getoutput("gpg --help")
		if '--generate-key' not in zxc:
			print('You need to install GnuPG - for example gnupg4win')
			exit()
	except:
		print('Unknown error')
		exit()
		
	print('GPG ready')
		
