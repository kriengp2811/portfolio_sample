'''
Created on July 27, 2020

@author: Krienglit
'''

# include libraries
import os
import signal
import logging
import configparser
from logging.handlers import TimedRotatingFileHandler
from mq_module.subscriber import Subscribermodule       # import subscriber module
from odoo_module.odoo_import import ODOOImportmodule   # import odoo file converter module

# Global variable
system_loop = True

# signal when press Ctrl-c or Kill
def signal_handler( signal, frame ):
    global system_loop  # change global value
    system_loop = False  # exit loop


class Odoo_MQInterface( object ):

    def __init__( self ):
        '''
            DESCRIPTION : initial value
            INPUT : N/A
            OUTPUT : N/A
            INPUT/OUTPUT : N/A
            RETURN : N/A
            TIMING :
            NOTE :
        '''    
        # Logger initialize    
        
        config = configparser.ConfigParser()
        config.read(os.path.dirname(os.path.abspath(__file__))+'/odoo_setting.ini')
        
        shared_config = config['SHARED_CONFIG']
        sub_config = config['SUBSCRIBER']
        odoo_config = config['ODOO_IMPORT']
        
        # logging.basicConfig(filename=shared_config['LoggingPath'],format='%(asctime)s [%(levelname)s] %(filename)s \t %(message)s',level=logging.DEBUG,)
        
        self.log_name = os.path.splitext(os.path.basename(__file__))[0]+'.log'
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] \t %(message)s')
        # add a rotating handler
        handler = TimedRotatingFileHandler(shared_config['LoggingPath']+self.log_name,when="D",interval=1,backupCount=5)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        
        self.logger.info('Init MQInterface main thread')
        # Modules declaration
        self.subscriber = Subscribermodule(logging_path=shared_config['LoggingPath'], ip_addr=shared_config['PulsarServerIP'] , topic=sub_config['Topic'] , sub_name=sub_config['SubscriptionName'] , thread_slp=float(sub_config['ThreadSleep']) , queue_size=int(sub_config['QueueSize']) )
        self.odoocsv = ODOOImportmodule(logging_path=shared_config['LoggingPath'], odoo_ip=odoo_config['OdooServerIP'] , odoo_db=odoo_config['OdooDBName'] , odoo_user=odoo_config['OdooAdminUsername'] , odoo_pass=odoo_config['OdooAdminPassword'] , pycmd=odoo_config['PythonCmd'] , thread_slp=float(odoo_config['ThreadSleep']) )

    def run_system( self ):
        '''
        DESCRIPTION : start thread
        INPUT : N/A
        OUTPUT : N/A
        INPUT/OUTPUT : N/A
        RETURN : N/A
        TIMING : N/A
        NOTE : N/A
        '''
        
        self.logger.info('Run MQInterface main thread')  
        # Assign signal
        signal.signal( signal.SIGINT, signal_handler )
        signal.signal( signal.SIGTERM, signal_handler )
        
        self.logger.info('Start all modules')
        # Start all modules
        self.subscriber.start()
        self.odoocsv.start()

        # Main loop
        while system_loop:  # running            
            # subscriber -> odoo import process start here
            if not self.odoocsv.odoo_check_busy():
                rcv_flg ,csv_rcv = self.subscriber.receive()
                if rcv_flg:
                    self.odoocsv.odoo_import(csv_rcv)
                    self.logger.info('MQInterface recieve data from Subscriber module and send to CSVgenerate module')
            # subscriber -> odoo import process end here
        # exit loop and kill all Thread
        self.subscriber.kill()
        self.odoocsv.kill()


if __name__ == '__main__':
    test = Odoo_MQInterface()
    test.run_system()
    
    
    
    
    
