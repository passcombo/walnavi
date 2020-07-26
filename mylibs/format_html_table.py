import os
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
import datetime


		
		
def asci_table(lol):
	#1 format all as strings and find max per column
	first_col_name=lol[0][0]
	
	m1=1 # max length 1st colmn
	m2=1
	
	if 'week' in first_col_name.lower() or 'total'  in first_col_name.lower() : # format column value as ints
		for ww in range(1,len(lol)):
			lol[ww][0]=str(int(lol[ww][0]))
			tmpl=len(lol[ww][0])
			if tmpl>m1:
				m1=tmpl
	else:
		
		dtformat='%Y-%m-%d'
		
		if 'hour' in first_col_name.lower():
			dtformat='%Y-%m-%d %Hh'
			# lol[0][0]='hour UTC'
		
		for ww in range(1,len(lol)):
			# print(lol[ww][0])
			lol[ww][0]= lol[ww][0].strftime(dtformat) 
			tmpl=len(lol[ww][0])
			if tmpl>m1:
				m1=tmpl
		
	if len(lol[0][0])>m1:
		m1=len(lol[0][0])
		
	m1+=3
	mm=[m1]
	
	# second column:
	scale_val_max=1
	val_list=[]
	
	if len(lol[0])>1:
		for ww in range(1,len(lol)):
			if lol[ww][1]>scale_val_max:
				scale_val_max=lol[ww][1]
			
			val_list.append(lol[ww][1])
		
			lol[ww][1]= str(int(lol[ww][1]))
			tmpl=len(lol[ww][1])
			if tmpl>m2:
				m2=tmpl
				
		val_list=[int(round(10*vv/scale_val_max,0) ) for vv in val_list]
		
		if len(lol[0][1])>m2:
			m2=len(lol[0][1])
			
		m2+=3
		mm=[m1,m2]
	else:
		m2=0
		
	x='\n<br>'
	if m2==0:
		x+='-'.join(['' for l in range(m1+m2+1)])+'\n<br>'
	else:
		x+='-'.join(['' for l in range(m1+m2+1+11)])+'\n<br>'
		
	
	for ii,ww in enumerate(lol):
		for jj,kk in enumerate(ww):
	
			ll=int(mm[jj]-len(kk)-1)
			# rr=1
			x+='<span style="color:white">'+'.'.join(['' for l in range(ll)])+'</span>' + str(kk) + ' |' 
			
			# if jj==len(ww)-1:
				# x+='\n<br>'
		
		if m2>0 and ii>0:
			x+=' '+'='.join(['' for l in range( val_list[ii-1] )])
		elif m2>0 and ii==0:
			x+=' chart '
		
		x+='\n<br>'
		
		if ii==0:
			# x+='-'.join(['' for l in range(m1+m2+1)])+'\n<br>'
			if m2==0:
				x+='-'.join(['' for l in range(m1+m2+1)])+'\n<br>'
			else:
				x+='-'.join(['' for l in range(m1+m2+1+11)])+'\n<br>'
	
	
	return x
	# exit()
	
	

	
	
		
def nocss_html_table(lol):
	#1 format all as strings and find max per column
	first_col_name=lol[0][0]
	
	# m1=1 # max length 1st colmn
	# m2=1
	
	if 'week' in first_col_name.lower() or 'total'  in first_col_name.lower() : # format column value as ints
		for ww in range(1,len(lol)):
			lol[ww][0]=str(int(lol[ww][0]))
			# tmpl=len(lol[ww][0])
			# if tmpl>m1:
				# m1=tmpl
	else:
		
		dtformat='%Y-%m-%d'
		
		if 'hour' in first_col_name.lower():
			dtformat='%Y-%m-%d %Hh'
			lol[0][0]='hour UTC'
		
		for ww in range(1,len(lol)):
			# print(lol[ww][0])
			lol[ww][0]= lol[ww][0].strftime(dtformat) 
			# tmpl=len(lol[ww][0])
			# if tmpl>m1:
				# m1=tmpl
		
	# if len(lol[0][0])>m1:
		# m1=len(lol[0][0])
		
	# m1+=3
	# mm=[m1]
	
	# second column:
	scale_val_max=1
	val_list=[]
	
	if len(lol[0])>1:
		for ww in range(1,len(lol)):
			if lol[ww][1]>scale_val_max:
				scale_val_max=lol[ww][1]
			
			val_list.append(lol[ww][1])
		
			lol[ww][1]= str(int(lol[ww][1]))
				
		val_list=[int(round(10*vv/scale_val_max,0) ) for vv in val_list]
		
 
	x='<table style="border-collapse: collapse;font-family:Consolas,monospace;font-size: 0.8em;"><thead>\n'
	 
	for ii,ww in enumerate(lol):
	
		x+='<tr>'
	
		for jj,kk in enumerate(ww):
	
			if ii==0:
				x+='<th style="border: 1px solid navy;padding: 4px;padding-top: 6px;padding-bottom: 3px;text-align: center;background-color: blue;color: white;"> '+ str(kk) +' </th>'
			else:
				x+='<td style="border: 1px solid navy;padding: 2px;position: relative;"> '+ str(kk) +' </td>'
				
		if len(ww)>1 and ii>0:
			x+='<td style="border: 1px solid navy;padding: 2px;position: relative;text-align: left;"> '+'&#x25AE;'.join(['' for l in range( val_list[ii-1]+1 )])+' </td>' #'='.join(['' for l in range( val_list[ii-1] )])
			x+='</tr>\n'
		elif len(ww)>1 and ii==0:
			x+='<th style="border: 1px solid navy;padding: 4px;padding-top: 6px;padding-bottom: 3px;text-align: center;background-color: blue;color: white;"> chart </th></tr>'
			x+='</thead>\n<tbody style="text-align: right;color: navy;">\n'
		elif len(ww)==1:				
			x+='</tr>\n'
			if ii==0:
				x+='</thead>\n<tbody style="text-align: right;color: navy;">\n'
			
			
		
	x+='</tbody>\n</table>'
		
	
	
	return x
	# exit()
	
	
	
	
	

def send_html_email(sender_email,password,sender_name,receiver_email, subj, html_part='\n', file_attach=[], img_file='' ):
 
	message = MIMEMultipart("html") #alternative
	message.set_charset('utf8')
	message["Subject"] = subj
	message["From"] = sender_name
			
	header_str_tmp_main='<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "https://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n'
	header_str_tmp_main+='<html xmlns="https://www.w3.org/1999/xhtml">\n'
	header_str_tmp_main+="""
	<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<meta http-equiv="X-UA-Compatible" content="IE=edge" />
<meta name="viewport" content="width=device-width, initial-scale=1.0 " />
</head>
<body>
"""
	
	if img_file!='':
	
		cas=check_att_size(img_file)
		if len(cas)>20: 
			return
		 
		h_head,t_tail=os.path.split(img_file) #<div style='width:1286px;height:836px'> </div>width:1456px;height:929px   #width='1456px' height='929px' width='100%' height='100%' 
		
		img_html=header_str_tmp_main+"<img src='cid:image1' alt='"+t_tail+"' title='"+t_tail+"'>"+'</body></html>'
		
		
		# msgText = MIMEText("<img src='cid:image1' alt='"+t_tail+"' title='"+t_tail+"'>", 'html')#width=80% height=80% #1456 x 929
		
		msgText = MIMEText(img_html, 'html')#width=80% height=80% #1456 x 929
		message.attach(msgText)
		
		try:
			fp = open(img_file, 'rb')
			msgImage = MIMEImage(fp.read())
			fp.close()
			msgImage.add_header('Content-ID', '<image1>')
			msgImage.add_header('Content-Disposition', 'inline', filename=t_tail) #, 'inline', filename=
			message.attach(msgImage)
		except:
			pass
		
		
	else: 
		part2 = MIMEText(html_part, "html")
		message.attach(part2)
		 
	
	if len(file_attach)>0:
		for file in file_attach:
			 
			h_head,t_tail=os.path.split(file)
			part_file = MIMEBase('application', 'octet-stream') #MIMEBase('multipart', 'mixed; name=%s' % t_tail)   #MIMEBase('application', 'octet-stream')
			part_file.set_payload(open(file, 'rb').read())
			encoders.encode_base64(part_file)
			part_file.add_header('Content-Disposition', 'attachment; filename="%s"' % t_tail)
			message.attach(part_file)
			 
	context = ssl.create_default_context()
	 
	
	with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
	
		server.login(sender_email, password)
		
		server.send_message( message, sender_email,  receiver_email )		# ','.join(receiver_email)
		 
		server.close()
		


		
def list_to_html_table(list_of_dict_of_lol): # [{title:, lol:, }]

	tmp_tables=[]
	tmp_tables_inmail=[]
	
	for ddd in list_of_dict_of_lol:
	
		# inmail_table=asci_table(ddd['lol'])
		inmail_table=nocss_html_table(ddd['lol'])
		
		tmp_tables_inmail.append(inmail_table)
		
	inmail_html='<!DOCTYPE html>\n <body style="font-family: Consolas, monospace;">\n\n\n'
	inmail_html+='<h2>Staking summary [Walnavi]</h2>'
	inmail_html+='\n<br>'.join(tmp_tables_inmail)+'\n</body></html>'	
	
	return inmail_html
	
		
