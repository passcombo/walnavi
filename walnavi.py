


import os
import smtplib
import time
import imaplib
import email

import sys, multiprocessing, time
from termcolor import colored
# from datetime import datetime
# from datetime import timedelta
import datetime

# from openpyxl import load_workbook
from pandas import DataFrame
import pandas
import subprocess
import json
# import mylibs.wallet_commands as wallet_commands
# import mylibs.helpers as helpers
import mylibs.mailbox as mailbox
import mylibs.process_msgs as msgproc
import mylibs.load_settings as load_settings
import mylibs.ioprocessing as iop
import mylibs.wallet_commands as wallet_commands
os.system('color')
# import platform

if __name__=='__main__':

	
	if not os.path.isdir( 'config' ): # test path is folder
		os.mkdir('config')
		
		if not os.path.isdir( os.path.join('config','addrbooks') ): # test path is folder
			os.mkdir(os.path.join('config','addrbooks'))
		
		if not os.path.isdir( os.path.join('config','currencies') ): # test path is folder
			os.mkdir(os.path.join('config','currencies'))
		
		if not os.path.isdir( os.path.join('config','deamons') ): # test path is folder
			os.mkdir(os.path.join('config','deamons'))
			
		if not os.path.isdir( os.path.join('config','logs') ): # test path is folder
			os.mkdir(os.path.join('config','logs'))
	
	if not os.path.isdir( 'tmp' ): # test path is folder
		os.mkdir('tmp')

	iop.check_already_running()
	auto_cur=iop.coin_autodetect()



	selected_mode=iop.ask_mode() 
	
	pswd=''

	
	load_settings.test_gpg()
	json_conf, pswd=load_settings.read_app_settings(selected_mode) #json_conf["wallet_secret_key"]

	
	if selected_mode=='deamon':
		if mailbox.is_imap_conn_bad( json_conf["email_addr"], json_conf["email_password"], json_conf["imap_addr"]):
			print("Email or password is wrong - cannot connect to mailbox with address ["+json_conf["email_addr"]+"] and password["+json_conf["email_password"]+"]. Edit credentials and run the app again...")
			exit()
		

	selcur,seldeam=load_settings.select_currency(auto_cur)
	
	ac_params_add_node=''
	
	if selcur['currency-conf']["ac_params"].strip()!='':
		ac_params_add_node=selcur['currency-conf']["ac_params"]
		
	if "addnode" in selcur['currency-conf']["addnode"]:
		if len(selcur['currency-conf']["addnode"])>0:
		
			for an in selcur['currency-conf']["addnode"]:
				ac_params_add_node+=' -addnode='+an
		
	FULL_DEAMON_PARAMS=[ seldeam['deamon-conf']['deamon-path'] ]
	
	if selcur['currency-conf']["ac_name"].strip() not in ['','VERUS']:
		FULL_DEAMON_PARAMS=[ seldeam['deamon-conf']['deamon-path'] , "-ac_name="+selcur['currency-conf']["ac_name"]]
		
	
	if len(ac_params_add_node.strip())>1:
		FULL_DEAMON_PARAMS+= ac_params_add_node.split(" ") #"komodod.exe"

	
	if selcur['currency-conf']["datadir"].strip()!='': # adjust data dir
		FULL_DEAMON_PARAMS+=['-datadir='+selcur['currency-conf']["datadir"]]

	CLI_STR=seldeam['deamon-conf']["cli-path"]
	if selcur['currency-conf']["ac_name"].strip() not in ['','VERUS']:
		CLI_STR+=" -ac_name="+selcur['currency-conf']["ac_name"]

	if selcur['currency-conf']["datadir"].strip()!='': # adjust cli for specified path
		CLI_STR+=' -datadir="'+selcur['currency-conf']["datadir"]+'"'

	# print(FULL_DEAMON_PARAMS)
	# print(CLI_STR)
	# print(selcur) # selcur['ac_name']=='VERUS'
	# exit()
		
	json_conf["cur_path_addr_book"]=selcur["path"].replace('.json','.addr').replace('currencies','addrbooks')
	#json_conf["cur_path_addr_book"] addrbooks.XXXX.addr
	
	FEE=selcur['currency-conf']["fee"]
	try:
		FEE=float(FEE)
	except:
		print('WRONG FEE VALUE! ',FEE)
		print('SETTING FEE 0.0001')
		FEE=0.0001
		
		
		
	#####################################################################
	####################### VERIFY wallet is synced

	tmpcond,tmppid=iop.check_deamon_running(''.join(FULL_DEAMON_PARAMS)) #seldeam['deamon-conf']['deamon-path'])

	deamon_started=False

	if not tmpcond:
		subprocess.Popen( FULL_DEAMON_PARAMS) # stdout , stdout=DEVNULL 
		deamon_started=True
		
	SLEEP_TIME=4
	time.sleep(SLEEP_TIME)
	max_iter=777
	deamon_warning="make sure server is running and you are connecting to the correct RPC port"
	# deamon_already_running=False
	zxc=''


	while max_iter>-1:

		print("... CHECKING WALLET STATUS ... ",max_iter)
		try:
		
			zxc=subprocess.getoutput(CLI_STR+" getinfo") # check wallet stat synced
			zxc=str(zxc)
			if 'error message:' in zxc:
				asdf=zxc.split('error message:')
				if len(asdf)>0:
					print(asdf[1])
			# print('****** ZXC \n\n\n ******** \n',zxc)
			# exit()
			if 'is not recognized' in zxc or 'exe' in zxc:
				print('Command ['+CLI_STR+" getinfo"+'] not recognized - wrong path ?')
			
			elif deamon_warning in zxc:
			
				if deamon_started:
					print("\n komodod deamon not responding? ..o.o... [komodod] already running ?.. if this error persists - check system processes and kill [komodod] ")
					
					tmpcond,tmppid=iop.check_deamon_running(''.join(FULL_DEAMON_PARAMS)) #seldeam['deamon-conf']['deamon-path'])
					
					if tmpcond:
						print('Found',tmppid)
						time.sleep(SLEEP_TIME)
						print('Killing process:')
						subprocess.getoutput(CLI_STR+" stop")
						time.sleep(SLEEP_TIME)
						print('Starting komodod:')
						subprocess.Popen( FULL_DEAMON_PARAMS) # stdout , stdout=DEVNULL 
						
						print('Started komodod. Give few seconds to catch up data...')
						time.sleep(SLEEP_TIME)
					
				else:
					print("\n*** DEAMON NOT RUNNING ? - TRY RUNNING DEAMON ***\n") #in new terminal
					
					subprocess.Popen( FULL_DEAMON_PARAMS) #, stdout=DEVNULL  
					print("\n STARTED DEAMON \n")
					deamon_started=True
					time.sleep(SLEEP_TIME)	
					
			else:
			
				y = json.loads(zxc)
				
				while y["longestchain"]==0 :
					print("\n***  ... WAITING PROPER DEAMON STATE... Now: longestchain==0\n")
					time.sleep(3*SLEEP_TIME)	
					zxc=subprocess.getoutput(CLI_STR+" getinfo") # check wallet stat synced
					zxc=str(zxc)
					y = json.loads(zxc)				
				
				if y["longestchain"]==y["blocks"] : #y["synced"]==True:
					print('\nWALLET SYNCED!\n')
					break
				else:
					print('\n... AWAITING WALLET SYNC ...',y["blocks"],y["longestchain"])
					
			
		except:
			print('...wallet syncing...')
			# print("Except",zxc)
		
		time.sleep(SLEEP_TIME)	
			
		max_iter-=1
		


	#####################################################################
	####################### SYNCED	

	COMMANDS=list(set(["help"
			, "help COMMAND"
			, "status"
			# ,"wallet"
			,"newzaddr"
			,"new_taddr" 
			, "send"
			,"stop"
			,"exit"
			,"getinfo"
			, "valaddr"
			,"listunspent"
			, "dispaddrbook"
			])) 
			
	if selected_mode=='wallet':
		COMMANDS.append("addrbook")
		COMMANDS.append("editappsettings")
		print('\n Wallet mode allows to edit address book and app settings.')
		
	if selcur['currency-conf']['ac_name']=='VERUS':
		COMMANDS.append("stake")
		COMMANDS.append("stakestop")
		
		if selected_mode!='wallet':
			opstat=subprocess.getoutput(CLI_STR+" setgenerate true 0")
			print("STAKING ON")
		
			
	COMMANDS.sort()




	CMD_HELP={"COMMAND":"EXAMPLE:\nhelp send"
			, "send":"EXAMPLE:\nsend from=zs1kp6dthe7sperd7n47cm6du4xd3q3kwc785dmz4pyc47xawydygy9ku5y3ha24pspdra4vygk04c to=zs19t5wmas587nvnaw2m5g00vky6v07jyfld2y90l3yj2gsj74qfsmck2szvhr5vjvz0f5vkq4uv8q amount=0.001 \n # you may also use aliasses like:\n send from=zs104c to=zs1v8q amount=0.002"
			, "status":"Show block number and balances"
			, "stop":"Stop komodod and exit script"
			, "exit":"Exit script without stopping komodod"
			, "merge":"merge from=zaddr1,zaddr2,..,zaddrN to=zaddrM"
			, "valaddr":"EXAMPLE:\nvaladdr zs19t5wmas587nvnaw2m5g00vky6v07jyfld2y90l3yj2gsj74qfsmck2szvhr5vjvz0f5vkq4uv8q"}
		
	if deamon_warning not in zxc:
		
		print(wallet_commands.get_status(CLI_STR))
		print( msgproc.helporcmd("help",COMMANDS,CMD_HELP,False) )
		
		
		

	toconfstr=''
	deamon_refresh_basic=120 # 300 sec = 5 min 

	t_last_cmd=datetime.datetime.now()-datetime.timedelta(1, 0, 0)

	wallet_secret_key=json_conf["wallet_secret_key"].strip()


	def format_confirmt_op(tmpstr,addcolor=False):
		am,origa,desta=wallet_commands.extract_from_confirmed_tx(tmpstr)
		if addcolor:
			return colored('CONFIRM','red',attrs=['bold'])+' sending \namount '+str(am)+'\nfrom address '+origa+'\nto address '+desta
		else:
			return 'CONFIRM'+' sending \namount '+str(am)+'\nfrom address '+origa+'\nto address '+desta
		

	# citer=4
	# better set working time 

	# dict_income, print_str = wallet_commands.check_for_new_tx(CLI_STR,wallet_commands.cur_name(json_conf))
	# print(print_str)
	# exit()
					
	while deamon_warning not in zxc: # and citer>0: 


		if selected_mode=='wallet':	
			wallet_mode_limits={}
			wallet_mode_limits["tx_amount_limit"]='999999'
			wallet_mode_limits["tx_time_limit_hours"]='1' # no limits when wallet mode!
			# print()
			time.sleep(0.5)
			user_cmd=iop.input_prompt("\nEnter your command:", confirm=False, soft_quite=True)    #input()
			user_cmd=iop.clear_whites(user_cmd)
			
			
			if user_cmd.lower() in ['confirm','confirmed'] and toconfstr!='':
				user_cmd=toconfstr
				
			elif toconfstr!='':
				print('Cancelled previous operation')
				toconfstr=''
				user_cmd=''
				
			if user_cmd!='':
				cmd_res=msgproc.cmd_process(user_cmd,COMMANDS,CMD_HELP,FEE,json_conf,CLI_STR,pswd,wallet_mode_limits)
				
				if 'CONFIRM OPERATION:: ' in cmd_res:
					toconfstr=cmd_res
					cmd_res=format_confirmt_op(cmd_res,True)
				else:
					toconfstr=''
				
				print(cmd_res)
		
		elif selected_mode=='deamon':
		
			# citer-=1
			deamon_subject='Cogito ergo sum'
				
			sender_email=json_conf["email_addr"]
			
			if json_conf["incoming_mail_sender_email"].strip()!='':
				sender_email=json_conf["incoming_mail_sender_email"].strip()
			
			sender_to=''
			if json_conf["incoming_mail_sender_email"].strip()!='':
				sender_to=json_conf["incoming_mail_sender_email"].strip()
			
				
			
			FROM_EMAIL=json_conf["email_addr"]
			FROM_PWD=json_conf["email_password"]
			SMTP_SERVER=json_conf["smtp_addr"]
			IMAP_SERVER=json_conf["imap_addr"]
			DEFAULT_RECEIVER=json_conf["incoming_mail_sender_email"].strip()
			if DEFAULT_RECEIVER=='':
				DEFAULT_RECEIVER=FROM_EMAIL
			
			title_contains=json_conf["incoming_mail_title"]
			
			def_opt={'last_msg_limit':555,'from':'any', 'subject':'any', 'only_new':'yes'}
			if title_contains!='':
				def_opt['subject']=title_contains
			if sender_email!='':
				def_opt['from']=sender_email
		
			
			msg_obj_list,iilist=mailbox.search_incoming(FROM_EMAIL , FROM_PWD , IMAP_SERVER, def_opt)
			
			potlist=['','','','']
			
			
			if len(iilist)==0:
				print("No new command... "+str(datetime.datetime.today()))
				if toconfstr=='':
					# print('checking for new income')
					dict_income, print_str = wallet_commands.check_for_new_tx(CLI_STR,wallet_commands.cur_name(json_conf))
					# HERE ALSO CHECK FOR NEW INCOMING TX confirmations < 5 and send only once ! 
					if print_str!='':
						# print('found',print_str)
						# deamon_refresh_basic=1
						# print_str='New session started - will check for new commands every 30 seconds since now\n'+print_str
						
						potlist=mailbox.send_input(json_conf ,pswd, False, False, msg_receiver_s=[DEFAULT_RECEIVER],subj=deamon_subject, sent_msg_cont=print_str)	
					# else:
						# print('nothing')
			
			else:
				iilist.sort() # process from olest to newest
				cmd=''
				lastii=-1
				cmd_res=''
				cur_msg_obj=''
				orig_cmd=''
				for ii in iilist:
					
					lastii=msg_obj_list[ii]['ID']
					# continue
					cur_msg_obj=msg_obj_list[ii]
					
					cmd=msgproc.decrypt_msg(json_conf,cur_msg_obj['ID'], pswd, json_conf['gpg_password'], aes256pp=json_conf['incoming_encryption_key'])
					
					orig_cmd=cmd
					
					if cmd is None:
						cmd=''
					
					if wallet_secret_key!='':
					
						if wallet_secret_key not in cmd:
							cmd_res='Wallet secret key missing....'
							cmd=''
						else:
							cmd=cmd.replace(wallet_secret_key,'').strip()
							
					if cmd!='':
						
						multilinespl=cmd.split('\n')
						# print('multilinespl',multilinespl)
						cmd=''
						found_cmd=False
						for mm in multilinespl:
						
							# print('mm',mm)
							if len(mm)>1:
								cmds=mm.split(' ')
								# print('cmds',cmds)
								if len(cmds)>0 and cmds[0].lower() in ['confirm','confirmed'] and toconfstr!='':
									cmd=toconfstr
									found_cmd=True
									break
								elif toconfstr!='':
									cmd_res='No confirmation. Cancelled previous operation.'
									toconfstr=''
									cmd=''
									continue
								elif cmds[0].lower() in COMMANDS:
									cmd=cmds[0]
									found_cmd=True
									break
						
						if found_cmd:
							break
					
					
				newto=mailbox.get_new_to_addr_list(json_conf["email_addr"],cur_msg_obj)
				
				msg_receiver_s=newto
				if sender_to!='': # if not configured- reply to asking email 
					msg_receiver_s=[sender_to]
						
				if cmd!='':
				
					t_last_cmd=datetime.datetime.now()
					# print('442 cmd',cmd)
					if cmd!='':
						cmd_res=msgproc.cmd_process(cmd,COMMANDS,CMD_HELP,FEE,json_conf,CLI_STR,pswd)
					
						if 'CONFIRM OPERATION:: ' in cmd_res:
							toconfstr=cmd_res
							cmd_res=format_confirmt_op(cmd_res)
						else:
							toconfstr=''
						
						# print(cmd_res)
					if deamon_refresh_basic==120:
						deamon_refresh_basic=30
						cmd_res='New session started - will check for new commands every 30 seconds since now\n'+cmd_res
						print('new session started - will check for new comds every 30 seconds since now')
						
					potlist=mailbox.send_input(json_conf ,pswd, False, False, msg_receiver_s=msg_receiver_s ,subj=deamon_subject, sent_msg_cont=cmd_res)		
				else:
					
					# print('Message id nr didnt contain proper command or wallet secret key was missing if configured?')
					if cmd_res=='':
						cmd_res='Message id '+str(lastii)+" didn't contain proper command. Available commands:\n"+'\n'.join(COMMANDS)
						
					cmd_res+='\n Orig message:\n'+orig_cmd
					potlist=mailbox.send_input(json_conf ,pswd, False, False, msg_receiver_s=msg_receiver_s,subj=deamon_subject, sent_msg_cont=cmd_res)		
			
			if potlist[0]!='':
			
				for pt in potlist:
					
					msg_receiver=pt[2]
					file_att=pt[0]
					subj=pt[1]
					text_part=pt[3]
					
					if msg_receiver=='':
						continue
					else:
						# print("MSG:\n"+)
						retv=mailbox.send_email(SMTP_SERVER,FROM_EMAIL, FROM_PWD, FROM_EMAIL, msg_receiver, [file_att] , subj, text_part)
						print(retv)
			
			if datetime.datetime.now() - t_last_cmd <datetime.timedelta(0, 600, 0):
				# print('485 cmd',datetime.timedelta(0, 600, 0), t_last_cmd,datetime.datetime.now())
				deamon_refresh_basic=30
				
			elif deamon_refresh_basic==30:
				deamon_refresh_basic=120
				
				cmd_res='Session ended - now checking for new commands every 2 minutes.'
				# if msg email not configured - will send to self 
				potlist=mailbox.send_input(json_conf ,pswd, False, False, msg_receiver_s=[DEFAULT_RECEIVER],subj=deamon_subject, sent_msg_cont=cmd_res)
				# print(potlist)
				retv=mailbox.send_email(SMTP_SERVER,FROM_EMAIL, FROM_PWD, FROM_EMAIL, potlist[0][2] , [potlist[0][0]] , potlist[0][1], potlist[0][3])
				print(retv)
			
			toquit=''
			toquit=iop.input_in_time("Enter 'q' to quit deamon or 'stop' to quit and stop komodod:", deamon_refresh_basic-1)
			# tsd=time.time()
			# print('Break for '+str(deamon_refresh_basic)+' seconds...')
			# while time.time() - tsd < deamon_refresh_basic:
				# time.sleep(1)
				# if toquit!='':
					# break
			
			
			if toquit.lower()=='stop':
				# print('deamon_warning',deamon_warning)
				if deamon_warning not in zxc:
				
					zzz=subprocess.getoutput(CLI_STR+" stop")
					print('\nKOMODOD STOP\n',zzz)
					time.sleep(11)
					exit()
			
				
					# mailbox.last_proc_mail_id(mail_id=cc)
		if selected_mode=='deamon':
			print('Next iteration')	
		zxc=str(subprocess.getoutput(CLI_STR+" getinfo"))


		
		
		


	
