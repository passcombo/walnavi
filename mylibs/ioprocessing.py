# user cmds:
# gpg_uids, edit_addr_book, add_email_addr_book

			
# file encryption:				
# gpg --recipient jim@dundermifflin.com --output dwight.jpg.pgp --encrypt dwight.jpg
# Then attach it to your email like you would any file. When the recipient has recieved the message, they can run the following command to decrypt it:

# gpg --output dwight.jpg --decrypt dwight.jpg.gpg
	

import re
import os
import datetime
import psutil
import traceback
import subprocess
import json
import shutil
from termcolor import colored
import time

import sys, multiprocessing




def check_deamon_running(deamon_cmd):

	is_komodod_running=False
	tmppid=-1
	
	for proc in psutil.process_iter(): # wallet config edit make sense only when komodod not running
		try:
			# Get process name & pid from process object.
			processName = proc.name()
			processID = proc.pid
			
			if ''.join(proc.cmdline())==deamon_cmd: #processName in deamon_cmd: # in processName:
				zxc=proc.as_dict(attrs=['pid', 'memory_percent', 'name', 'cpu_times', 'create_time', 'memory_info', 'cmdline','cwd'])
				print('\n\n\n NOTE: komodod already running',proc.exe(),'\n\n\n' ) # , ' ::: ', processID,zxc)
				
				is_komodod_running=True
				tmppid=zxc['pid']
				break
					
		except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
			x=1
			
	return is_komodod_running, tmppid


def ask_mode(): # mode = wallet or deamon

	options=['wallet','deamon','wal','de']
	# print(colored('hello', 'red'))
	owc='x'
	while owc not in options: #!='wallet' and owc != 'n':
		owc=input("\nSelect mode: ['"+colored('wallet', 'green')+"' or '"+colored('deamon', 'cyan')+"'] ? ") #"\nSelect mode: ['wallet' or 'deamon'] ? ") 
		
		if owc=='q':
			exit()
		
		if owc not in options:
			print(colored("Wrong value, try again", 'red',attrs=['bold'])) #, 'blink'
			
	if owc=='wal':
		return 'wallet'
	elif owc=='de':
		return 'deamon'
		
	return owc



			
def coin_autodetect():

	deamons_list=['komodod','verusd']
	cc=0
	lastproc=''
	
	
	for proc in psutil.process_iter(): # wallet config edit make sense only when komodod not running
		try:
		
			processName = proc.name().replace('.exe','')
			if processName in deamons_list:
				lastproc=proc.cmdline()
				# print('got process ',proc.cmdline())
				cc+=1
					
		except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
			x=1

	
		
	if 'komodod' in ''.join(lastproc) and cc==1: # extract ac name
		
		strm=''.join(lastproc).split('-ac_name=')
		splitminus=strm[1].split('-')
		
		return splitminus[0]
		
	elif 'verusd' in ''.join(lastproc) and cc==1:
		return 'VERUS'
	
	return ''


def input_process(stdin_fd, sq, sstr):
	sys.stdin = os.fdopen(stdin_fd)
	print(colored(sstr,'red',attrs=['bold']))
	try:
		inp = input()
		sq.put(inp)
	except:
		sq.put('')

		
		
def input_in_time(sstr, max_time_sec):
	sq = multiprocessing.Queue()
	p = multiprocessing.Process(target=input_process, args=( sys.stdin.fileno(), sq, sstr))
	p.start()
	t = time.time()
	inp = ''
	iterc=0
	
	while True:
	
		if not sq.empty():
			inp = sq.get()
			# print('inp',inp)
			break
			
		if time.time() - t > max_time_sec:
			break
		
		tleft=int( (t+max_time_sec)-time.time())
		if tleft<max_time_sec-1 and tleft>2 and iterc%10==0:
			print(colored('...time left '+str(tleft)+'s: ','red',attrs=['bold']))
			
		time.sleep(min(2,tleft))
		iterc+=1
		
	p.terminate()
	# sys.stdin = os.fdopen( sys.stdin.fileno() )
	# inp=str(os.fdopen( sys.stdin.fileno() ))+'|'+str(sys.stdin.fileno())
	if inp.lower() in ['q','stop']:
		print('Got',inp,'should end before next iteration')
	else:
		print('...')
	
	if inp.lower()=='q':
		print('Quitting deamon')
		time.sleep(1)
		exit()
		
	return inp





def lorem_ipsum(): #iop.lorem_ipsum()

	litmp="""
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut gravida, nisi sit amet bibendum commodo, mi nulla elementum sapien, rhoncus tempor dui mi ut dolor. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed sollicitudin pulvinar porta. Praesent viverra laoreet accumsan. Sed accumsan mollis diam, quis sollicitudin arcu accumsan non. Proin gravida iaculis sapien ut placerat. Sed vehicula magna in quam interdum aliquet. Nam tempor metus id dui molestie maximus.
"""

	return litmp
	
	
def list_files(dirpath,toprint=False):

	fl=[]
	
	dir_content=os.listdir(dirpath)
	
	for dd in dir_content:
		if os.path.isdir( os.path.join(dirpath,dd) ):
			continue # pass dirs
		fl.append(dd)
		if toprint:
			print(dd)
		
	return fl

	
	
	
def is_float(ff):	
	try: 
		float(ii)
		return True
	except :
		return False
	
	
def is_int(ii):
	try: 
		int(ii)
		return True
	except :
		return False
	
	

# available uids ... 
def gpg_uids(secret=False,toprint=False):

	if toprint:
		print("Available pgp id's:")
	
	stri='gpg -k'
	if secret:
		stri='gpg -K'
	# print('stri',stri)
	str_rep=subprocess.getoutput(stri)
	s1=str_rep.split('<')
	# for si in s1:
		# print('si',si)
	uids=[]
	for ij in range(len(s1)-1):
		
		s2=s1[ij+1].split('>')
		if len(s2)>1:
			uids.append(s2[0])
			
			if toprint:
				print(' '+s2[0])
				
	return uids
	

	
def match_pgp_uid(avuids):

	while True:
		tmpr2=input_prompt('> Enter gpg id - email address should be good enough if it is contained in gpg id: ', True, True)
		
		if tmpr2 in ['','q']:
			return ''
		
		tmpr3=''
		cc=0
		for av in avuids:
			if tmpr2 in av:
				tmpr3=av
				cc+=1
				# break
				
			if cc>1:
				print("Your string ["+tmpr2+"] matches multiple gpg uid - choose a unique one!")
				tmpr3=''
				break
		
		if tmpr3!='':
			print('Matched uid '+tmpr3)
			return tmpr3
		else:
			print('Wrong gpg uid, try again one of: '+str(avuids) )		
		

def select_file(tmppath='my_files'):
	imp_dir_file=''
	while True:
		print('Available files:')
		list_files(tmppath,True)
		imp_dir_file=input_prompt('> Enter file name to import - must be be found inside ['+tmppath+'] director: ', True, True)
		tmp=imp_dir_file
		if imp_dir_file in ['','q']:
			return ''
		
		if tmppath not in imp_dir_file:
			imp_dir_file=os.path.join(tmppath,imp_dir_file)
			
		if os.path.exists(imp_dir_file):
			return imp_dir_file
		else:
			print('No such file ['+tmp+'] in ['+tmppath+'] directory!')
	
#gpg --export-secret-keys $ID > my-private-key.asc
#kgk -K
def manage_keys(passphrase,selcmd): #["gen-key","import","export","export-secret","delete-pub-key","delete-priv-key"]

	imp_dir_file=''
	gpguid=''
	exp_dir_file=''
	pgpkey_ext='.x'
	
	# print('120',selcmd)

	if selcmd =="import":
		# check any file available in the folder
		# print('125')
		imp_dir_file=select_file(tmppath='my_files')
		if imp_dir_file=='':
			return
		
		
	elif selcmd in ["export","export-secret","delete-pub-key","delete-priv-key"]:
		
		if selcmd in ["export","delete-pub-key"]:
			# print('144',selcmd)
			avuid=gpg_uids(False,True)
			# print('145',selcmd)
			gpguid=match_pgp_uid(avuid)
			if gpguid=='':
				return
			exp_dir_file=os.path.join('my_files',gpguid.replace('@','').replace('.','')+pgpkey_ext)
			
		elif selcmd in ["export-secret","delete-priv-key"]:
			avuid=gpg_uids(True,True)
			gpguid=match_pgp_uid(avuid)
			if gpguid=='':
				return
			exp_dir_file=os.path.join('my_files','secret_'+gpguid.replace('@','').replace('.','')+pgpkey_ext)
			
		
	elif selcmd=="gen-key":
		print('')

	cmddict={"gen-key":'gpg --pinentry loopback --passphrase '+passphrase+' --gen-key', 
			"export":'gpg --export --armor '+gpguid+' > '+exp_dir_file, 
			"export-secret":'gpg --pinentry loopback --passphrase '+passphrase+' --export-secret-keys '+gpguid+' > '+exp_dir_file, 
			"import":'gpg --pinentry loopback --passphrase '+passphrase+' --import '+imp_dir_file, 
			"delete-pub-key":'gpg --delete-keys '+gpguid, 
			"delete-priv-key":'gpg --passphrase '+passphrase+' --delete-secret-keys '+gpguid}
	print(cmddict[selcmd])
	str_rep=subprocess.getoutput(cmddict[selcmd])
	print('Exported key '+gpguid+' to my_files directory: '+exp_dir_file)
	


	

def display_msg_dict(msgdict,nomsgfound='',header='\nFound messages:',raw=False):
	
	print(header)
		
	if len(msgdict)<1:
		print(nomsgfound)
		return
		
	ids=[ii for ii in msgdict.keys() ]
	ids.sort(reverse = True) 
	# for rr,rv in msgdict.items():
		# ids.append(int(rv["ID"]))
		
	for ii in ids : #rr,rv in msgdict.items():
		# print(rr,rv)
		rr=ii
		rv=msgdict[ii]
		if raw:
			print(rr,rv)
		else:
			print('ID: '+str(rv["ID"])+' Date: '+str(rv["Date"])+' Attachments: '+str(rv["Attachments"])+' EmailSize: '+str(rv["EmailSize"])+' From: '+xtract_email(rv["From"])+' Subject: '+str(rv["Subject"]) )
		
# def clear_local_mails(json_obj, newest_file, pswd):
	# json_obj["decrypted_mails"]={}
	# saving_encr_cred( json.dumps(json_obj), newest_file, pswd)
	# return json_obj
			
def clear_archive(myfiles=''):
	
	toclear='archive'
	if myfiles=='clear_my_files':
		toclear='my_files'
	
	if os.path.exists(toclear):
		# os.removedirs('archive')
		try:
			shutil.rmtree(toclear, ignore_errors=False)
			time.sleep(3)
			print('Directory cleared!')
			os.mkdir(toclear)
		except:
			print('[!] Could not clear archive.')
	
	
	

		
def print_addr_book(json_conf,only_return=False):
	
	if "address_book" not in json_conf:
		return {}
	
	if not only_return:
		print('\n=============== Address book ===============')
		print('[ALIAS] : [FULL EMAIL ADDRESS] : [ENCRYPTION TYPE] : [ENCRYPTION KEY] : [DECRYPTION KEY]\n')
	
	if len(json_conf["address_book"].keys())==0:
		print('\n ... book is empty ... \n')
		return {}
	
	addr_list=json_conf["address_book"].keys()
	addr_alia=email_address_aliases(addr_list)
	
	for kk in addr_list:
		# ask edit every one separately
		tmp_addr=kk #json_conf["address_book"][kk]
		tmp_alias=addr_alia[kk]
		tmp_encr=json_conf["address_book"][kk]["encryption_type"]
		tmp_decr=''
		try:
			tmp_decr=json_conf["address_book"][kk]["decryption_password"]
		except:
			tmp_decr=''
		# tmp_active='* Not active - encryption missing'
		encr_key=''
		if tmp_encr=='password':
			encr_key=json_conf["address_book"][kk]["password"]
		elif tmp_encr=='pgp':
			encr_key='pgp_id '+json_conf["address_book"][kk]["pgp_id"]
		# if tmp_encr in ['password','pgp']:
			# tmp_active='Yes'
		
		if not only_return:
			print("["+tmp_alias+"] : ["+tmp_addr+"] : ["+tmp_encr+"] : ["+encr_key+"] : ["+tmp_decr+"]")
		
	return addr_alia
		

def email_address_aliases(addr_list): # address_aliases(get_wallet(True))
	alias_map={}
	for aa in addr_list:
		tmpa=aa.replace('@','').replace('.','').lower()
		tmpa=tmpa[:5] #.lower() #+aa[-3:].lower()
		iter=1
		while tmpa in alias_map.values():
			tmpa+=str(iter)
			iter+=1
		
		alias_map[aa]=tmpa #.append([aa, tmpa])
		
	return alias_map		
		
	
def edit_addr_book(json_conf , newest_file, pswd, addroralia=''):

	addr_alia=print_addr_book(json_conf)
	if addr_alia=={}:
		print('Book is empty - cannot edit - first add some addresses ...')
		return #json_conf
	
	avuids=gpg_uids()
	print('\nINFO: Available public keys [gpg uids]: '+str(gpg_uids()))
			
	ync=addroralia

	if ync=='':
		ync=input_prompt("\nEnter alias or address to edit or quit: ", False, True) #'Enter value or quit [q]: '
	
	if ync in ['','q']:
		return
	
	set_key=''
	
	if ync in addr_alia.keys():
		set_key=ync
		
	else:
		for kk in addr_alia.keys():
			if addr_alia[kk]==ync:
				set_key=kk
				break
	
	if set_key!='':
		print("Editing "+set_key)
	
		encr_type=optional_input('> Enter encryption type [none,password,pgp]? Type "del" to remove entire record or quit: ', ['none','password','pgp','del','q'], True)
		
		if encr_type=='del':
			del json_conf["address_book"][set_key]
			
		elif encr_type=='q':
			return
		
		elif encr_type=='password':
			tmpr2=input_prompt('> Enter password: ', True, True)
			json_conf["address_book"][set_key]={"encryption_type": encr_type, "password":tmpr2}
			
		elif encr_type=='pgp' and len(avuids)>0:
			# tmpr2=input_prompt('> Enter pgp id - email address should be good enough if it is contained in pgp id: ', True, True)
			tmpr3=match_pgp_uid(avuids)
			
			
			json_conf["address_book"][set_key]={"encryption_type": encr_type, "pgp_id":tmpr3}
			
		elif encr_type=='pgp':
			print('To use PGP first you need to add some public keys... Try again later.')
			
		# else:
			# json_conf["address_book"][set_key]={"encryption_type": encr_type}
		if encr_type!='del':
			tmpr2=input_prompt('> Enter decryption password [or enter for default pgp]: ', True, True)
			json_conf["address_book"][set_key]["decryption_password"]=tmpr2
			
		saving_encr_cred( json.dumps(json_conf), newest_file, pswd)
	else:
		print("Address or alias ["+ync+"] not found in book...")
	
	
	
	
	


def add_email_addr_book(emadr, json_conf , newest_file, pswd, encr_type='', sym_pass='', decr_pass=''):

	emadr=emadr.strip().lower()
	if encr_type=='password' and sym_pass!='':
		json_conf["address_book"][emadr]={"encryption_type": encr_type, "password":sym_pass}
		saving_encr_cred( json.dumps(json_conf), newest_file, pswd)	
		
	elif encr_type=='pgp':
		json_conf["address_book"][emadr]={"encryption_type": encr_type, "pgp_id":emadr}
		saving_encr_cred( json.dumps(json_conf), newest_file, pswd)	
		
	else:

		ync=optional_input('\nAdd ['+emadr +'] to local address book [y/n]? : ', ['y','n','Y','N']) 
		
		if ync.lower()=='y':
			
			avuids=gpg_uids()
			print('Available public keys [gpg uids]: '+str(avuids))
			
			encr_type=optional_input('> Enter encryption type [none,password,pgp]? ', ['none','password','pgp'], True)
				
			if encr_type=='password':
				tmpr2=input_prompt('> Enter password for encryption: ', True, True)
				json_conf["address_book"][emadr]={"encryption_type": encr_type, "password":tmpr2}
				
			elif encr_type=='pgp' and len(avuids)>0:
				tmpr3=match_pgp_uid(avuids)
				
				
				json_conf["address_book"][emadr]={"encryption_type": encr_type, "pgp_id":tmpr3}
			
			elif encr_type=='pgp':
				print('To use PGP first you need to add some public keys... Try again later.')	
			else:
				json_conf["address_book"][emadr]={"encryption_type": encr_type}
				
			
			# decr_type=optional_input('> Enter decryption password [or enter for default pgp]? ', ['none','password','pgp'], True)
			tmpr2=input_prompt('> Enter decryption password [or enter for default pgp]: ', True, True)
			json_conf["address_book"][emadr]["decryption_password"]=tmpr2
			
			
			print('Added to local address book:\n'+str(json_conf["address_book"][emadr]))
			# json_conf=json.dumps(json_conf)
			saving_encr_cred( json.dumps(json_conf), newest_file, pswd)	
		
	return json_conf #json.loads(json_conf)
	
	


def xtract_email(strt): 
	x=strt.split("<")
	if len(x)>1:
		
		x=x[1].split(">")
		return x[0]
	else:
		return strt


def now_time_str():
	time_format='%Y-%m-%dh%Hm%Ms%S'
	return datetime.datetime.today().strftime(time_format)

		


def readfile(ff):
		
	tmpstr='err'
	try:
		with open(ff, 'r') as f:
						
			tmpstr=f.read()
			f.close()	
			
		return tmpstr
	except:
		return tmpstr
		
		

def save_file(ff,tmpstr,binary=False): #ensure full path exist ... 

	headtail=os.path.split(ff)
	try:
		if not os.path.exists(headtail[0]):
			# print('create path',headtail[0])
			os.makedirs(headtail[0])
	except:
		print("Could not create path ... save file failed ... ")

	try:
	# if True:
		# print(ff)
		wstr='w'
		if binary:
			wstr='wb'
			
		with open(ff, wstr) as f:
						
			f.write(tmpstr)
			f.close()	
			
		return True
	except:
		return False
		
		

def createtmpfile(encr_str='thisissecret'): # used in encrypting via gpg


	if not os.path.isdir( 'tmp' ): # test path is folder
		os.mkdir('tmp')
		
	tmpn=os.path.join('tmp','x.txt')
	with open(tmpn,'w+') as ff:
		ff.write(lorem_ipsum()+encr_str)
		ff.close()
	return tmpn

	
	

def check_already_running(): # ... 

	main_script_name=os.path.basename(__file__)

	script_counts=0
	
	for proc in psutil.process_iter():
		try:
			# Get process name & pid from process object.
			processName = proc.name()
			processID = proc.pid
			if 'python' in processName:
				zxc=proc.as_dict(attrs=['pid', 'memory_percent', 'name', 'cpu_times', 'create_time', 'memory_info', 'cmdline','cwd'])
				
				if main_script_name in str(zxc['cmdline']):
					script_counts+=1
					
		except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
			pass

	if script_counts>1:
		# helpers.log_file(log_file_path,'\n\n__ '+main_script_name+' ALREADY RUNNING __\n\n')
		print('\n\n__ '+main_script_name+' ALREADY RUNNING __\n\n')
		exit()
	else:
		print('Starting...')
		
		
		

	
def fix_equal(strt): # replace " = " with "="
	x=clear_whites(strt)
	x=x.replace('= ','=').replace(' =','=')
	return x		


def clear_whites(strt): # replace multiple spaces with single space
	x=re.sub("\s+", " ", strt)
	x=x.strip()
	return x
	
	
	
	
	

def get_config_file():

	if not os.path.isdir( 'config' ): # test path is folder
		os.mkdir('config')


	filelist=os.listdir('config')
	filed={}
	newest_date=datetime.datetime.strptime('1981-01-01','%Y-%m-%d')
	newest_file=''
	
	for ff in filelist:
		# print(ff)
		if os.path.isdir( os.path.join('config',ff) ): # test path is folder
			continue		
		
		if "gnupg_deamon_cfg_" in ff:
			# print(ff)
			x=re.sub(".*gnupg_deamon_cfg_", "", ff)
			# print(x)
			x=re.sub("\.txt*", "", x)
			
			# print(x,'\n\n\n') # now should be date 2019-12-10
			try:
				
				strdate=datetime.datetime.strptime(x,'%Y-%m-%dh%Hm%Ms%S')

				filed[ff]=strdate
				# print(strdate,newest_date)
				if strdate>newest_date:
					newest_date=strdate
					newest_file=os.path.join('config',ff)
				elif strdate==newest_date:
					print('WARNING! Another config file with the same date! ['+ff+'] Keeping previous one ['+newest_file+']')
				
			except ValueError:
				print('Wrong date string '+x)
				
	if newest_file=='': # makre proposeed file - first one
		ddate=datetime.datetime.now()
		newfname=os.path.join('config',"gnupg_deamon_cfg_"+ddate.strftime('%Y-%m-%dh%Hm%Ms%S')+".txt")
		filed[newfname]=ddate

	return 	newest_date, newest_file, filed

	
		
def testpassbasic(strpass):

	if strpass.lower()==strpass:
		return 'Password should contain some UPPER CAPS!'
	elif strpass.upper()==strpass:
		return 'Password should contain some lower caps!'
	elif len(strpass)<12:
		return 'Password shorter then 12 signs is not allowed!'
	else:
		for ii in range(1,10):
			if str(ii) in strpass:
				return ''
		
		return 'Password should contain at least one number!'
			
# if str contains password - forbid chars are "'|-		
# colored('deamon', 'cyan')	
def input_prompt(propmtstr, confirm=False, soft_quite=False): # input_test should be function returning '' if ok		
	
	propmtstr=colored(propmtstr, 'cyan',attrs=['bold'])	
	
	pp=''
	forbidpass=["'",'"',"|","-"]
	while True: # confirmation loop
		
		pp=str(input(propmtstr)  )
		pp=clear_whites(pp)	
		if pp=='q' or pp=='': # default quit option always avail
			if soft_quite:
				return ''
			else:
				exit()
				
		if 'password' in propmtstr.lower():
			tmpt=False
			for zzz in forbidpass:
				if zzz in pp:
					print('Your password contains forbidden character from list'+str(forbidpass)+':'+zzz+' Try avoiding very special characters - best to use very long alphanumeric passwords.')
					tmpt=True
					break
			if tmpt:
				continue
					
					
				
		if confirm:
			ync=optional_input('Confirm value ['+pp+']? [y/n] or quit [q]:  ', ['y','n','Y','N'],soft_quite) #'Enter value or quit [q]: '
			
			if ync.lower()=='y':
				return pp
			elif ync=='': # soft quit
				return ''
			else: 
				continue
		
		return pp
	
	
	
def optional_input(propmtstr, options_list, soft_quite=False):

	# print(propmtstr)
	propmtstr=colored(propmtstr, 'cyan',attrs=['bold'])	
	
	while True:
		
		pp=str(input(propmtstr) ) 
		
		pp=clear_whites(pp)	
		
		if pp.lower()=='q' or pp.lower()=='quit' or pp.lower()=='exit': # default quit option always avail
			if soft_quite:
				return ''
			else:
				print('Exiting app')
				exit()
			
		splp=pp.split(' ')
		if splp[0] in options_list:
			return pp
		else:
			print('[!] Enterred value must match one of:\n',str(options_list))
			print('    Try again...' )
			
			

			
def ask_password(config_file=''): # mode = wallet or deamon

	propmtstr='Enter strong main password to encrypt your email credentials on this device: '
	if config_file!='':
		propmtstr='Enter relevant main password to decrypt config file ['+config_file+']: '
		
	propmtstr=colored(propmtstr, 'cyan',attrs=['bold'])	
	while True: 
		pp=input(propmtstr)  
		
		if pp=='q':
			exit()
		
		strt='' #testpassbasic(pp)
		if strt=='':
			return pp
			
		else:
			print(strt, 'Try again or quit [q]...')
			
encr_ext='.targz'
# also encrypts file if str_cont is a file!
def encr_msg(str_cont,encr_type,keyorpass,internal_id_str): # fnam should be indexed file ... to not have simmilar names ... save in folder sent ...
	
	fname=os.path.join('tmp','send.txt'+encr_ext)
	# if os.path.exists(fname):
		# os.remove(fname)
	
	str_rep=''
	tmpfile=''
	
	if os.path.exists(str_cont): # if file!!  if tmpfile!='':
		tmpfile=str_cont
		
		headtail=os.path.split(tmpfile)
		fname=os.path.join('archive','sent',headtail[1]+encr_ext)
		
	# print('fname '+fname)
	
	if os.path.exists(fname):
		os.remove(fname)
		
	if not os.path.exists('archive'):
		os.mkdir('archive')
		
	if not os.path.exists( os.path.join('archive','sent') ):
		os.mkdir(os.path.join('archive','sent'))
		
	if encr_type=='aes256':
		gpgstr="gpg --cipher-algo AES256 --pinentry loopback --passphrase " # was "gpg --cipher-algo AES256 -a --pinentry loopback --passphrase "
		if tmpfile=='':
			tmpfile=createtmpfile(str_cont)
		gpg_tmp=gpgstr+keyorpass+" -o "+fname+" -c "+tmpfile
		
		# print('encrypting ... 760 '+gpg_tmp)
		str_rep=subprocess.getoutput(gpg_tmp)
		
	elif encr_type=='pgp':
		# gpg -a -r konrad.kwaskiewicz@gmail.com -o zxcvzxcv.txt -e cel.py
		if tmpfile=='':
			tmpfile=createtmpfile(str_cont)
		gpg_tmp="gpg -r "+keyorpass+" -o "+fname+" -e "+tmpfile # was "gpg -a -r "
		str_rep=subprocess.getoutput(gpg_tmp)
		
	print(str_rep)
	
	if os.path.exists(fname):
		return fname
	
	return '' # if error
	
	


def saving_encr_cred(json_str,fname,pp):

	#gpg --cipher-algo AES256 
	gpgstr="gpg --cipher-algo AES256 -a --pinentry loopback --passphrase "

	if os.path.exists(fname):
		os.remove(fname)

	print('Saving encrypted credentials')
	tmpfile=createtmpfile(json_str)
	gpg_tmp=gpgstr+pp+" -o "+fname+" -c "+tmpfile
	print('Encrypting using gnupg',gpg_tmp)
	str_rep=subprocess.getoutput(gpg_tmp)
	print(str_rep)
	llll=lorem_ipsum()
	createtmpfile(encr_str=llll+llll+llll) #overwrite



# can als odecrypt file if it is legit path [msg_cont]	
def ensure_clear_path(ppath):
	
	if os.path.exists(ppath):
		os.remove(ppath)	

		

def decr_msg2(msg_id,pp,msg_cont,gpgpass='',aes256pp='',print_content=False):

	tryaes=False
	outputfile=''
	decr_file_path=''
	save_copy=''
	fileext=''
	fname='' # encrypted decrypted
	
	if os.path.exists(msg_cont):
	
		decr_file_path=msg_cont
		
		headtail=os.path.split(decr_file_path)
		split_ext=headtail[1].split('.')
		
		if len(split_ext)>2:
			fileext=split_ext[1].lower()
			outputfile='d_'+split_ext[0]+'.'+fileext
			
			if fileext!='txt':# file diff then txt always decrypted to 2 locations? 1. archive 2. my_files
				save_copy=os.path.join('my_files',outputfile)
				
			outputfile=os.path.join(headtail[0],outputfile)
			fname=os.path.join(headtail[0],'decr_'+split_ext[0]+'.'+fileext)
		else:
			outputfile=os.path.join(headtail[0],'d_'+decr_file_path)  # if no extension
			fname=os.path.join(headtail[0],'decr_'+decr_file_path)
			
	else: # create file with content
		fileext='txt'
		decr_file_path=createtmpfile(encr_str=msg_cont)
		outputfile=os.path.join('tmp','z.txt')		
		fname=os.path.join('archive',str(msg_id),'decr_body.txt')
	
	ensure_clear_path(outputfile)
	
	
			
	if aes256pp==''  or aes256pp=='pgp': # if no decrypt pass - first try pgp
		try:
			gpgstr="gpg -o "+outputfile+" -d "+decr_file_path
			if gpgpass!='':
				gpgstr="gpg --pinentry loopback --passphrase "+gpgpass+" -o "+outputfile+" -d "+decr_file_path
								
			str_rep=subprocess.getoutput(gpgstr)
			
			if '@' in str_rep: 
				print('Decrypted using asymetric key file ['+decr_file_path+'] to ['+outputfile+']\n Delete the file after usage to stay safe!')
			else:
				tryaes=True
		except:
			tryaes=True
	else:
		tryaes=True	
		
		
	if tryaes:		
		
		if aes256pp=='':
			aes256pp=input_prompt(propmtstr="Enter password to decrypt message: ", confirm=False, soft_quite=True)
		
		if aes256pp!='':
			gpgstr="gpg -a --pinentry loopback --passphrase "+aes256pp+" -o "+outputfile+" -d "+decr_file_path
			# gpgstr="gpg --cipher-algo AES256 -a --pinentry loopback --passphrase "+aes256pp_ajd+" -o "+tmpdecr+" -d "+msg_cont
			print('cmd847',gpgstr)
			str_rep=subprocess.getoutput(gpgstr)
			# print(gpgstr)
			print(str_rep)
			
			print('Decrypted using password to ['+outputfile+']')
		else:
			print("No password provided - quit decryption...")
	# print('os.path.exists(outputfile)',os.path.exists(outputfile))
	if os.path.exists(outputfile):
	
		retv=readfile(outputfile)
		# print('859',retv)
		os.remove(outputfile)
		return retv.replace(lorem_ipsum(),'')
		
	else:
		return ''
	
	
	
		


		
	
	

def decrypt_cred(pp,newest_file):

	gpgstr="gpg --cipher-algo AES256 -a --pinentry loopback --passphrase "

	return subprocess.getoutput(gpgstr+pp+" -d "+newest_file)

	
	
