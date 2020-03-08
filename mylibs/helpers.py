
import os
import smtplib
import time
import imaplib
import email
import datetime
from termcolor import colored
from pandas import DataFrame
import pandas
import subprocess
import json

import re
import psutil # pip install psutil


		
def input_prompt(propmtstr, confirm=False, soft_quite=False): # input_test should be function returning '' if ok		
	
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

	if cc==1: # extract ac name
	
		strm=''.join(lastproc).split('-ac_name=')
		
		splitminus=strm[1].split('-')
		
		return splitminus[0]
	
	return ''
	
	# print('total deamons',cc)



def check_deamon_running(deamon_cmd):

	is_komodod_running=False
	tmppid=-1
	
	for proc in psutil.process_iter(): # wallet config edit make sense only when komodod not running
		try:
			# Get process name & pid from process object.
			processName = proc.name()
			processID = proc.pid
			# if 'komodod' in processName:
				# print(deamon_cmd)
				# print('\n')
				# print(''.join(proc.cmdline()) )
				# print(''.join(proc.cmdline())==deamon_cmd)
				# exit()
				# print(proc.exe())
			if ''.join(proc.cmdline())==deamon_cmd: #processName in deamon_cmd: # in processName:
				zxc=proc.as_dict(attrs=['pid', 'memory_percent', 'name', 'cpu_times', 'create_time', 'memory_info', 'cmdline','cwd'])
				print('\n\n\n NOTE: komodod already running',proc.exe(),'\n\n\n' ) # , ' ::: ', processID,zxc)
				# edit_wallet_deamon=False
				is_komodod_running=True
				tmppid=zxc['pid']
				break
					
		except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
			x=1
			# print('Some exception checking komodod running ... ')
	
	return is_komodod_running, tmppid




def now_time_str():
	time_format='%Y-%m-%dh%Hm%Ms%S'
	return datetime.datetime.today().strftime(time_format)



def clear_whites(strt): # replace multiple spaces with single space
	x=re.sub("\s+", " ", strt)
	x=x.strip()
	return x
	
def fix_equal(strt): # replace " = " with "="
	x=clear_whites(strt)
	x=x.replace('= ','=').replace(' =','=')
	return x
	

def is_num(ii):
	try: 
		float(ii)
		return True
	except :
		return False
		

def write_json_str(ff,rd):

	with open(ff, 'w') as f:
					
		jsd=json.dumps( rd)
		f.write(str(jsd))
		f.close()
		
		
		
		
def save_file(ff,tmpstr):

	with open(ff, 'w') as f:
					
		f.write(tmpstr)
		f.close()	
		
		


def readfile(ff):
		
	tmpstr='err'
	try:
		with open(ff, 'r') as f:
						
			tmpstr=f.read()
			f.close()	
			
		return tmpstr
	except:
		return tmpstr		
		

# id may be usefull for deleting msg after few minutes ...
def msg_id(msg_str,file_path=os.path.join("logs","zmsglogs.txt") , msg_id_file=os.path.join("logs","zmsgid.txt") ): # id may be needed to not read again passed emails ?
	# print('enter msg id')
	msg_id=0
	try:
		with open(msg_id_file, 'r') as f: # read last id
			msg_id=int(f.read())
			f.close()
	except:
		print("\n Wrong msg id in the file or zmsgid.txt file missing, using 0.")
	# print(392)	
	msg_id+=1
	try:
		with open(msg_id_file, 'w+') as f: # overwrite last id
		
			f.write( str(msg_id) )
			f.close()
	except:
		print("\n Could not save msg id ...")
	
	# print(401)
	try:
		
		x=datetime.datetime.today()
		time_format='%Y-%m-%d %H:%M:%S'

		x1=x.strftime(time_format)
		with open(file_path, 'a+') as f: # add msg
			f.write( str(x1)+' '+str(msg_id)+' '+msg_str+'\n' )
			f.close()
	except:
		print("\n Could not save msg log ...")
				
		

def sent_log_append(amnt,addr_from,addr_to,file_path=os.path.join("logs","zlogs.txt") ): # saving tx done

	x=datetime.datetime.today()
	time_format='%Y-%m-%d %H:%M:%S'

	x1=x.strftime(time_format)
	# print('writing',str(amnt),str(addr_from),str(addr_to))
	with open(file_path, 'a+') as f:
		f.write(str(x1)+';'+str(amnt)+';'+str(addr_from)+';'+str(addr_to)+' \n')
		f.close()

		
def sent_log_read(file_path=os.path.join("logs","zlogs.txt")):

	if os.path.exists(file_path):
		return pandas.read_csv(file_path,";",names=['date_time','amount','addr_from','addr_to'],parse_dates=['date_time'],infer_datetime_format=True)

	return DataFrame()	
	
	
	
	


def get_available_limited_balance(DEAMON_DEFAULTS): # based on historical spends 
	
	df=sent_log_read()
	# print(df)
	if len(df)==0:
		print("! could not read log file zlog.txt to verify limits used. No file or file empty- allow max tx.")
		
		return float(DEAMON_DEFAULTS["tx_amount_limit"])
		# return -1 
	# aggregate to have total balance used in current_time >current time - DEAMON_DEFAULTS["tx_time_limit_hours"]
	
	cur_time=pandas.Timestamp('today') #datetime.datetime.today()
	min_time = cur_time - pandas.Timedelta(hours=int(DEAMON_DEFAULTS["tx_time_limit_hours"]))

	filter_id = (df['date_time'] > min_time) & (df['date_time'] <= cur_time) 
	tmpdf = df.loc[filter_id]
	if tmpdf.empty:
		return float(DEAMON_DEFAULTS["tx_amount_limit"])
		
	# print(tmpdf)
	usedlimit=tmpdf['amount'].sum()
	
	return float(DEAMON_DEFAULTS["tx_amount_limit"]) - usedlimit

	
	

def get_key_eq_value(str_base,str_extract):	# extracting values from "key=value" in sending transaction...

	if 'from' in str_extract:
		str_extract='from'
	elif 'to' in str_extract:
		str_extract='to'

	tmpstr=str_base.split(str_extract+'=')
	
	if len(tmpstr)!=2:
		return "["+str_extract+"] is missing in the command "+str_base
		
	tmpstr=tmpstr[1].split(' ')
	
	return tmpstr[0]
		
		
# grey
# red
# green
# yellow
# blue
# magenta
# cyan
# white
# text = colored('Hello, World!', 'red', attrs=['reverse', 'blink'])
# Attributes:

# bold
# dark
# underline
# blink
# reverse
# concealed
def ask_mode(): # mode = wallet or deamon

	options=['wallet','deamon','wal','de']
	# print(colored('hello', 'red'))
	owc='x'
	while owc not in options: #!='wallet' and owc != 'n':
		owc=input("\nSelect mode: ['"+colored('wallet', 'green')+"' or '"+colored('deamon', 'cyan')+"'] ? ") #"\nSelect mode: ['wallet' or 'deamon'] ? ") #colored('hello', 'red')
		if owc not in options:
			print(colored("Wrong value, try again", 'red',attrs=['bold'])) #, 'blink'
			
	if owc=='wal':
		return 'wallet'
	elif owc=='de':
		return 'deamon'
		
	return owc



########## MANAGE DEFAULT CONFIG FILES



def edit_dict(rd,default_dict): # 

	for ik in rd.keys():
		if ik not in default_dict.keys():
			if '-wrong key-' not in rd[ik]:
				rd[ik]=rd[ik]+'-wrong key-'
			continue #print("\nSkipping wrong key ["+ik+"] in "+dict_file)
		else:		
		
			owc='x'
			while owc!='y' and owc != 'n':
				owc=input("\n...Processing ["+ik+"]=["+rd[ik]+"]. Do you want to edit or skip this value ? [y=edit / n=skip]: ")
				if owc!='y' and owc != 'n':
					print("Wrong value, try again")
					
			if owc=='n':
				print("Skipping ["+rd[ik]+"]")
				continue
			
			print("Editing ["+rd[ik]+"]")
			accept=False
			while accept==False:
				nv=str(input("Enter new value for "+ik+" current value "+rd[ik]+":"))
				nv=nv.strip()
				
				# special case - numbers - check auto!
				# if ik is not numerical type expected or is correct numerical value then ask for conf
				if is_num(nv) or ik not in ['tx_amount_limit','tx_time_limit_hours','fee']:
				
					owc='x'
					while owc!='y' and owc != 'n':
						owc=input("You have entered '"+nv+"' is it ok [y/n]?")
						if owc!='y' and owc != 'n':
							print("Wrong value, try again")
					if owc=='y':
						accept=True
				
			rd[ik]=nv

	# add missing keys:
	for ik in default_dict.keys():
		if ik not in rd.keys():
			print('\n*** adding missing key',ik,default_dict[ik])
			rd[ik]=default_dict[ik]
			
	return rd




def ask_edit(wc,rd,ff,ddict): # ask forced if value numbers wrong ... 

	force_edit=False
	
	for tt in ['tx_amount_limit','tx_time_limit_hours','fee']:
		if tt in rd:
			if is_num(rd[tt])==False:
				force_edit=True
				print('\n FORCE EDIT - wrong numerical values',tt)
				break
	print('\nCURRENT VALUES for ',ff)
	# print(rd)
	for ik in ddict.keys():
		# print(ik,'vs',str(rd))
		if ik not in rd.keys():
			print('### adding missing key |'+ik+'| ['+ddict[ik]+']')
			rd[ik]=ddict[ik]
		print('|'+ik+'| ['+rd[ik]+']')

	if force_edit or wc and rd!='': # prompt for editing

		owc='x'
		while owc!='y' and owc != 'n':
			owc=input("\nEdit config file "+ff+" [y/n]? :")
			if owc!='y' and owc != 'n':
				print("Wrong value, try again")
				
		if owc=='y':	
		
			rd=edit_dict(rd,ddict)
			print("Config editing finished. These values will be used in current run and saved to config file:\n"+str(rd) )
			print("\nNow trying to save these values in the file for future runs...")
	
			try:
				
				fr=fr.replace("\\\\","\\") # when saving on windows ...
				write_json_str(ff,rd)
				
				print("SUCCESS")
			except:
				print("FAILED - permissions missing or low disk space or sth else ... ")	
		


	

def create_config_file_if_not_exist(dict_file,default_dict):
	
	if os.path.isfile(dict_file)==False:
		print("\nConfig file not found: ["+dict_file+"]. Creating this file with default values for future purpose.")
		try:
			
			write_json_str(dict_file,default_dict)
			
			return True, default_dict  # file exist now
			
		except:
			print("\nCould not create file. Wrong permissions, small disk free space or another issue...")
			return False,''
	else: # validate file:

		with open(dict_file, 'r') as f:
			strjs=''
			try:
				fr=f.read()
				fr=fr.replace("\\","\\\\")
				# print('\nfr\n',fr,'\n')
				tmpstr=str(fr).strip()
				# print('\ntmpstr\n',tmpstr,'\n')
				strjs=json.loads( tmpstr )
			except:
				print("\nFile is corrupt? Coma missing or sth? Not proper json: ["+dict_file+"]\n Delete it or change name and run again to reconfigure... It will not be used in current run. Best not to use \\ escape signg ... ")
				
			f.close()
			print('\nRead file ['+dict_file+']')
			return True, strjs
			
	return True,'' # file exist already

	
	

def get_dict_config(dict_file,default_dict): # IF FOUND FILE BEFORE - ask to reconfig! maybe move the part detecting missing file ?

	print("\n...Enter get_dict_config")
	
	if os.path.isfile(dict_file):
		
		print("Found: ["+dict_file+"]")
		
		with open(dict_file, 'r') as f:
		
			try:
			
				fr=f.read()
				fr=fr.replace("\\","\\\\")
				# print('\nfr\n',fr,'\n')
				tmpstr=str(fr).strip()
				
				strjs=json.loads(tmpstr) # str(f.read()).strip() )
				# print(strjs)
				
				for ik in strjs.keys():
					if ik not in default_dict.keys():
						print("Skipping wrong key ["+ik+"] in "+dict_file)
					else:
						if default_dict[ik]!=strjs[ik]:
							print("Overwrite default key ["+ik+"] value["+default_dict[ik]+"] changed to ["+strjs[ik]+"]")
							default_dict[ik]=strjs[ik].strip()
			except:
				print("!!! File is corrupted? Coma missing or sth? Not proper json: ["+dict_file+"]\n Delete it or change name and run again to reconfigure...")
				
			f.close()
	else:
		print("??? File not found: ["+dict_file+"]. Will use default values.")

	print("Ending get_dict_config\n")
	return default_dict

	
	
	
	

	
	