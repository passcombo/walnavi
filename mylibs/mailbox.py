

import ssl
import smtplib
import imaplib
from email import encoders
import email

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase

import time
import datetime
import traceback

import mylibs.ioprocessing as iop
import re
import os


def get_new_to_addr_list(my_addr,msgobj):

	# print(msgobj)
	cur_to=[]
	if 'to' in msgobj:
		if msgobj['to']!='':
			cur_to=msgobj['to']
		# print('to',cur_to)
	elif 'To' in msgobj:
		if msgobj['To']!='':
			cur_to=msgobj['To'].split(',')
		# print('To',cur_to)
	
	cur_from=''
	if 'from' in msgobj:
		cur_to.append(msgobj['from'])
	elif 'From' in msgobj:
		cur_to.append(msgobj['From']) #.split(',')
	
	# print(cur_to)
	
	try:
		cur_to.remove(my_addr)
	except:
		print()
		
	
	cur_to.append(cur_from)
	
	return cur_to
	
	

def send_input(json_obj , pp, send_file=False, send_public=False, msg_receiver_s='',subj='',sent_msg_cont=''):

	# get aliases:
	only_return_book=False
	if msg_receiver_s!='' or subj!='':
		only_return_book=True
		
	addr_alia=iop.print_addr_book(json_obj,only_return_book)

	# 1. prompt for subject / or default
	# subj='' #iop.input_prompt(propmtstr='\n Enter message subject: ', confirm=True, soft_quite=True)
	# 2. prompt for receiver / check key or pass exist ...
	if msg_receiver_s=='':
		msg_receiver_s=iop.input_prompt(propmtstr='\n Enter receiver address or alias - multiple after comas: ', confirm=False, soft_quite=True) 	
	
	if msg_receiver_s=='q' or msg_receiver_s=='':
		print('Quitting message...')
		return '', '', '', ''
		
	# msg_receiver_s=msg_receiver_s.split(',')
		
	msg_receivers_list=msg_receiver_s #[] #msg_receiver.strip().lower()
	# for msg_receiver in msg_receiver_s:
	
		# if msg_receiver in addr_alia.keys():
			# msg_receivers_list.append(msg_receiver.strip())
			
		# elif '@' in msg_receiver and send_public:
			# msg_receivers_list.append(msg_receiver.strip())
			
		# else : # if not full mail try match alias
			# print('Extracting alias address...')
			# tmp=0
			# for kk in addr_alia.keys():
				# if addr_alia[kk]==msg_receiver:
					# tmp=1
					# print('Matched alias '+msg_receiver+' to '+kk)
					# msg_receivers_list.append(kk)
					# break
	print(msg_receivers_list)			
	
	if len(msg_receivers_list)==0:
		print('...no proper address found - quitting message!...')
		return '', '', '', ''
	else:
		print('Sending to '+str(msg_receivers_list))
	
	same_keys=True
	keytype=[]
	key=[]
	if send_public==False:
	
		pubkeys=iop.gpg_uids()
		# "outgoing_encryption_type","outgoing_encryption_key"
		for ijk, msg_receiver in enumerate(msg_receivers_list):
			if json_obj["outgoing_encryption_type"]=='pgp':
				if json_obj["outgoing_encryption_key"] in str(pubkeys):
					keytype.append('pgp')
					key.append(json_obj["outgoing_encryption_key"])
				else:
					print('Wrong key '+json_obj["outgoing_encryption_key"]+' for address '+msg_receiver)
					print('Available keys: '+str(pubkeys))
					return '', '', '', ''
				
			elif json_obj["outgoing_encryption_type"]=='aes256': #msg_receiver in json_obj["address_book"].keys():
				keytype.append('aes256')
				key.append(json_obj["outgoing_encryption_key"])
				
			else:
				print('Address '+msg_receiver+' missing key or password! First add the address to address book using command saveaddr and set proper password for message encryption and decryption.')
				return '', '', '', ''
				
			if same_keys and ijk>0:
				if keytype[ijk]!=keytype[ijk-1] or key[ijk]!=key[ijk-1]:
					same_keys=False
					print('[!] Provided addresses have different keys/passwords - will send multiple messages if you continue...')
				
		
	msg_content=''
	
	if send_public:
		subj=iop.input_prompt(propmtstr='\n Enter message subject: ', confirm=True, soft_quite=True) # if empty - quit sending ... 
		
	if send_file:
		msg_content=iop.select_file(tmppath='my_files')	
	elif sent_msg_cont!='':
		msg_content=sent_msg_cont
	else:	
		# 3. prompt for content -> save to attachment
		msg_content=iop.input_prompt(propmtstr='\n Enter message text/content: ', confirm=True, soft_quite=True) # if empty - quit sending ... 
	
	
	
	if msg_content in ['','q']:
		if msg_content=='':
			print('Quitting message - empty content...')
		else:
			print('Quitting message.')
			
		return '', '', '', ''
		
	str_new_id_send=str(0)
	new_id_send=0
	try:
		new_id_send=int(json_obj["send_internal_id"]) +1
		str_new_id_send=str( new_id_send )
	except:
		print()
	
	ret_list=[]
	
	if send_public:
		
		fname='' #os.path.join('archive','sent','sent_'+str_new_id_send+'.txt')
		if send_file:
			fname=msg_content
		# else:
			# iop.save_file(fname,msg_content )
		ret_list.append([fname, subj, msg_receivers_list, msg_content]) 
	
	elif same_keys:
		
		ret_list.append([iop.encr_msg(msg_content,keytype[0],key[0],internal_id_str=str_new_id_send), subj, msg_receivers_list, str_new_id_send])  		
	else:
		print('msg_content',msg_content)
		
		for ijk in range(len(keytype)):
			ret_list.append([iop.encr_msg(msg_content,keytype[ijk],key[ijk],internal_id_str=str_new_id_send), subj, msg_receivers_list[ijk], str_new_id_send])
			new_id_send+=1
			str_new_id_send=str( new_id_send )
			
	json_obj["send_internal_id"]=str_new_id_send
	# iop.saving_encr_cred( json.dumps(json_obj), newest_file, pp)
	
	return ret_list








def prepare_message_email(sender_name, file_attach=[] , subj='', text_part=''):
	
	def_subject='Lorem ipsum ut gravida'
	if subj=='':
		subj=def_subject
		
	def_content='GDPR protected customer data update.'
	if text_part=='':
		text_part=def_content

	message = MIMEMultipart("alternative") #html
	message.set_charset('utf8')
	message["Subject"] = subj
	message["From"] = sender_name
	
	msgText = MIMEText(text_part, 'plain')
	message.attach(msgText)			
	att_added=0
	if len(file_attach)>0:
		for file in file_attach:
		
			cas=check_att_size(file)
			if len(cas)>20:		
				print(cas)
				continue
			
			h_head,t_tail=os.path.split(file)
			part_file = MIMEBase('application', 'octet-stream') #MIMEBase('multipart', 'mixed; name=%s' % t_tail)   #MIMEBase('application', 'octet-stream')
			part_file.set_payload(open(file, 'rb').read())
			encoders.encode_base64(part_file)
			part_file.add_header('Content-Disposition', 'attachment; filename="%s"' % t_tail)
			message.attach(part_file)
			att_added+=1
			
	if att_added==0 and subj==def_subject and text_part==def_content:
		return '[!] No attachment - only default content - not sending message... Change message subject or content or add attachment to be able to send.'
		
	return message



def check_att_size(att_file_path,max_bytes=1024*1024*8):
	bytes_size = os.path.getsize(att_file_path)
	if bytes_size>max_bytes:
		return 'Attachment too big. Byte size '+str(bytes_size)+' bigger then max '+str(max_bytes)
	else :
		return str(bytes_size)
		
		
# file attach - place sent files in sent folder in archive - ensure folder exist !
# add method clear attach folder ? clear archive enough
# reply option use the same just enter default email receiver, subject - rest enter manual ...


# def send_email(smpt_cred_dict,receiver_email, file_attach=[] , subj='', text_part=''):
def send_email(smtp_addr,sender_email, password, sender_name, receiver_email, file_attach=[] , subj='', text_part=''):

	text_part='GDPR protected customer data update. Part '+text_part
	
	message=prepare_message_email(sender_name, file_attach , subj, text_part)
	
	if type(message)==type('asdf'):
		return message
		
		
	context = ssl.create_default_context() # Create secure connection with server and send email
	
	with smtplib.SMTP_SSL(smtp_addr, 465, context=context) as server:
	
		server.login(sender_email, password)		
		server.send_message( message, sender_email,  receiver_email )		
		server.close()
		
	return 'Message sent!'




######
##########
#####################################################3
## IMAP:

		
		
		
		
def msg_cont_extr_pgp(msg_content):

	pgp_start='-----BEGIN PGP MESSAGE-----'
	pgp_end='-----END PGP MESSAGE-----'
	
	msg_list=[]

	if pgp_start in msg_content:
	
		split1=msg_content.split(pgp_start)
		
		for s1 in split1:
		
			if pgp_end in s1:
			
				split2=s1.split(pgp_end)
				
				for s2 in split2:
				
					if len(iop.clear_whites(s2))>1: # check if hites only but save orig! len(s2)>1: #len(iop.clear_whites(s2))>1:
					
						tmpmsg=pgp_start+s2+pgp_end
						msg_list.append(tmpmsg)
						
	return msg_list
		
		
		

# if att>0 allow read att for last message? or per id ?
def download_msg_id_att(mail_from , mail_from_pswd , imap_addr, id,att_name='all',attfolder='tmp'): # check if not already downloaded!
		
	print('\n\nDownloading attachments for message ID=['+str(id)+']:\n')
	
	mail=None
	
	try:
		mail = imaplib.IMAP4_SSL(imap_addr)
		mail.login(mail_from,mail_from_pswd)
		mail.select('inbox')
	except:
		err_track = traceback.format_exc()
		return {"Error":err_track}, []
				
	typ, dd = mail.fetch(str(id), '(RFC822)' ) # '(BODY.PEEK[TEXT])'
	
	downl=[]
	
	for response_part in dd:
		if isinstance(response_part, tuple):
		
			msg = email.message_from_string(response_part[1].decode('utf-8'))			
			
			if msg.is_multipart():
			
				for part in msg.walk():
				
					if 'attachment' in str(part.get('Content-Disposition')).lower(): #part.get_content_type() == 'application/octet-stream':
					
						fname=part.get_filename()
						file_name_str=os.path.join(attfolder,id,fname) #os.path.join(attfolder,'id'+id+fname)
						
						if fname!=att_name and att_name.lower()!='all':
							continue
						
						
						print('Downloading file ['+fname+'] ...')
						
						if fname : #and fname.endswith(fileformat):
							file_content= part.get_payload(decode=1)
							
							if iop.save_file(file_name_str,file_content,True):
								print('... saved to '+file_name_str)
								downl.append(file_name_str)
							else:
								print('Failed to save to '+file_name_str)
								
						else:
							print('Wrong attachmentf file format? ['+fname+']')
							
	mail.close()
	mail.logout()
	
	print('Downloaded '+str(downl))
	
	return downl
		
		
		
		
		
		
		
		
		
		
		
		
		
		
# laos detects attachment files to process
def read_msg_id(mail_from , mail_from_pswd , imap_addr, id)	:
	
	mail=None
	
	try:
		mail = imaplib.IMAP4_SSL(imap_addr)
		mail.login(mail_from,mail_from_pswd)
		mail.select('inbox')
	except:
		err_track = traceback.format_exc()
		return {"Error":err_track}, []
				
	# print(id,type(id),str(id))			
				
	typ, dd = mail.fetch(str(id), '(RFC822)' ) # '(BODY.PEEK[TEXT])'
	
	printstr='\n\n Message ID=['+str(id)+'] content:\n'
	msgraw=''
	msghtml=''
	files_att=[]
	sender_email=''
	mail_to=[]
	subj=''
	date=''
	
	for response_part in dd:
		if isinstance(response_part, tuple):
		
			msg = email.message_from_string(response_part[1].decode('utf-8'))			
			
			tmpdate=email.utils.parsedate(msg["Date"])
			tmpdate=datetime.datetime.fromtimestamp(time.mktime(tmpdate))
			tmpdate=tmpdate.strftime('%Y-%m-%d')
			
			subj=msg["Subject"]
			date=tmpdate
				
			printstr+='Date: '+tmpdate+' From: '+msg["From"]+' Subject: '+msg["Subject"]+'\n'
			sender_email=iop.xtract_email(msg["From"])
			# print(msg)
			# print(msg["To"])
			mail_to=''
			if msg["To"]!=None:
				mail_to=msg["To"].split(',')
			# print(msg["From"],iop.xtract_email(msg["From"]))
			# exit()
			
			if msg.is_multipart():
				for part in msg.walk():
				
					if part.get_content_type()=='text/plain':
					
						tmp=str(part.get_payload())
						msgraw+=tmp
						printstr+=tmp+'\n'
					
					elif part.get_content_type()=='text/html':
					
						tmp=str(part.get_payload())
						msghtml+=tmp
						printstr+=tmp+'\n'
					elif 'attachment' in str(part.get('Content-Disposition')).lower():
						# part.get_content_type() == 'application/octet-stream':
						files_att.append(part.get_filename())
						# file_name_datetime_str=file_name.replace(rep_fname,'').replace(rep_fname2,'')
						# str_file_date=file_name_datetime_str[0:4]+'-'+file_name_datetime_str[4:6]+'-'+file_name_datetime_str[6:8]
						
			else:
				# print('optsdf')
				printstr+=str(msg.get_payload())+'\n'
			

	# print(printstr)
	
	
	mail.close()
	mail.logout()
	
	for ij,mm in enumerate(mail_to):
		mail_to[ij]=iop.xtract_email(mm).lower()
		
	# raw_msg={"from":"ktostam", "subj":"jakis", "body":body, "attachments":[attname]}
	return {"from":sender_email, "subj":subj, "body":msgraw, "attachments":files_att, "body_html":msghtml, "to":mail_to}
	# return {"msg_text":msgraw, "msg_html":msghtml, "from":sender_email, "subject":subj, "date":date}, files_att

	# return msg_to_process
		# tmpdict={ "Date":tmpdate, "From":msg["From"], "Subject":msg["Subject"], "ID":str(i), "Attachments":att_count, "EmailSize":msg_size} #, "Nr":max_iter 
				
		
		
		

def search_incoming(mail_from , mail_from_pswd , imap_addr, def_opt_init={} ): 

	mail=None
	try:
		mail = imaplib.IMAP4_SSL(imap_addr)
		mail.login(mail_from,mail_from_pswd)
		mail.select('inbox')
	except:
		err_track = traceback.format_exc()
		return {"Error":err_track},[]


	def_opt={'date_before':'any','date_since':'any', 'from':'any', 'subject':'any', 'last_msg_limit':5, 'only_new':'yes'}
	
	def_opt_set={'date_before':['*','any','all','9912-12-12'], 'date_since':['*','any','all','1912-12-12'], 'from':['*','any','all'], 'subject':['*','all','any']}
	
	def_opt_usr=def_opt.copy() #{'date_before':'2019-09-01','date_since':'any', 'from':'*', 'subject':'any', 'last_msg_limit':5, 'only_new':'no'} #def_opt
	
	## tutaj prompter - user wybier i potwierdza dane ... 6 danych ... 
	
	
	if def_opt_init!={}:
		for kk, vv in def_opt_usr.items():
			if kk in def_opt_init:
				def_opt_usr[kk]=def_opt_init[kk] #overwrite with init value
	
	else: # manual enter values
	
		# print('\nSet mail search params ... ') #,json_obj[kk])
		for kk in def_opt_usr.keys():
		
			opt=''
			if kk in def_opt_set.keys():
				opt=' Options: '+str(def_opt_set[kk])
		
			tmpv=iop.input_prompt('> Enter ['+str(kk)+'] current: ['+str(def_opt_usr[kk])+'] '+opt+' OR end editing [e] : ',False,True)
			tmpv=tmpv.strip()
			
			if tmpv=='e':
				break
			
			elif tmpv=='':
				continue
			
			elif kk=='last_msg_limit':
				try:
					tmpv=int(tmpv)
				except:
					# print('Wrong mail search value - should be int number: '+tmpv)
					continue
			
			def_opt_usr[kk]=tmpv #propmtstr,confirm=False, soft_quite=False
	
	
	# print('Mail search params: ', def_opt_usr)
	
	
	
	
	
	total_str=''
	
	if True: #def_opt_usr!=def_opt:
	
		for kk, vv in def_opt_usr.items():
				
			if kk=='only_new': #,'only_new':['yes','no','y','n']
				if vv in ['yes','y']:
					total_str+='(UNSEEN) '
					
			elif kk=='last_msg_limit': # def_opt_usr['last_msg_limit']
				continue
		
			elif vv not in def_opt_set[kk]: # if not default option:
				
				if vv in ['*','any','all']:
					continue
				
				if kk=='date_since':
					
					tmpdate=datetime.datetime.strptime(vv,'%Y-%m-%d')
					tmpdate=tmpdate.strftime("%d-%b-%Y")
					
					total_str+='(SENTSINCE {0})'.format(tmpdate)+' '
				
				elif kk=='date_before':
					
					tmpdate=datetime.datetime.strptime(vv,'%Y-%m-%d')
					tmpdate=tmpdate.strftime("%d-%b-%Y")
					
					total_str+='(SENTBEFORE {0})'.format(tmpdate)+' '
						
				elif kk=='from':
					
					total_str+='(FROM {0})'.format(vv.strip())+' '
					
				elif kk=='subject':
					
					total_str+='(SUBJECT "{0}")'.format(vv.strip())+' '
			
				
			# elif kk=='last_msg_limit':
				# if vv>1
	
	total_str=total_str.strip()
	if total_str=='':
		total_str='ALL'
		
	# now seelect top N msg ... 
	# print('Search string: ['+total_str+']')
	ttype, data = mail.search(None,  total_str ) #'(SENTSINCE {0})'.format(date), '(FROM {0})'.format(sender_email.strip())
	
	if ttype !='OK':
		mail.close()
		mail.logout()
		return {},[] #'no msg found'
			
	mail_ids = data[0]
	id_list = mail_ids.split()   
	
	inter_indxi=[int(x) for x in id_list]
	# inter_indxi.sort(reverse = True) 
	inter_indxi.sort( ) 
	
	msg_to_process={}
	
	# def_opt_usr['last_msg_limit']
	max_iter=def_opt_usr['last_msg_limit']
	if max_iter<1 or max_iter>len(inter_indxi) or max_iter>999:
		max_iter=min(999,len(inter_indxi))
		# print('Search [last_msg_limit]<1, setting max '+str(max_iter)+' messages')
		# max_iter=999
	
	
	# in here only return indexes for decryption!
	
	
	
	
	# print('... processing messages ... count ',str(len(inter_indxi)))
	
	iilist=[]
	
	for i in inter_indxi: #[25]
	
		if max_iter<1:
			break
	
		# first fetch body structure to count attachments! and email size
		typ, dd = mail.fetch(str(i), 'BODYSTRUCTURE' )
		
		att_count=0
		msg_size=0
		
		if len(dd)>0: #count att:
			# print('\n***'+str(email.message_from_bytes(dd[0] ))+'***\n')
			bstr=str(email.message_from_bytes(dd[0] )) #.lower()
			tmpstr=bstr.split("\"ATTACHMENT\"") #'attachment')
			att_count+=len(tmpstr)-1
			# print('att_count',att_count)
			# exit()
			
		
		typ, dd = mail.fetch(str(i), '(RFC822.SIZE)' )
		tmps=str(email.message_from_bytes(dd[0] ))
		tmps=tmps.replace('(','').replace(')','')
		tmps=tmps.split()
		if len(tmps)>2:
			if 'RFC822.SIZE' in tmps[1]:
				# print('size?',tmps[2])
				msg_size=tmps[2]
				if iop.is_int(msg_size):
					msg_size= str( round(float(msg_size)/1024/1024,1) )+' MB'
		
		
		typ, dd = mail.fetch(str(i), '(BODY.PEEK[] FLAGS)' ) # FIRST READ FLAGS TO RESTORE THEM !
		
		for response_part in dd:
			if isinstance(response_part, tuple):
			
				msg = email.message_from_string(response_part[1].decode('utf-8'))
				mail_to=''
				if msg["To"]!=None:
					mail_to=msg["To"] #.split(',')
				# print(msg["Date"]+'|'+msg["From"]+'|'+msg["Subject"])
				
				tmpdate=email.utils.parsedate(msg["Date"]) 
				tmpdate=datetime.datetime.fromtimestamp(time.mktime(tmpdate))
				tmpdate=tmpdate.strftime('%Y-%m-%d')
				
				iilist.append(max_iter)
				tmpdict={ "Date":tmpdate, "From":msg["From"],"To":mail_to , "Subject":msg["Subject"], "ID":str(i), "Attachments":att_count, "EmailSize":msg_size} 
				msg_to_process[max_iter]=tmpdict #.append(tmpdict)
				max_iter-=1
		
	mail.close()
	mail.logout()
	
	return msg_to_process,iilist
	
	
	
	


def is_imap_conn_bad( mail_from, mail_from_pswd, imap_addr):

	print('\nVeryfing IMAP credentials...')
	try:
	# if True:
		with imaplib.IMAP4_SSL(imap_addr) as mail:
			# mail = 
			mail.login(mail_from,mail_from_pswd)
			mail.select('inbox')
			mail.close()
			mail.logout()
		return False # OK
	except:
		return True	
		
		

def is_smtp_conn_bad(smtp_addr,sender_email,password):
	
	print('\nVeryfing SMTP credentials...')
	context = ssl.create_default_context()
	with smtplib.SMTP_SSL(smtp_addr, 465, context=context) as server:
	
		try:
			server.login(sender_email, password)
			server.close()
			return False
		except:
			server.close()
			return True
