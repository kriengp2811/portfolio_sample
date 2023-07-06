'''
Created on July 27, 2020

@author: Krienglit
'''

import os
import time
import pulsar
import logging
from queue import Queue
from threading import Thread
from logging.handlers import TimedRotatingFileHandler

class Subscribermodule( Thread ):

    def __init__( self ,logging_path='/run/shm/', ip_addr='pulsar://localhost:6650' , topic='my-topic', sub_name='my-sub' , thread_slp=1 , queue_size=5 ):
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
        
        self.logger.info('Init Subscriber Module') 
        self.logger.info('config: ip_addr='+ip_addr+' topic='+topic+' thread_slp='+str(thread_slp)+' queue_size='+str(queue_size)) 
        
        Thread.__init__( self )
        self.running = True  # set running flag
        self.busy = False  # set busy flag
        self.stop = False  # set stop flag
        
        self.recvQ = Queue(maxsize=queue_size)
        self.Thread_slp = thread_slp

        try:
            self.client = pulsar.Client(ip_addr) 
            self.consumer = self.client.subscribe(topic,subscription_name=sub_name) 
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
        self.logger.info('Kill Subscriber Module')
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
        self.logger.info('Run Subscriber Module')
        while self.running:  # running
            if not self.recvQ.full():
                try:
                    msg = self.consumer.receive()
                    self.recvQ.put(msg.data())   
                    self.logger.info("Received message: '%s'" % msg.data().decode('utf-8'))    
                    self.consumer.acknowledge(msg)                       
                except Exception as e:
                    self.logger.error('receive pulsar failed')
                    self.logger.error(e)
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
        self.logger.info('Pause Subscriber Module')
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
        self.logger.info('Resume Subscriber Module')
        self.stop = False  # clear stop flag
        self.busy = False  # clear busy flag
        
    def receive( self ):
        '''
        DESCRIPTION : resume thread
        INPUT : N/A
        OUTPUT : N/A
        INPUT/OUTPUT : N/A
        RETURN : N/A
        TIMING : N/A
        NOTE : N/A
        '''
        if not self.recvQ.empty():
            return True,self.recvQ.get_nowait()
        else:
            return False,None
        

if __name__ == '__main__':
    test = Subscribermodule()
    test.run()
    
    
    
    
    
    
    
    
    
    
    