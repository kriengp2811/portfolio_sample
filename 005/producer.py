'''
Created on July 27, 2020

@author: Krienglit
'''

import os
import time
import pulsar
import logging
from threading import Thread
from logging.handlers import TimedRotatingFileHandler


class Producermodule( Thread ):

    def __init__( self ,logging_path='/run/shm/', ip_addr='pulsar://localhost:6650' , topic='my-topic' , thread_slp = 1 ):
        '''
            DESCRIPTION : initial value
            INPUT : N/A
            OUTPUT : N/A
            INPUT/OUTPUT : N/A
            RETURN : N/A
            TIMING :
            NOTE :
        '''
        # prepare log
        self.log_name = os.path.splitext(os.path.basename(__file__))[0]+'.log'
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] \t %(message)s')
        
        # add a rotating handler
        handler = TimedRotatingFileHandler(logging_path+self.log_name,when="D",interval=1,backupCount=5)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        self.logger.info('Init Producer Module')   
        self.logger.info('config: ip_addr='+ip_addr+' topic='+topic+' thread_slp='+str(thread_slp)) 
        
        Thread.__init__( self )
        self.running = True  # set running flag
        self.busy = False  # set busy flag
        self.stop = False  # set stop flag
           
        self.send_flag = False    
        self.send_data = None
        
        self.Thread_slp = thread_slp
        
        try:
            self.client = pulsar.Client(ip_addr)
            self.producer = self.client.create_producer(topic)
        except Exception as e:
            self.logger.error('init pulsar failed')
            self.logger.error(e)
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
        self.logger.info('Kill Producer Module')
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
        self.logger.info('Run Producer Module')
        
        while self.running:  # running
            if self.send_flag :
                self.logger.info('start pulsar send process '+str(len(self.send_data))+'times')
                for i in range(len(self.send_data)):
                    try:
                        self.producer.send(self.send_data[i].encode('utf-8'))
                        self.logger.info('send pulsar: '+self.send_data[i])
                    except Exception as e:
                        self.logger.error('send pulsar failed at '+str(i))
                        self.logger.error(e)
                self.send_flag = False   # reset send_flag
                self.send_data = None
                self.logger.info('send process end')
            time.sleep(self.Thread_slp)
        self.client.close()
        self.logger.info('pulsar client closed')

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
        self.logger.info('Pause Producer Module')
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
        self.logger.info('Resume Producer Module')
        self.stop = False  # clear stop flag
        self.busy = False  # clear busy flag
    
    def send(self,data):
        '''
        DESCRIPTION : resume thread
        INPUT : N/A
        OUTPUT : N/A
        INPUT/OUTPUT : N/A
        RETURN : N/A
        TIMING : N/A
        NOTE : N/A
        '''
        self.send_data = data
        self.send_flag = True
    
    def check_send_busy( self ):
        '''
        DESCRIPTION : resume thread
        INPUT : N/A
        OUTPUT : N/A
        INPUT/OUTPUT : N/A
        RETURN : N/A
        TIMING : N/A
        NOTE : N/A
        '''
        return self.send_flag


if __name__ == '__main__':
    test = Producermodule()
    test.run()
    
    
    
    
    