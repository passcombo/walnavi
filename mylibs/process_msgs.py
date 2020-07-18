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
# import mylibs.helpers as helpers
import mylibs.mailbox as mailbox
import mylibs.wallet_commands as wallet_commands
import mylibs.load_settings as load_settings

import mylibs.ioprocessing as iop
import re


# ensure paths!
# dodac detekcje komendy!

def decrypt_msg(json_obj,msg_id, pp, gpgpass, aes256pp): # decr body content ...

	mail_from=json_obj["email_addr"]	
	mail_from_pswd=json_obj["email_password"]
	imap_addr=json_obj["imap_addr"]
	
	msg_obj=mailbox.read_msg_id(mail_from , mail_from_pswd , imap_addr, msg_id)
	
	# print(msg_obj)
	# return
	# {"from":sender_email, "subj":subj, "body":msgraw, "attachments":files_att, "body_html":msghtml}
	# save to tmp file
	# decrypt and return command
	# overwrite file 
	test_body_cmd=iop.decr_msg2(msg_id,pp,msg_obj["body"],gpgpass,aes256pp)
	# print('XXX ',test_body_cmd)
	# print('ZZZ ','failed' not in str(test_body_cmd))
	if test_body_cmd!='':
		# print(test_body_cmd)
		return test_body_cmd
	# zxcv=detect_command(test_body_cmd)
	
	else:
		print('failed to decrypt body...')
		for ff in msg_obj["attachments"]:
			att_downloaded_list=mailbox.download_msg_id_att(mail_from , mail_from_pswd , imap_addr, msg_id, ff)
			# print(att_downloaded_list, att_downloaded_list[0],gpgpass,aes256pp)
			# tmppath=os.path.join('archive',str(msg_id),ff)
			dm=iop.decr_msg2(msg_id,pp,  att_downloaded_list[0] ,gpgpass,aes256pp)
			# print(dm)
			# zxcv=detect_command(dm)
			if dm!='':
				return dm
				# break
				
	
				
	









def helporcmd(ucmd,COMMANDS,CMD_HELP,html=True):

	tmpcmdhelp =  {k.lower(): v for k, v in CMD_HELP.items()}

	tmphtml_1=' '
	tmphtml_2=' , '
	
	if html==False:		
		tmphtml_1=''
		tmphtml_2='\n'

	retv=''
	if "help" in ucmd.lower():
	
		tmp=ucmd.split(' ')
		if len(tmp)==1:
	
			retv+=tmphtml_2+tmphtml_1+"AVAILABLE COMMANDS:"+tmphtml_2
			# print("\nAVAILABLE COMMANDS:\n" )
			for iicmd in COMMANDS:
				# print(iicmd)
				retv+=tmphtml_1+iicmd+tmphtml_2
			
		elif len(tmp)==2:
			# print(tmpcmdhelp,tmp[1].lower())
			if tmp[1].lower() in tmpcmdhelp: #CMD_HELP:
				retv+=  tmpcmdhelp[tmp[1].lower()]+"\n"#CMD_HELP[tmp[1]]+"\n"
				# print('\n'+CMD_HELP[tmp[1]])
			else:
				retv='\nThis command does not exist or is too simple to need additional help...'
				# print('\nThis command does not exist or is too simple to need additional help...')
		
	# print('OK???',retv)	
		
	return retv

	
# IMPORTANT : EXIT OUTSIDE! cmd_process

def cmd_process(user_cmd,COMMANDS,CMD_HELP,FEE,DEAMON_DEFAULTS,CLI_STR,pswd,wallet_mode_limits={}):
	
#	print('start',user_cmd)
	is_special_cmd=False
	
	user_cmd=iop.clear_whites(user_cmd)
	ucmdlow=user_cmd.lower()
	# ucmdlow=user_cmd.replace("= ","=").replace(" =","=")
	
	cmdsplit=ucmdlow.split()
	cmd_name=cmdsplit[0]
#	print('cmd_name',cmd_name)
	
	# if 'valaddr' in ucmdlow or 'help' in ucmdlow or 'history' in ucmdlow or 'send' in ucmdlow or 'z_getoperationstatus' in ucmdlow or 'merge' in ucmdlow:
	if 'confirm operation::' in ucmdlow or cmd_name in ['valaddr','help','history','send','z_getoperationstatus','merge']:
		is_special_cmd=True
		# print(user_cmd,'confirm operation::' in user_cmd)
		
	if 'dispaddrbook'==cmd_name :
		return load_settings.external_addr_book(wallet_commands.get_wallet(CLI_STR,True),DEAMON_DEFAULTS["cur_path_addr_book"],pswd,CLI_STR,True)
	
	elif 'addrbook' == cmd_name :
		load_settings.external_addr_book(wallet_commands.get_wallet(CLI_STR,True),DEAMON_DEFAULTS["cur_path_addr_book"],pswd,CLI_STR)
		return ''
		
	elif cmd_name=='editappsettings':
		load_settings.edit_app_settings(DEAMON_DEFAULTS,pswd)
		return ''
		
	elif cmd_name in COMMANDS or is_special_cmd: #"send" in ucmd
	
#		print(114,cmd_name)
		if cmd_name=="exit" or cmd_name=="q": # only make sense fo wallet not deamon
			print("...Exiting...")
			print("Cryptocurrency deamon still running until you use command 'stop'")
			exit()
			
		elif cmd_name=="help":	
			# print(120)
				
			return helporcmd(ucmdlow,COMMANDS,CMD_HELP,False)
			
		else:	
			# print(125)
			# try:
			if True:
			
				tmp_deamon_defaults=DEAMON_DEFAULTS.copy()
			
				if cmd_name in ['send','status'] and len(wallet_mode_limits)>0:
					# wallet mode chenge limits:
					# DEAMON_DEFAULTS["tx_amount_limit"]=wallet_mode_limits["tx_amount_limit"]
					# DEAMON_DEFAULTS["tx_time_limit_hours"]=wallet_mode_limits["tx_time_limit_hours"] 
					tmp_deamon_defaults["tx_amount_limit"]=wallet_mode_limits["tx_amount_limit"]
					tmp_deamon_defaults["tx_time_limit_hours"]=wallet_mode_limits["tx_time_limit_hours"] 
				
				cmd_res=wallet_commands.process_cmd(load_settings.get_addr_book(tmp_deamon_defaults["cur_path_addr_book"],pswd), FEE,tmp_deamon_defaults,CLI_STR,user_cmd)
				
				if 'CONFIRM OPERATION:: ' in cmd_res:
					return cmd_res
				else:
					if cmd_name.lower()=='status':
						cmd_res+=load_settings.external_addr_book(wallet_commands.get_wallet(CLI_STR,True),tmp_deamon_defaults["cur_path_addr_book"],pswd,CLI_STR,True)
				
					return "\nCOMMAND RESULT:\n"+cmd_res
			
	else:
		return "\nYour command ["+user_cmd+"] not matching any of\n"+str(COMMANDS )
		



def save_msg(kk,msg,file=''):

	tmpf=''
	if file=='':
		tmpf=os.path.join('archive','inbox','msg_id_'+str(kk)+'.txt')
	else:
		tmpf=file
	
	with open(tmpf, 'w+') as f: # overwrite last id
		
		f.write( str(msg) )
		f.close()

		
		
		
def readcurrentdecry():

	tmpf=os.path.join('archive','inbox','proc','currentd.txt')
	msg_d=''
	with open(tmpf, 'r') as f: # overwrite last id
		
		msg_d=iop.clear_whites(f.read())
		f.close()
		
	os.remove(tmpf)
		
	return msg_d


def process_main(msg_dict,fullgpgpass,simplepass=''):
	
	
	full_gpg_cmd="gpg --pinentry loopback --passphrase "+fullgpgpass #+" -o "++" -d "+
	simple_gpg="gpg --pinentry loopback --passphrase "+simplepass
	
	commands={}
	
	for k in sorted(msg_dict):
		# print(k,msg_dict[k])
		save_msg(k,msg_dict[k])
		
		# iter=0
		for manymsg in msg_dict[k]:
			tmpf=os.path.join('archive','inbox','proc','current.txt')
			# print(tmpf)
			save_msg(0,manymsg,file=tmpf)
			
			# first try RSA
			
			str_rep=subprocess.getoutput(full_gpg_cmd+" -o "+tmpf.replace('current.txt','currentd.txt')+" -d "+tmpf)
			
			if 'RSA' in str_rep:
				print('Assume correct RSA')
				# print(k,'RSA',readcurrentdecry())
				# commands.append({k:readcurrentdecry()})
				commands[k]=readcurrentdecry()
				
			elif 'AES' in str_rep:
				print('Assume error - try AES')
				str_rep=subprocess.getoutput(simple_gpg+" -o "+tmpf.replace('current.txt','currentd.txt')+" -d "+tmpf)
				# print(k,'AES',readcurrentdecry())
				# commands.append({k:readcurrentdecry()})
				commands[k]=readcurrentdecry()
			else:
				print('Decrypt failed')
				
			os.remove(tmpf)
		
			
	return commands		
	
	
	
	
def encrypt_msg(msg_content,mid,rsa_pass='',aes_pass=''):

	tmp_path1=os.path.join('archive','outbox','proc','tmpmsg.txt')
	
	with open(tmp_path1, 'w+') as f:
					
		f.write(msg_content)
		f.close()	

	# h_head,t_tail=os.path.split(somefile)
	tmp_path2=os.path.join('archive','outbox','proc','at_'+str(mid)+'_'+iop.now_time_str()+'.txt')
	# ofile=os.path.join(h_head,'current_encr.txt')
	
	if rsa_pass=='':
		str_gpg="gpg --cipher-algo AES256 --pinentry loopback --passphrase "+aes_pass+" -o "+tmp_path2+" -a -c "+tmp_path1
	else:
		str_gpg="gpg --pinentry loopback --passphrase "+rsa_pass+" -o "+tmp_path2+" -a -d "+tmp_path1
		
	# print('Encrypting '+str_gpg)
	gpgo=subprocess.getoutput(str_gpg)
	# print('**** gpg_output',gpgo)
		
	ret_str=''
	
	with open(tmp_path2, 'r') as f:
					
		ret_str=f.read()
		f.close()	
		
	os.remove(tmp_path1)
	# os.remove(tmp_path2)
	
	
	return ret_str,tmp_path2
	
	
	

		
		
		
