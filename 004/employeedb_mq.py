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
from mq_module.producer import Producermodule           # import producer module
from IO_module.file_monitor import Filemonitormodule     # import monitoring csv module

# Global variable
system_loop = True

# signal when press Ctrl-c or Kill
def signal_handler( signal, frame ):
    global system_loop  # change global value
    system_loop = False  # exit loop


class Employee_MQInterface( object ):

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
        config.read(os.path.dirname(os.path.abspath(__file__))+'/employee_setting.ini')
        
        shared_config = config['SHARED_CONFIG']
        prod_config = config['PRODUCER']
        monitor_config = config['FILE_MONITOR']
        
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
        self.producer = Producermodule(logging_path=shared_config['LoggingPath'], ip_addr=shared_config['PulsarServerIP'] , topic=prod_config['Topic'] , thread_slp=float(prod_config['ThreadSleep']) )
        self.csvmonitor = Filemonitormodule(logging_path=shared_config['LoggingPath'], monitor_path=monitor_config['MonitorPath'], format_file=monitor_config['DetectExtention'] ,  thread_slp=float(monitor_config['ThreadSleep'])  )

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
        self.producer.start()
        self.csvmonitor.start()

        # Main loop
        while system_loop:  # running
            # filemonitor -> producer process start here
            if not self.producer.check_send_busy():
                read_busy,csv_send = self.csvmonitor.read_csv()    # get csv file
                if read_busy:                                      # csv file detect check
                    self.logger.info('MQInterface receive csv data from CSVmonitor module')
                    csv_send.pop(0)
                    self.producer.send(csv_send)        # Send only file data , removea file name from list
                    self.csvmonitor.clr_read_busy()                         # when csv file send successful remove file
                    self.logger.info('MQInterface send csv data to Producer module and clear CSVmonitor module busy bit')
            # filemonitor -> producer process end here
        # exit loop and kill all Thread
        self.producer.kill()
        self.csvmonitor.kill()


if __name__ == '__main__':
    test = Employee_MQInterface()
    test.run_system()
    
    
    
    
    
