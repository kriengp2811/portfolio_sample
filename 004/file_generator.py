'''
Created on July 27, 2020

@author: Krienglit
'''

import os
import time
import logging
from threading import Thread
from logging.handlers import TimedRotatingFileHandler


class Filegeneratemodule( Thread ):

    def __init__( self ,logging_path='/run/shm/', generate_path='/run/shm/rcv/' , extension='.txt' , thread_slp=1 ):
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
        
        self.logger.info('Init Filegenerate Module') 
        self.logger.info('config: generate_path='+generate_path+' extension='+extension+' thread_slp='+str(thread_slp)) 
        
        Thread.__init__( self )
        
        self.running = True  # set running flag
        self.busy = False  # set busy flag
        self.stop = False  # set stop flag
        
        self.target_path = generate_path
        self.target_extention = extension
        self.Thread_slp = thread_slp
        
        self.write_busy = False
        self.csv_desc = None
        
        self.isFilename = False     # local variable flag
        self.Filename = None        # local variable temp value
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
        self.logger.info('Kill Filegenerate Module')
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
        self.logger.info('Run Filegenerate Module')
        
        while self.running:  # running
            if self.csv_desc != None:
                if not self.isFilename:
                    try:
                        result = self.csv_desc.decode('utf-8').find(self.target_extention)
                    except Exception as e:
                        self.logger.error('file generate decode error')
                        self.logger.error(e)
                        break
                    
                    if result != -1:
                        self.isFilename = True
                        self.Filename = self.csv_desc
                        self.logger.info('seq-1 : receive csv filename ok wait for file data')
                    else:
                        self.logger.info('seq-1: receive wrong file extension format:'+ self.csv_desc.decode('utf-8'))
                    
                else:
                    try:
                        target = os.path.join(self.target_path, self.Filename.decode('utf-8'))
                        self.logger.info('seq-2: generate file: '+target)
                        if os.path.isfile(target):
                            f = open(target, "a+")
                            self.logger.warning('seq-2: file already existing in generate path: '+target)
                        else:
                            #  f = open(target, "w+",encoding='cp932')
                            f = open(target, "w+" , encoding='shift-jis')
                            self.logger.info('seq-2: receive file data')
                        f.write(self.csv_desc.decode('utf-8'))
                        self.logger.info('seq-2: write data-> '+self.csv_desc.decode('utf-8'))
                        f.close
                        
                    except Exception as e:
                        self.logger.error('seq2: process write file failed')
                        self.logger.error(e)  
                         
                    self.isFilename = False
                    self.Filename = None
                    self.logger.info('seq-2: write file done')           
            self.write_busy = False
            self.csv_desc = None
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
        self.logger.info('Pause Filegenerate Module')
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
        self.logger.info('Resume Filegenerate Module')
        self.stop = False  # clear stop flag
        self.busy = False  # clear busy flag
        
    def check_write_busy( self ):
        '''
        DESCRIPTION : resume thread
        INPUT : N/A
        OUTPUT : N/A
        INPUT/OUTPUT : N/A
        RETURN : N/A
        TIMING : N/A
        NOTE : N/A
        '''
        return self.write_busy 
        
        
        
    def write_csv( self , data ):
        '''
        DESCRIPTION : resume thread
        INPUT : N/A
        OUTPUT : N/A
        INPUT/OUTPUT : N/A
        RETURN : N/A
        TIMING : N/A
        NOTE : N/A
        '''
        self.csv_desc = data
        self.write_busy = True
        
        
if __name__ == '__main__':
    test = Filegeneratemodule()
    test.run()
    
    
    
    