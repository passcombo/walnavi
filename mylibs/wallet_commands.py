

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
import mylibs.ioprocessing as iop
import mylibs.format_html_table as aggr_mail
import pytz
# import mylibs.helpers as helpers

import re


### if coins = VRSC and mode=deamon - allow option for sending staked reports
def check_txid_in_df(zzz,df):
	toappend=[]
	overlaped=0
	# tmpii=0
	
	for z in zzz:
	
		if z['category'] not in ['mint','immature'] or 'generated' not in z:
			continue

		if z['generated']==False:
			continue
			
		date_time=datetime.datetime.fromtimestamp(z['time'])
		
		amount=z['amount'] # float
		txid=z['txid'] # str
		ind= df['date_time'] >= date_time
		
		
		if len(df[ind])==0:
		
			df2=df[ind]
			ind2=df2['txid']==txid
			#print('df2[ind2]',df2[ind2])
			if len(df2[ind2])==0:
				# print('new txid',txid)
				toappend.append([date_time, amount, txid])
				# tmpii+=1
		else:
			overlaped+=1
	
	return toappend, overlaped
	
	
	
def stake_sum_write(toappend,file_path,mode='w'): #  'a+' for append

	# x=datetime.datetime.today()
	time_format='%Y-%m-%d %H:%M:%S'

	# x1=x.strftime(time_format)
	# print('writing',str(amnt),str(addr_from),str(addr_to))
	
	with open(file_path, mode) as f:
	
		if mode=='w':
			# names=['date_time','amount','txid']
			f.write('date_time'+';'+'amount'+';'+'txid'+';\n')
	
		for aa in toappend:
			f.write(aa[0].strftime(time_format)+';'+str(aa[1])+';'+str(aa[2])+';\n')
		f.close()	
	
def add_periods(df):
	
	df['hour']=df['date_time'].copy()
	df['day']=df['date_time'].copy()
	df['month']=df['date_time'].copy()
	df['weeknr']=df['date_time'].copy()
	for ii, dd in enumerate(df['date_time']):
		df['hour'].iloc[ii]=datetime.datetime( dd.year, dd.month, dd.day, dd.hour )
		df['day'].iloc[ii]=datetime.datetime( dd.year, dd.month, dd.day  ) 
		df['month'].iloc[ii]=datetime.datetime( dd.year, dd.month, 1  ) 
		df['weeknr'].iloc[ii]=dd.isocalendar()[0]*100+dd.isocalendar()[1]
		
	
	total=df[['amount']].copy().aggregate(['sum'])
	
	hourly=df[['hour','amount']].groupby('hour',as_index=False).aggregate({'amount':['sum']})
	hourly=hourly.sort_values(by='hour', ascending=False)
	hourly.columns = hourly.columns.droplevel(1)
	# print(hourly.iloc[:24,:])
	
	daily=df[['day','amount']].groupby('day',as_index=False).aggregate({'amount':['sum']})
	daily=daily.sort_values(by='day', ascending=False)
	daily.columns = daily.columns.droplevel(1)
	# print(daily.iloc[:7,:])
	
	monthly=df[['month','amount']].groupby('month',as_index=False).aggregate({'amount':['sum']})
	monthly=monthly.sort_values(by='month', ascending=False)
	monthly.columns = monthly.columns.droplevel(1)
	# print(monthly.iloc[:6,:])
	
	weekly=df[['weeknr','amount']].groupby('weeknr',as_index=False).aggregate({'amount':['sum']}).sort_values(by='weeknr', ascending=False)
	weekly.columns = weekly.columns.droplevel(1)
	
	return total.iloc[0,0], monthly.iloc[:6,:], weekly.iloc[:5,:], daily.iloc[:7,:], hourly.iloc[:24,:]
	
	

def get_staked_sum(CLI_STR,sender_email,password,sender_name,receiver_email): # run 1 an hour, exclude current hour 
	# 1. check file exist:
	sumpath=os.path.join('config','logs','vrsc_stake_sum.csv')
	cur_time=time.localtime()
	if cur_time.tm_min>15:
		return

		 
	toappend=[]
	
	if os.path.exists(sumpath):
	
		tmptimestamp=os.path.getmtime(sumpath) # BUG? cannot set exact time - trick
		
		if time.time()-tmptimestamp<3500: 
			return
	
		#read file
		df=pandas.read_csv(sumpath,";",names=['date_time','amount','txid'],header=0, index_col=False  ,parse_dates=['date_time'],infer_datetime_format=True,date_parser=lambda x: pandas.datetime.strptime(x, '%Y-%m-%d %H:%M:%S') )#,names=['date_time','amount','txid']
		df=df.dropna()
		# try:
		zzz=json.loads(subprocess.getoutput(CLI_STR+' listtransactions "" 999') )
		#print('last5',zzz[-8:-1])
		toappend,overlaped=check_txid_in_df(zzz,df)
		
		
		if overlaped==0: # if no overlap maybe period was too short...
			# print('overlap',overlaped)
			zzz=json.loads(subprocess.getoutput(CLI_STR+' listtransactions "" 9999') )
			toappend,overlaped=check_txid_in_df(zzz,df)
		
		if len(toappend)>0:
			stake_sum_write(toappend,sumpath,'a+')	
		else:
			toappend.append([datetime.datetime.now(), 0, ''])
			stake_sum_write(toappend,sumpath,'a+') #write
			
		# except:
			# pass
	else: 
		# try:
		# print('create new file')
		zzz=json.loads(subprocess.getoutput(CLI_STR+' listtransactions "" 9999') )
		df = DataFrame(columns=['date_time','amount','txid'])
		toappend,overlaped=check_txid_in_df(zzz,df)
		# print('overlap',overlaped)
		
		stake_sum_write(toappend,sumpath )	 
		# except:
			# pass

	# now read again
	df=pandas.read_csv(sumpath,";",names=['date_time','amount','txid'],header=0, index_col=False  ,parse_dates=['date_time'],infer_datetime_format=True,date_parser=lambda x: pandas.datetime.strptime(x, '%Y-%m-%d %H:%M:%S') )#,names=['date_time','amount','txid']
	
	
	# adjust to show zeros:
	t1=datetime.datetime.now() # pytz.utc)
	
	add_dates=[]

	for tt in range(1,25):
		add_dates.append(datetime.datetime(t1.year,t1.month,t1.day,t1.hour) - datetime.timedelta(hours=tt) )
		
	for tt in range(1,190):
		add_dates.append(datetime.datetime(t1.year,t1.month,t1.day) - datetime.timedelta(days=tt) )

		
		
		
	for aa in add_dates:
		df=df.append(DataFrame([[aa,0,'']], columns=['date_time','amount','txid']))
	
	# aggregate by hours, days, weeks, months -> add new column calculated in df
	# write aggr result to list
	total, monthly, weekly, daily, hourly=add_periods(df)
	
	monthly_list=[]
	monthly_list.append(monthly.columns.tolist())
	monthly_list+=monthly.values.tolist()
	
	
	weekly_list=[]
	weekly_list.append(weekly.columns.tolist())
	weekly_list+=weekly.values.tolist()
	
	
	daily_list=[]
	daily_list.append(daily.columns.tolist())
	daily_list+=daily.values.tolist()
	
	
	hourly_list=[]
	hourly_list.append(hourly.columns.tolist())
	hourly_list+=hourly.values.tolist()
	
	total_list=[['Total'],[total]]
	
	list_of_dict_of_lol=[{'title':'Hourly', 'lol':hourly_list },{'title':'Daily', 'lol':daily_list },{'title':'Weekly', 'lol':weekly_list },{'title':'Monthly', 'lol':monthly_list },{'title':'Total', 'lol':total_list } ]
	
	html_ready=aggr_mail.list_to_html_table(list_of_dict_of_lol) # [{title:, lol:, }]
	
	
	aggr_mail.send_html_email(sender_email,password,sender_name,receiver_email, 'Staking notification', html_ready  )
 
 







# nicer usage
def get_key_eq_value_x(str_base,str_extract):	# extracting values from "key=value" in sending transaction...

	# from should extr from or fr
	toextr=str_extract
	
	if str_extract=='amount':
		if 'am=' in str_base:
			toextr='am'

	elif str_extract=='from':
		if 'fr=' in str_base:
			toextr='fr'
			
	toextr+='='
	
	tmpstr=str_base.split(toextr)
	
	if len(tmpstr)!=2:
		return "["+str_extract+"] is missing in the command "+str_base
		
	tmpstr=tmpstr[1].split(' ')
	
	return tmpstr[0]




def nice_print(dd): # dd={ head[],main ,tail , partsplit, linesplit, }
	
	retstr=dd['partsplit']
	
	for pp in ['head','main','tail']:
		if len(dd[pp])>0:
			for ll in dd[pp]:
				retstr+=ll+dd['linesplit']
				
			retstr+=dd['partsplit']
	
	return retstr


#selcur
def clear_txid_logs(currency_name): #only left last one

	file_path=os.path.join("config","logs",currency_name+"_txid_logs.txt")
	# print(file_path)
	# print(os.getcwd())
	df=DataFrame()	
	if os.path.exists(file_path):
		df= pandas.read_csv(file_path,";",names=['date_time','txid'],parse_dates=['date_time'],infer_datetime_format=True)

	if len(df)==0:
		return
		
	cur_time=pandas.Timestamp('today') #datetime.datetime.today()
	min_time = cur_time - pandas.Timedelta(hours=1)

	filter_id = (df['date_time'] > min_time)
	tmpdf = df.loc[filter_id]
	
	time_format='%Y-%m-%d %H:%M:%S'
	
	with open(file_path, 'w') as f:
		for index, row in df.iterrows():
			f.write(str(row['date_time'].strftime(time_format))+';'+row['txid']+'\n')
		
		f.close()
	

	
def is_new_txid(strtxid,currency_name): # return array of known txids

	file_path=os.path.join("config","logs",currency_name+"_txid_logs.txt")
	df=DataFrame()	
	if os.path.exists(file_path):
		df= pandas.read_csv(file_path,";",names=['date_time','txid'],parse_dates=['date_time'],infer_datetime_format=True)

	if len(df)==0:
		return True
		
	# print(df)
	# print('filtering',strtxid)
	
	filter_id = (df['txid'] == strtxid)
	df=df[filter_id]
	# print(df)
	
	if len(df)>0:
		return False
	else:
		return True




def log_txid(strtxid,currency_name ): # saving tx done
	file_path=os.path.join("config","logs",currency_name+"_txid_logs.txt")
	x=datetime.datetime.today()
	time_format='%Y-%m-%d %H:%M:%S'
	x1=x.strftime(time_format)
	
	with open(file_path, 'a+') as f:
		f.write(str(x1)+';'+strtxid+'\n')
		f.close()
	

	
# list unspend general -> iterate through with addr?? do I need adddr anyway ?
# dict_unconf_tx_all[tmpadr]={'txid':tmptxid ,'amount':tmpam} = unconf_tx_all(CLI_STR,max_conf='100')
def unconf_tx_all(CLI_STR,max_conf='100'):
	
	dict_unconf_tx_all={}
	cmdloc=['z_listunspent 0 '+max_conf+' true', 'listunspent 0 '+max_conf, 'listtransactions "*" 999999']
	
	for ccc in cmdloc:
	
		tmp1=subprocess.getoutput(CLI_STR+" "+ccc )
		# if ccc=='listtransactions "*" 0 999999':
			# print(tmp1)
		
		try:
			js1=json.loads(tmp1)
			# print('139',js1)
			for jj in js1:
			
				if "address" not in jj or "amount" not in jj or "txid" not in jj or "confirmations" not in jj:
					continue
					
				if ccc!='listtransactions "*" 999999':
					if int(jj["confirmations"])>int(max_conf):
						continue
			
				tmpadr=jj["address"]
				tmpam=jj["amount"]
				tmptxid=jj["txid"]
				tmpgen='False'
				tmpconf=jj["confirmations"]
				
				# print('146',jj)
				if 'generated' in jj:
					tmpgen=str(jj["generated"])
					
				if 'category' in jj: # category only for mintes = listtransaction
					#print(str(jj))
					#try:
					if str(jj["category"]) in ['mint','immature']: # take only mint
						if int(jj["confirmations"])>100: # but remove if conf > 100
							continue
						else:
							tmpgen='True'
					else:
						continue
					
					
				
				if tmpadr not in dict_unconf_tx_all:
					dict_unconf_tx_all[tmpadr]=[]
				
				dict_unconf_tx_all[tmpadr].append({'txid':tmptxid ,'amount':tmpam, 'staked':tmpgen, 'conf':tmpconf})
				
		except:
			pass
	
	return dict_unconf_tx_all
	
	


# dict_income, print_str=check_for_new_tx(CLI_STR,currency_name,max_conf='100')
def check_for_new_tx(CLI_STR,currency_name): #{'txid':tt["txid"] ,'amount':tt["amount"]}
	
	dict_income={}
	print_str=''
	udi=unconf_tx_all(CLI_STR)
	# print(udi)
	
	addr_list, addr_type=get_all_addr(CLI_STR)
	alias_map=address_aliases(addr_list)

	
	for aa, dd in udi.items():
		# print('174',dd)
		for vv in dd:
			# print('176',vv,vv["txid"])
			if is_new_txid(vv["txid"],currency_name):
				
				log_txid(vv["txid"],currency_name)
			
				dict_income[aa]={'txid':vv["txid"] ,'amount':vv["amount"]}
				staked=''
				if vv['staked']=='True':
					staked='[STAKED] '
				
				print_str+='Amount '+staked+str(vv["amount"])+' to address '+aa+' alias '+alias_map[aa]+'\n'+'  txid '+vv["txid"]+'\n\n' #
				
					
				
	
	if print_str!='':
		print_str='Incoming transactions:\n\n'+print_str+'\n\n'
		
	return dict_income, print_str
	




def extract_from_confirmed_tx(ucmd):
	amount=0
	conf_str_split=ucmd.split('z_sendmany')
	origaddr=''
	toaddr=''
	if len(conf_str_split)>1:
		conf_str_split=conf_str_split[1].strip().split()
		origaddr=conf_str_split[0].replace('"','')
		conf_str_split=conf_str_split[1].replace('"[','[').replace(']"',']').replace('\\','')
		
		# print(origaddr,conf_str_split)
		jsd=json.loads(conf_str_split)
		try:
			for kl in jsd:
				if kl["address"]!=origaddr:
					amount=float(kl["amount"])
					toaddr=kl["address"]
					break
		except:
			return amount,origaddr,toaddr
		# print(jsd[0]["amount"])
		
	return amount,origaddr,toaddr

#"selcur",
def get_available_limited_balance(DEAMON_DEFAULTS,currency_name): # based on historical spends 
	
	df=DataFrame()	
	file_path=os.path.join("config","logs",currency_name+"_limit_logs.txt")
	if os.path.exists(file_path):
		df= pandas.read_csv(file_path,";",names=['date_time','amount'],parse_dates=['date_time'],infer_datetime_format=True)

	if len(df)==0:
		print("! could not read log file "+file_path+" to verify limits used. No file or file empty- allow max tx.")
		
		return float(DEAMON_DEFAULTS["tx_amount_limit"])
		
		
	cur_time=pandas.Timestamp('today') #datetime.datetime.today()
	min_time = cur_time - pandas.Timedelta(hours=int(DEAMON_DEFAULTS["tx_time_limit_hours"]))

	filter_id = (df['date_time'] > min_time) & (df['date_time'] <= cur_time) 
	tmpdf = df.loc[filter_id]
	if tmpdf.empty:
		return float(DEAMON_DEFAULTS["tx_amount_limit"])
		
	usedlimit=tmpdf['amount'].sum()
	
	return float(DEAMON_DEFAULTS["tx_amount_limit"]) - usedlimit

	

#"selcur",
def log_limit(amnt,currency_name ): # saving tx done
	file_path=os.path.join("config","logs",currency_name+"_limit_logs.txt")
	try:
		float(amnt)

		x=datetime.datetime.today()
		time_format='%Y-%m-%d %H:%M:%S'

		x1=x.strftime(time_format)
		# print('writing',str(amnt),str(addr_from),str(addr_to))
		with open(file_path, 'a+') as f:
			f.write(str(x1)+';'+str(amnt)+' \n')
			f.close()
	except:
		print('log limit err - wrong amount '+amnt)




# ta funkcja czasem w petli i nieelegancko wychodzi w polaczeniu z 		list_unspent=all_t_addr_list()...
def get_t_balance(CLI_STR,test_addr):
	
	list_unspent=all_t_addr_list(CLI_STR) #json.loads( subprocess.getoutput(CLI_STR+" "+'listunspent') ) #
	test_balance=float(0)
	
	for lu in list_unspent:
		
		if lu["address"]==test_addr:
			test_balance+=float(lu["amount"])
			
	return test_balance
	
	
	
def get_t_addr_json(a1,list_unspent): # takes json a1 and json unspent


	for lu in list_unspent:
		cc=0
		for aa in a1:
			if lu["address"]==aa:
				break
			cc+=1
		# print('\n 569 checking',lu["address"],cc,len(a1))
		if cc==len(a1):
			a1.append(lu["address"])
			
	# print('560',a1)
	return a1
	
	

def address_aliases(addr_list): # address_aliases(get_wallet(True))
	alias_map={}
	for aa in addr_list:
		tmpa=aa[:3].lower()+aa[-3:].lower()
		iter=1
		while tmpa in alias_map.values():
			tmpa+=str(iter)
			iter+=1
		
		alias_map[aa]=tmpa #.append([aa, tmpa])
		
	return alias_map
	


def get_unconfirmed(CLI_STR,aa): # ttype z or t
	
	send_js_str=''
	if aa[0]=='z':
		send_js_str='z_listunspent 0 0 true ["'+str(aa)+'"]'
	else:
		send_js_str='listunspent 0 0 ["'+str(aa)+'"]'
		
	send_js_str=send_js_str.replace('"','\\"').replace("]",']"').replace("[",'"[')
	zxc=subprocess.getoutput(CLI_STR+" "+send_js_str )
	
	inc=json.loads(zxc)

	suma=0
	for tt in inc: # multiple incoming per address:
		try:
			suma+=float(tt["amount"])				
		except:
			pass
			
	return suma
	
	
	
	

def get_unconfirmed_balance(CLI_STR):
	
	dict_income={}
	alias_map=get_wallet(CLI_STR,True)
	
	for aa in alias_map.keys(): # for each addr:
		send_js_str=''
		if aa[0]=='z':
			send_js_str='z_listunspent 0 0 true ["'+str(aa)+'"]'
		else:
			send_js_str='listunspent 0 0 ["'+str(aa)+'"]'
		send_js_str=send_js_str.replace('"','\\"').replace("]",']"').replace("[",'"[')
		
		zxc=subprocess.getoutput(CLI_STR+" "+send_js_str )
		
		inc=json.loads(zxc)
		
		suma=0
		for tt in inc: # multiple incoming per address:
			
			try:
				suma+=float(tt["amount"])				
			except:
				pass
		
		if suma>0:
			dict_income[aa]=suma
		
	return dict_income

	
def get_all_addr(CLI_STR): # addr_list, addr_type=get_all_addr(CLI_STR) -> alias_map=address_aliases(addr_list)

	addr_list=[]
	addr_types={}
	
	r1=subprocess.getoutput(CLI_STR+" "+'listaddressgroupings')

	a1=json.loads(r1)	
	
	
	for aa in a1:
		# if 'address' in aa:
			# addr_list.append(aa['address'])
			# addr_types[aa['address']]='t'
		# else:
		for bb in aa:
			if bb[0] in addr_list:
				continue
				
			addr_list.append(bb[0])
			addr_types[bb[0]]='t'
				# if 'address' in bb:
					# addr_list.append(bb['address'])
					# addr_types[bb['address']]='t'
				# else:
			# for cc in bb:
						# if 'address' in cc:
				# print(cc)
				# addr_list.append(cc[0])
				# addr_types[cc[0]]='t'
						# else:
							# print('\n\n\n WARNING listaddressgroupings - the hirerachy is even deeper !')
	
	# for aa in a1:
		# addr_list.append(aa['address'])
		# addr_types[aa['address']]='t'
		
	r2=subprocess.getoutput(CLI_STR+" "+"z_listaddresses")
	a2=json.loads(r2)
	
	for aa in a2:
		addr_list.append(aa)
		addr_types[aa]='z'
		
	return addr_list, addr_types
	
	

def get_wallet(CLI_STR,only_addr_list=False,or_addr_amount_dict=False, both=False, above_amount=-1): #0.0001

	addr_list, addr_type=get_all_addr(CLI_STR)
	alias_map=address_aliases(addr_list)
	
	if only_addr_list:
		return alias_map
	
	addr_amount_dict={}
	total_balance=float(0)
	total_conf=float(0)
	total_unconf=float(0)
	wl=[]
	amounts=[]
	amounts_conf=[]
	amounts_unc=[]
	
	dict_unconf_tx_all= unconf_tx_all(CLI_STR,max_conf='0') #[tmpadr]={'txid':tmptxid ,'amount':tmpam} 
	
	for aa in addr_list:
	
		amount_init=0
		if addr_type[aa]=='t':
			amount_init=get_t_balance(CLI_STR,aa)
		else:
			amount_init=float(subprocess.getoutput(CLI_STR+" "+'z_getbalance '+aa))
		
		am_unc=0
		if aa in dict_unconf_tx_all:
			
			for vv in dict_unconf_tx_all[aa]:
				am_unc+=vv['amount'] #get_unconfirmed(CLI_STR,aa)dict_unconf_tx_all[aa]
		
		addr_amount_dict[aa]={'confirmed':amount_init,'unconfirmed':am_unc}
		amounts_unc.append(am_unc)
				
		if amount_init>0:
			wl.append({'addr':aa,'confirmed': amount_init, 'unconfirmed': am_unc })
			amounts.append(amount_init+am_unc)	
			amounts_conf.append(amount_init)	
			total_balance+=amount_init
			total_conf+=amount_init
		else:
			wl.append({'addr':aa,'confirmed':0, 'unconfirmed':am_unc})
			amounts.append(0+am_unc)	
			amounts_conf.append(0)
			
		total_balance+=am_unc
		total_unconf+=am_unc
		
	
	if both:
		return alias_map, addr_amount_dict
		
	if or_addr_amount_dict:
		return addr_amount_dict
		
	wl_str=[]
	wl_str.append("\nWallet Total {:.8f}".format(total_balance) )
	if total_unconf>0:
		wl_str.append(" - confirmed {:.8f}".format(total_conf) )
		wl_str.append(" - unconfirmed {:.8f}".format(total_unconf))
		
	wl_str.append("\n Alias | Amount | Full Address\n")
	for i in sorted(enumerate(amounts), key=lambda x:x[1], reverse=True):
		ii=i[0]
		
		tmp_total=wl[ii]['confirmed']+wl[ii]['unconfirmed']
		
		if tmp_total<=above_amount:
			continue
		
		wl_str.append(" "+alias_map[wl[ii]['addr']]+" | {:.8f}".format(tmp_total)+" | "+wl[ii]['addr'] )
		if wl[ii]['unconfirmed']>0:
			wl_str.append("   - confirmed {:.8f}".format(wl[ii]['confirmed']) )
			wl_str.append("   - unconfirmed {:.8f}".format(wl[ii]['unconfirmed']) )
	
	return '\n'.join(wl_str)
	
	
	
	
	
def get_zaddr_history(CLI_STR,addr):
	
	v1=json.loads( subprocess.getoutput(CLI_STR+" "+'z_listreceivedbyaddress '+addr) )
	lz=[]
	lconfs=[]
	for zz in v1:
		mm=''
		if 'memo' in zz:
			# mm=zz["memo"].decode("hex")
			try:
				mm=''+str(bytes.fromhex(zz["memo"]).decode('utf-8')).strip(' \r\0')
			except:
				mm=''
		lz.append('Conf='+str(zz["confirmations"])+' amount='+str(zz["amount"])+' txid='+zz["txid"]+' memo:'+mm)
		lconfs.append(int(zz["confirmations"]))
		
	lz=[lz[i[0]] for i in sorted(enumerate(lconfs), key=lambda x:x[1], reverse=True)]
	
	return '\n'.join(lz)
	
	

# zastapic listunspent przez listtransactions - stamtad wziac wszystkie adresy ... 	
	

def all_t_addr_list(CLI_STR):
	
	listunspent=json.loads( subprocess.getoutput(CLI_STR+" "+'listunspent') ) 
	luaggr={}
	for lu in listunspent:
		if lu["address"] not in luaggr.keys():
			luaggr[lu["address"]]=lu["amount"]
		else:
			luaggr[lu["address"]]+=lu["amount"]
	
	# print(listunspent)
	v1=json.loads( subprocess.getoutput(CLI_STR+" "+'listreceivedbyaddress 1 true true') )
	addrl=[]
	# print(v1)
	tmpaddr=[]
	for zz in v1:
		
		initamount=float(0)
		if len(luaggr)>0:
			for kk,lu in luaggr.items():
				if kk==zz["address"]: #lu["address"]
					initamount+=lu #["amount"]
		
		tmpaddr.append(zz["address"])
		addrl.append({"address":zz["address"],"amount":initamount})
		
	# just in case addr in unspent but not in received ... 
	for kk,lu in luaggr.items():
		if kk not in tmpaddr:
			addrl.append({"address":kk,"amount":lu})
		
		# lconfs.append(int(zz["confirmations"]))
	return addrl
	
	
	
	
def get_taddr_history(CLI_STR,addr=None):
	
	v1=json.loads( subprocess.getoutput(CLI_STR+" "+'listreceivedbyaddress 1 true true') )
	# print(v1)
	lz=[]
	lconfs=[]
	
	for zz in v1:

		lz.append(zz["address"]+' conf='+str(zz["confirmations"])+' amount='+str(zz["amount"]))
		# taddr.append()
		lconfs.append(int(zz["confirmations"]))
		
	lz=[ lz[i[0]] for i in sorted(enumerate(lconfs), key=lambda x:x[1], reverse=True)]
	# print(lz)
	lz2=[]
	if addr!=None:
		
		for tt in lz:
			# print(tt,'vs',addr, (addr in tt))
			if addr in tt:
				lz2.append(tt)
		lz=lz2					
	
	return lz
	
	
	
	

	
def aliast_to_addr(alias_map,alias):
		
	# if alias in alias_map.values(): # addr_to is alias!
		# print(' alias detected')
	for oo in alias_map:
		if alias_map[oo]==alias:
			# addr_to=oo
			print('...alias['+alias+'] changed to addr ['+oo+']')
			return oo
				# break
	return alias
			
			
			
def isaddrvalid(CLI_STR,addr):
		
	tmp=''
	is_z=False
	
	if addr[0]=='z':
		tmp=subprocess.getoutput(CLI_STR+" "+'z_validateaddress '+addr)
		is_z=True
	else:
		tmp=subprocess.getoutput(CLI_STR+" "+'validateaddress '+addr)
		
	tmpj=json.loads(tmp)
	
	# print(tmp)
			
	return tmpj['isvalid'],is_z
	
				
# if from list =[all] - take all
# if to_addr=any - take any z addr, if nonexistent - create one
# if list = aliast - replace with addr				
# def merge_to(CLI_STR,from_dict,to_addr): 
	
	# alias_map=address_aliases(get_wallet(CLI_STR,True))
	
	
	# if to_addr in alias_map.values(): # addr_to is alias!
		# print(' alias detected')
		# to_addr=aliast_to_addr(alias_map,to_addr)	
	# vv,isz=isaddrvalid(CLI_STR,to_addr) 
	# if vv==False:
		# return 'Not valid to_addr '+to_addr
	
	# tmpstr='['
	
	# for fl,flal in from_dict.items():
	
		# if fl in alias_map.values(): # addr_to is alias!
			# print(' alias detected')
			# fl=aliast_to_addr(alias_map,fl)	
			 
		# vv,isz=isaddrvalid(CLI_STR,fl)
		# if vv:
			# tmpstr+='"'+fl+'",'
		# else:
			# print('Skip bad addr ',fl)	
	
	# tmpstr+=']'
	# tmpstr=tmpstr.replace(',]',']')
			
	# tmpstr=tmpstr.replace('"','\\"')
		
	# tmp_str=CLI_STR+" "+'z_mergetoaddress ' + tmpstr +' '+to_addr
	 	
	# tmp=subprocess.getoutput(tmp_str)
	
	# return tmp
	
	
				
def get_any_zaddr(FEE,CLI_STR):

	min_v_addr=''
	min_k_val=-1
	fee_v_addr=''
	for kk,vv in get_wallet(CLI_STR,or_addr_amount_dict=True).items():
		if kk[0]=='z':
			if fee_v_addr=='' and vv<=float(FEE):
				fee_v_addr=kk
			if min_v_addr=='':
				min_v_addr=kk
				min_k_val=vv
			elif vv<min_k_val:
				min_v_addr=kk
				
	if min_v_addr=='': #gen z addr
		return subprocess.getoutput(CLI_STR+" "+"z_getnewaddress" )
	else:
		if fee_v_addr=='':
			return min_v_addr
		else:
			return fee_v_addr
			
			
def get_status(CLI_STR,addr_balance_more=-1):

	tmp=subprocess.getoutput(CLI_STR+" "+"getblockcount" )
	# print("Current block: "+str(tmp))

	return "Current block: "+str(tmp)+'\n\n'+get_wallet(CLI_STR, above_amount=addr_balance_more)			
	
	
	
	
def list_utxo(CLI_STR):

	alias_map, addr_amount_dict = get_wallet(CLI_STR, False, False, True)
	
	
	tmp1=subprocess.getoutput(CLI_STR+" "+'z_listunspent ' )
	try:
		js1=json.loads(tmp1)
		for jj in js1:
			tmpadr=jj["address"]
			tmpconf=jj["confirmations"]
			tmpam=jj["amount"]
			tmptxid=jj["txid"]
			
			if "utxo" not in addr_amount_dict[tmpadr]:
				addr_amount_dict[tmpadr]["utxo"]=[]
				
			# if "utxo_list" not in addr_amount_dict[tmpadr]:
				addr_amount_dict[tmpadr]["utxo_list"]=[]
				addr_amount_dict[tmpadr]["utxo_conf_list"]=[]
				
			addr_amount_dict[tmpadr]["utxo"].append({"confirmations":tmpconf,"amount":tmpam, "txid": tmptxid})
			addr_amount_dict[tmpadr]["utxo_conf_list"].append(tmpconf)
			addr_amount_dict[tmpadr]["utxo_list"].append(tmptxid)
	except:
		pass
	
	tmp2=subprocess.getoutput(CLI_STR+" "+'listunspent ' )
	
	
	try:
		# print()
		js1=json.loads(tmp2)
		for jj in js1:
			tmpadr=jj["address"]
			tmpconf=jj["confirmations"]
			tmpam=jj["amount"]
			tmptxid=jj["txid"]
			
			if "utxo" not in addr_amount_dict[tmpadr]:
				addr_amount_dict[tmpadr]["utxo"]=[]
				
			# if "utxo_list" not in addr_amount_dict[tmpadr]:
				# addr_amount_dict[tmpadr]["utxo_list"]=[]
				addr_amount_dict[tmpadr]["utxo_conf_list"]=[]
				
			addr_amount_dict[tmpadr]["utxo"].append({"confirmations":tmpconf,"amount":tmpam, "txid": tmptxid})
			addr_amount_dict[tmpadr]["utxo_conf_list"].append(tmpconf)
			# addr_amount_dict[tmpadr]["utxo_list"].append(tmptxid)
			
		udi=unconf_tx_all(CLI_STR,max_conf='0')	# staked amounts
				
		for aa, dd in udi.items():
		
			for vv in dd: #{'txid':tmptxid ,'amount':tmpam, 'staked':tmpgen, 'conf':tmpconf}
				
				addr_amount_dict[aa]["utxo"].append({"confirmations":vv['conf'],"amount":vv["amount"], "txid": vv["txid"]})
				addr_amount_dict[aa]["utxo_conf_list"].append(vv['conf'])
	except:
		pass
	
	strprint=''
	ind=1
	

	amlist=[]
	adrlist=[]
	adr_total=[]
	
	for aa in addr_amount_dict:
		adrlist.append(aa)
		amlist.append( round(addr_amount_dict[aa]['confirmed']+addr_amount_dict[aa]['unconfirmed'],8) )
		tmpa=0
		if "utxo" in addr_amount_dict[aa]:
			for jj in addr_amount_dict[aa]["utxo"]:
				tmpa+=jj['amount']
		adr_total.append(tmpa)

	#print('\n\n\n')
	#print(amlist)
	#print(adrlist)
	#print('\n')
	for i in sorted(enumerate(amlist), key=lambda x:x[1], reverse=True):
		ii=i[0]
		if adr_total[ii]==0: # remove zeros from unspent!
			continue
			
		tmpaddr=adrlist[ii]
		strprint+=str(ind)+' Total '+str(amlist[ii])+' of addr. '+tmpaddr+'\n'
		tmpobj=addr_amount_dict[tmpaddr]
		#print(i,tmpaddr,tmpobj)
		ind+=1
		
		if "utxo_conf_list" in tmpobj:
			#print('obj',tmpobj)
		
			for j in sorted(enumerate(tmpobj["utxo_conf_list"]), key=lambda y:y[1], reverse=True):
				jj=j[0]
				#print('jj',jj)
				strprint+=' - conf. '+str(tmpobj["utxo"][jj]["confirmations"])+' amount '+str(tmpobj["utxo"][jj]["amount"])+' txid '+tmpobj["utxo"][jj]["txid"]+'\n'
			strprint+=' -- utxo count '+str(len(tmpobj["utxo_conf_list"]))+'\n'
		else:
			strprint+=' -- no utxo yet\n'
	
	
	return strprint

#####################################################################
####################### PROCESSING COMMANDS	
# WALLET_DEFAULTS,DEAMON_DEFAULTS,

def cur_name(DEAMON_DEFAULTS):
	#json_conf["cur_path_addr_book"] addrbooks.XXXX.addr
	h,t=os.path.split(DEAMON_DEFAULTS["cur_path_addr_book"])
	t=t.replace('.addr','').lower()
	return t
	
	

def process_cmd(addr_book,FEE,DEAMON_DEFAULTS,CLI_STR,ucmd):

	currency_name=cur_name(DEAMON_DEFAULTS)

	ucmd=iop.fix_equal(ucmd)
	
	cmdsplit=ucmd.lower().split()
	
	if cmdsplit[0]=='merge': # in ucmd.lower():
		print()
	
	elif "balance"==cmdsplit[0]:
			
		limav='\n\nApp current limit: '+str(get_available_limited_balance(DEAMON_DEFAULTS,currency_name))+'\n'
		
		return get_status(CLI_STR,FEE)+limav	

	elif "balance0"==cmdsplit[0]:
			
		limav='\n\nApp current limit: '+str(get_available_limited_balance(DEAMON_DEFAULTS,currency_name))+'\n'
		
		return get_status(CLI_STR)+limav
		
	elif "valaddr"==cmdsplit[0]: # in ucmd.lower():
		
		if len(cmdsplit)==1:
			return "Address missing"
			
		elif len(cmdsplit)==2:
		
			tmpaddr=cmdsplit[1]
			tmpb,isz=isaddrvalid(CLI_STR,tmpaddr)
			if tmpb:
				return '[VALID ADDR] '+tmpaddr
			else:
				return '[WRONG ADDR ! ! ! ] '+tmpaddr+' NOT VALID !'
			
			
	elif "unspent" ==cmdsplit[0]: # ucmd.lower():	
		
		
		return list_utxo(CLI_STR)
		
	elif "send"==cmdsplit[0]: #  in ucmd.lower():	
	
		amount=get_key_eq_value_x(ucmd,'amount')
		if "is missing in" in amount:
			return amount
		
		if amount.lower()!='all':
			amount=float(amount)
		else:
			amount='all'
			
			
		alias_map=address_aliases(get_wallet(CLI_STR,True))	# can be useful for verifying both addr
		

		addr_to=get_key_eq_value_x(ucmd,'to')
		
		if "is missing in" in addr_to:
			return addr_to
			
		if addr_to in alias_map.values(): # addr_to is alias!alias_map=address_aliases(get_wallet(True))
			print(' alias detected')
			addr_to=aliast_to_addr(alias_map,addr_to)
			
		if addr_to in addr_book.keys():
			addr_to=addr_book[addr_to]
			
		# addr validation
		v12,isz=isaddrvalid(CLI_STR,addr_to)
		
		if v12!=True: #v1['isvalid']!=True and v2['isvalid']!=True:
			# print('addr <to> not valid v1,v2',addr_to)
			return 'addr <to> not valid '+str(addr_to)
			
			
			
			
		addr_from=get_key_eq_value_x(ucmd,'from')
		if "is missing in" in addr_from:
			return addr_from
			
		
		if addr_from in alias_map.values(): # addr_to is alias!
			# print(' alias detected')
			addr_from=aliast_to_addr(alias_map,addr_from)	
			
			
		# addr validation
		v12,isz=isaddrvalid(CLI_STR,addr_from)
		
		if v12!=True: #v1['isvalid']!=True and v2['isvalid']!=True:
			# print('addr from not valid v1,v2',v1,v2)
			return 'addr <from> not valid '+str(addr_from)
			
		# print('addr_from',addr_from)
		# check balance:
		cur_balance=0
		if isz: #v1['isvalid']:
			cur_bal=subprocess.getoutput(CLI_STR+" "+'z_getbalance '+addr_from)
			cur_bal=round(float(cur_bal) ,8)
			if amount=='all':
				amount=round(cur_bal- FEE,8) #0.0001
			elif cur_bal<amount+FEE:
				return "\n TX CANCELLED. Current CONFIRMED balance requested addr is ["+str(cur_bal)+"] <= requested amount of ["+str(amount)+ "] + FEE exceeds the value!"
				
		else: # v2['isvalid']:
			cur_bal=get_t_balance(CLI_STR,addr_from) #subprocess.getoutput(CLI_STR+" "+'getreceivedbyaddress '+addr_from)
			cur_bal=round(float(cur_bal)  ,8)
			# print('cur bal',cur_bal,addr_from)
			if amount=='all':
				amount=round(cur_bal-FEE ,8) #0.0001
			elif cur_bal<amount+FEE:
				return "\n TX CANCELLED. Current CONFIRMED balance of requested addr is ["+str(cur_bal)+"] <= requested amount of ["+str(amount)+ "] + FEE exceeds the value!"
		
		amount=round(amount,8)
			
		if amount<=FEE:
			return 'Amount '+str(amount)+' lower then fee '+str(FEE)+' - wont process it.'
			
		check_limit=get_available_limited_balance(DEAMON_DEFAULTS,currency_name)
		# print(amount,check_limit)
		if amount>check_limit:
			return 'Amount > limit = '+str(check_limit)+' Remeber about [tx_amount_limit]='+str(DEAMON_DEFAULTS["tx_amount_limit"])+' and tx_time_limit_hours='+str(DEAMON_DEFAULTS["tx_time_limit_hours"])
		
		left_balance=0
		
		if amount+FEE<cur_bal:
		
			left_balance=round(cur_bal-amount-FEE,8) # ENSURE LEFT BALANCE IS OK
			
			if left_balance+amount+FEE >cur_bal:
			
				btmp=(left_balance+amount-cur_bal+FEE)
				left_balance=round(left_balance - btmp,8) 
				if left_balance+amount+FEE>cur_bal: # just in case ...
					left_balance=round(left_balance - 0.00000001,8)
					
			# print('***left_balance',left_balance)
		
		
		memo=get_key_eq_value_x(ucmd,'memo')
		if "is missing in" in memo:
			memo="Sent via Wallet Navigator - github.com/passcombo"
		memo_hex=memo.encode('utf-8').hex()
			
		if isz: #v1['isvalid']:
			if addr_to[0]=='z':
				send_js_str='[{"address":"'+str(addr_to)+'","amount":'+str(amount)+',"memo":"'+str(memo_hex)+'"}]'  #, {"address":"'+str(addr_from)+'","amount":'+str(left_balance)+'}]'
			else:
				send_js_str='[{"address":"'+str(addr_to)+'","amount":'+str(amount)+'}]'
		else:
			# if left_balance>0.00000001:
				# send_js_str='[{"address":"'+str(addr_to)+'","amount":'+str(amount)+'},{"address":"'+str(addr_from)+'","amount":'+str(left_balance)+'}]'
			# else:
				# send_js_str='[{"address":"'+str(addr_to)+'","amount":'+str(amount)+'}]'
			# now change is served by consolidation option
			send_js_str='[{"address":"'+str(addr_to)+'","amount":'+str(amount)+'}]'
			
		# print(send_js_str)
		send_js_str=send_js_str.replace('"','\\"')
		
		tmp_str=CLI_STR+" "+'z_sendmany "' + str(addr_from)+'" "'+send_js_str+'"'
		return 'CONFIRM OPERATION:: '+tmp_str
		
		
		
		
	elif cmdsplit[0]=='confirm':
	
		
	
		tmp_str=ucmd.replace('CONFIRM OPERATION:: '.lower(),'').replace('CONFIRM OPERATION:: ','')
		print('Confirmed command: '+tmp_str)
		tmp=subprocess.getoutput(tmp_str)
		# print(tmp)
		# if isz: #v1['isvalid']:
		time.sleep(7)
		# else:
			# 
			
		checkopstr="z_getoperationstatus "+'[\\"'+str(tmp)+'\\"]'
		opstat=subprocess.getoutput(CLI_STR+" "+checkopstr)
		
		opstat_orig=opstat
		opj=json.loads(opstat)[0]
		opstat=opj["status"]
		
		while "result" not in opj:
			opstat=subprocess.getoutput(CLI_STR+" "+checkopstr)
			print('...need more time ...')
			# print(opstat)
			opstat_orig=opstat
			opj=json.loads(opstat)[0]
			opstat=opj["status"]
			if opstat=="failed":
				
				return 'FAILED\n'+opstat_orig
				
			time.sleep(3)
		
		# print('opstat full\n\n',str(opstat))
		
		txid=''
		# print(opj)
		
		if "txid" in opj["result"]:
			txid=opj["result"]["txid"]
		
		while opstat=="executing":
			print('... processing . .. ... ')
			time.sleep(7)
			checkopstr="z_getoperationstatus "+'[\\"'+str(tmp)+'\\"]'
		
			opstat=subprocess.getoutput(CLI_STR+" "+checkopstr)
			opstat_orig=opstat
			# print(str(opstat))
			opj=json.loads(opstat)[0]
			opstat=opj["status"]
			if "txid" in opj["result"]:
				txid=opj["result"]["txid"]
			
		final_opstat=json.loads(opstat_orig)
		
		if opstat=="success":
			# print(txid)
			if txid!='':
				
				log_txid(txid,currency_name)
		
			amount,z1,z2=extract_from_confirmed_tx(ucmd)
			# only log if sent not to self addr ... 
			# helpers.sent_log_append(amount) #,addr_from,addr_to)
			log_limit(amount ,currency_name)
			limav='\n\nApp current limit: '+str(get_available_limited_balance(DEAMON_DEFAULTS,currency_name))+'\n'
			return 'SUCCESS \n ' +'\n\n'+ get_status(CLI_STR)+limav
		else:
			# print('FAILED opstat ',str(opstat_orig) )
			limav='\n\nApp current limit: '+str(get_available_limited_balance(DEAMON_DEFAULTS,currency_name))+'\n'
			return 'FAILED\n'+str(opstat_orig)+'\n\n'+ get_status(CLI_STR)+limav
		
		
		
	elif ucmd.lower()=="newzaddr":
		tmp=subprocess.getoutput(CLI_STR+" "+"z_getnewaddress" )
		return ucmd+" "+str(tmp)
		
		
	elif ucmd.lower()=="new_taddr":
		tmp=subprocess.getoutput(CLI_STR+" "+"getnewaddress" )
		return ucmd+" "+str(tmp)

	elif ucmd.lower()=="stake":
		print("Turning staking ON ... ")
		opstat=subprocess.getoutput(CLI_STR+" setgenerate true 0")
		time.sleep(7)
		# print(opstat)
		return 'Staking ON'
		
	elif ucmd.lower()=="stakestop":
		opstat=subprocess.getoutput(CLI_STR+" setgenerate false")
		# print(opstat)
		return 'Staking OFF'
	
	elif cmdsplit[0]=="shield":
		
		# check for arg 1
		if len(cmdsplit)<2:
			return 'Address missing'
			
		cmdsplit=ucmd.split()
		addr_to=cmdsplit[1]
		
		addresses_tmp=get_wallet(CLI_STR,True)
		
		if addr_to not in addresses_tmp.keys():
			
			alias_map=address_aliases(addresses_tmp)
		
			if addr_to in alias_map.values(): 
				print(' alias detected')
				addr_to=aliast_to_addr(alias_map,addr_to)
			
		# validate addr: cmdsplit[1]
		vv,isz=isaddrvalid(CLI_STR,addr_to)
		
		if vv==False:
			return 'Address ['+addr_to+'] not valid!'
			
		if isz==False:
			return 'Address ['+addr_to+'] is not z-addr!'
		
		# run action
		shield_str=CLI_STR+' z_shieldcoinbase "*" '+'"'+addr_to+'" '+str(FEE)
		# print(shield_str)
		# exit()
		# return result
		opstat=subprocess.getoutput(shield_str)
		
		opj=json.loads(opstat)
		
		str1='Shielding '+str(opj["shieldingUTXOs"])+' utxos of value '+str(opj["shieldingValue"])
		str2='\nUtxos still available for shielding: '+str(opj["remainingUTXOs"])+' of value '+str(opj["remainingValue"])
		return str1+str2
		
	# elif ucmd.lower()=="stop":
		# clear_txid_logs(currency_name)
		
		# tmplst=CLI_STR.split(" ")
		
		# if len(tmplst)>1: # 1 version for verus 1 for kmd
			# tmplst=[tmplst[0],tmplst[1],ucmd]
		# else:
			# tmplst=[tmplst[0], ucmd]
			
		# subprocess.Popen(  tmplst  )
		# print("Remote Control closed! Handling commands and blockchain download turned off. Stopping deamon ... ",flush=True)
		# time.sleep(5)
		# try:
			# deamon_warning="make sure server is running and you are connecting to the correct RPC port"
	
			# zxc=subprocess.getoutput(CLI_STR+" getinfo")
			# while deamon_warning not in zxc:
				# print('.',end='',flush=True)
				# time.sleep(5)
				# zxc=subprocess.getoutput(CLI_STR+" getinfo")
				
			# print('Done')
			
		# except:
			# print('Done')
			
		# exit()
		
		# return "Remote Control closed! Handling commands and blockchain download turned off. Stopping deamon ... "
		
		
	else:
		print("else")
		return subprocess.getoutput(CLI_STR+" "+ucmd)
	

