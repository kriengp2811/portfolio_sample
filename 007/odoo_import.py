'''
Created on July 27, 2020

@author: Krienglit
'''

import os
import csv
import jaconv
import logging
import subprocess
from subprocess import PIPE
from threading import Thread
from logging.handlers import TimedRotatingFileHandler

class ODOOImportmodule( Thread ):

    def __init__( self ,logging_path='/run/shm/' , odoo_ip='http://localhost:20999' , odoo_db='mydbname' , odoo_user='anonymous' , odoo_pass='anonymous' , pycmd = 'python' ,thread_slp=1 ):
        '''
            DESCRIPTION : initial value
            INPUT : N/A
            OUTPUT : N/A
            INPUT/OUTPUT : N/A
            RETURN : N/A
            TIMING :
            NOTE :
        '''
        # prepare log for monitoring
        self.log_name = os.path.splitext(os.path.basename(__file__))[0]+'.log'
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] \t %(message)s')
        
        # add a rotating handler
        handler = TimedRotatingFileHandler(logging_path+self.log_name,when="D",interval=1,backupCount=5)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        self.logger.info('Init ODOOImport Module') 
        self.logger.info('config: odoo_ip='+odoo_ip+' odoo_db='+odoo_db+' odoo_user='+odoo_user+' odoo_pass='+odoo_pass+' pycmd='+pycmd+' thread_slp='+str(thread_slp)) 
        
        Thread.__init__( self )
        
        self.running = True # set running flag
        self.busy = False  # set busy flag
        self.stop = False  # set stop flag
        
        self._odoo_ip = odoo_ip
        self._odoo_db = odoo_db
        self._odoo_user = odoo_user
        self._odoo_pass = odoo_pass
        self._pycmd = pycmd
        self._odoo_script = os.getcwd()+'/scripts/odoo_add_user.py'     # fix
        self.Thread_slp = thread_slp
        self.tmp_file = os.getcwd()+'/tmp.csv'
        self.csv_desc = None
        self.import_busy = False
        pass

    def kill( self ):
        '''
        DESCRIPTION : kill thread
        INPUT : N/A
        OUTPUT : N/A
        INPUT/OUTPUT : N/A
        RETURN : N/A
        TIMING : N/A
        NOTE : N/A
        '''
        self.logger.info('Kill ODOOImport Module')
        self.running = False  # set False to running flag
        self.busy = True  # set busy flag is True
        self.stop = False  # set stop flag is False
        pass

    def run( self ):
        '''
        DESCRIPTION : start thread
        INPUT : N/A
        OUTPUT : N/A
        INPUT/OUTPUT : N/A
        RETURN : N/A
        TIMING : N/A
        NOTE : N/A
        '''
        self.logger.info('Run ODOOImport Module')
        
        while self.running:  # running
            if self.import_busy:
                self.logger.info('Received import data')
                try:
                    f = open(self.tmp_file,"w+" , encoding='shift-jis')
                    f.write(self.csv_desc.decode('utf-8'))
                    f.close()
                except Exception as e:
                    self.logger.error('create temp file error')
                    self.logger.error(e)
                       
                try:
                    with open(self.tmp_file, mode='r',encoding='shift-jis') as csv_file:
                        self.logger.info('convert data to ODOO format')
                        csv_reader = csv.DictReader(csv_file)
                        for row in csv_reader:
                            temp_name = None
                            if int(row['nation_id']) == 1:
                                # change japanese to alphabet
                                tmp_kana_list = row['name_kana'].split()
                                tmp_fname = jaconv.kana2alphabet(jaconv.kata2hira(tmp_kana_list[0]))
                                tmp_lname = jaconv.kana2alphabet(jaconv.kata2hira(tmp_kana_list[1]))             
                                # create odoo name for japanese
                                temp_name = row['name']+' '+tmp_lname.capitalize()+' '+tmp_fname.upper()
                            else:
                                # create odoo name for foreigner
                                temp_name = row['nickname']+' '+row['name'] 
                            
                            # cmd : python3.x odoo_add_user.py --host=xxx --db=xxx --user=xxx --pass=xxx --add_name=xxx --add_login=xxx --add_pass=xxx
                            exe_cmd = self._pycmd+' '+self._odoo_script
                            exe_cmd +=' --host=\''+self._odoo_ip            # add target host ip arguments
                            exe_cmd +='\' --db=\''+self._odoo_db            # add odoo db name arguments
                            exe_cmd +='\' --user=\''+self._odoo_user        # add odoo admin username for login argument
                            exe_cmd +='\' --pass=\''+self._odoo_pass        # add odoo admin password for login arguemnt
                            exe_cmd +='\' --add_name=\''+temp_name          # add employee name for register argument
                            exe_cmd +='\' --add_login=\''+row['email']      # add odoo username for register argument
                            exe_cmd +='\' --add_pass=\''+row['email']+'\''  # add odoo password for register argument
                            
                            proc = subprocess.run(exe_cmd, shell=True, stdout=PIPE, stderr=PIPE, text=True)
                            self.logger.info('run script: '+exe_cmd)
                            if not proc.stderr:
                                self.logger.info('Odoo import data success: '+temp_name+' '+row['email']+' '+row['email'])
                            else:
                                self.logger.error('Odoo import data failed: '+temp_name+' '+row['email']+' '+row['email'])
                                self.logger.error(proc.stderr)
                except Exception as e:
                    self.logger.error('read temp file error')
               
                self.logger.info('import data end')
                self.import_busy = False
                self.csv_desc = None
                
    def pause( self ):
        '''
        DESCRIPTION : pause thread
        INPUT : N/A
        OUTPUT : N/A
        INPUT/OUTPUT : N/A
        RETURN : result
        TIMING : N/A
        NOTE : N/A
        '''
        logging.info('Pause ODOOImport Module')
        self.busy = True  # set busy flag
        while True:  # stop when stop flag is False
            if self.stop:  # check stop
                break
        return True

    def resume( self ):
        '''
        DESCRIPTION : resume thread
        INPUT : N/A
        OUTPUT : N/A
        INPUT/OUTPUT : N/A
        RETURN : N/A
        TIMING : N/A
        NOTE : N/A
        '''
        self.logger.info('Resume ODOOImport Module')
        self.stop = False  # clear stop flag
        self.busy = False  # clear busy flag
        
    def odoo_import( self ,data):
        '''
        DESCRIPTION : start import data to odoo thread
        INPUT : N/A
        OUTPUT : N/A
        INPUT/OUTPUT : N/A
        RETURN : N/A
        TIMING : N/A
        NOTE : N/A
        '''
        self.csv_desc = data
        self.import_busy = True
    
    def odoo_check_busy( self ):
        '''
        DESCRIPTION : check status target odoo thread
        INPUT : N/A
        OUTPUT : N/A
        INPUT/OUTPUT : N/A
        RETURN : N/A
        TIMING : N/A
        NOTE : N/A
        '''
        return self.import_busy
    
        
        
        
if __name__ == '__main__':
    test = ODOOImportmodule()
    test.run()
    
    
    
    
