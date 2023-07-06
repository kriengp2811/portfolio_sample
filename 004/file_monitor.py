'''
Created on July 27, 2020

@author: Krienglit
'''

import time
import logging
import datetime
import glob, os
from threading import Thread
from logging.handlers import TimedRotatingFileHandler

class Filemonitormodule( Thread ):

    def __init__( self ,logging_path='/run/shm/', monitor_path='/run/shm/send/' , format_file='*.txt' ,  thread_slp=1 ):
        '''
            DESCRIPTION : initial value
            INPUT : N/A
            OUTPUT : N/A
            INPUT/OUTPUT : N/A
            RETURN : N/A
            TIMING :
            NOTE :
        '''
        self.log_name = os.path.splitext(os.path.basename(__file__))[0]+'.log'
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] \t %(message)s')
        # add a rotating handler
        handler = TimedRotatingFileHandler(logging_path+self.log_name,when="D",interval=1,backupCount=5)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        self.logger.info('Init Filemonitor Module') 
        self.logger.info('config: monitor_path='+monitor_path+' format_file='+format_file+' thread_slp='+str(thread_slp)) 
        
        Thread.__init__( self )
        
        self.running = True  # set running flag
        self.busy = False  # set busy flag
        self.stop = False  # set stop flag
        
        self.target_path = monitor_path
        self.target_format = format_file
        self.Thread_slp = thread_slp
        
        self.read_busy = False
        self.csv_desc = []
        self.csv_filename = None # local variable
        
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
        self.logger.info('Kill Filemonitor Module')
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
        self.logger.info('Run Filemonitor Module')
        
        os.chdir(self.target_path)
        while self.running:  # running
            if self.read_busy != True :
                get_file_list = glob.glob(self.target_format)
                file_num = len(get_file_list)
                if file_num > 0:
                    for file in get_file_list:              
                        self.csv_desc.append(file)                      # add filename to first index
                        self.logger.info('add filename to csv_desc[0]: '+file)
                        self.csv_filename = os.path.join(self.target_path, file)
                        self.logger.info('check filesize: '+str(os.stat(self.csv_filename).st_size))
                        
                        if os.stat(self.csv_filename).st_size == 0:
                            self.csv_filename = None
                            self.csv_desc = []
                            self.logger.warning('file is used by another process')
                            break
                        
                        self.logger.info('found '+self.target_format+' file:'+self.csv_filename)
                        
                        try:
                            f = open(self.csv_filename, "r",encoding='shift-jis')
                            f_data = f.read()
                            csv_desc_tmp = []   # declare temp for csv desc
                            csv_desc_tmp.append(f_data)                  
                            f.close
                        except Exception as e:
                            self.logger.error('open file: '+self.csv_filename+' error')
                            self.logger.error(e)
                            self.csv_filename = None
                            self.csv_desc = []
                            break
                            
                        
                        self.csv_desc.extend(csv_desc_tmp)              # join csv data to csv list
                        self.logger.info('add filedata to csv_desc[1]: '+self.csv_desc[1]) 
                        self.logger.info('read csv file done')
                        self.read_busy = True
                        break
            time.sleep(self.Thread_slp)   
                

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
        self.logger.info('Pause Filemonitor Module')
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
        self.logger.info('Resume Filemonitor Module')
        self.stop = False  # clear stop flag
        self.busy = False  # clear busy flag
    
    def read_csv( self ):
        '''
        DESCRIPTION : resume thread
        INPUT : N/A
        OUTPUT : N/A
        INPUT/OUTPUT : N/A
        RETURN : N/A
        TIMING : N/A
        NOTE : N/A
        '''
        return self.read_busy,self.csv_desc
    
    def clr_read_busy( self ):
        '''
        DESCRIPTION : resume thread
        INPUT : N/A
        OUTPUT : N/A
        INPUT/OUTPUT : N/A
        RETURN : N/A
        TIMING : N/A
        NOTE : N/A
        '''
        Current_Date = datetime.datetime.today().strftime ('%d-%b-%Y-%H:%M:%S')
        try:
            os.rename(self.csv_filename,self.csv_filename +'_'+ str(Current_Date))
            self.csv_filename = None # local variable
            self.read_busy = False
            self.csv_desc = []
        except Exception as e:
            self.logger.error('rename file error')
            self.logger.error(e)

if __name__ == '__main__':
    test = Filemonitormodule()
    test.run()
    
    
    
    
