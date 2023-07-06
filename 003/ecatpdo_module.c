/*
 * EtherCAT Processdata Object Module Source File
 *
 * File    : ecatpdo_module.c
 * Version : 1.0.0
 * Date    : xxxxxxxxx
 * Authors : Krienglit Poolsawat
 */


/********************************************************************/
/*		INCLUDE														*/
/********************************************************************/
#include <stdlib.h>
#include "kernel.h"
#include "module_lib.h"
#include "sysctrl_module.h"
#include "ecatpdo_module.h"
#include "trace_module.h"
#include "gpio_module.h"

/********************************************************************/
/*		DEFINE MACROS												*/
/********************************************************************/


/********************************************************************/
/*		EXTERNS														*/
/********************************************************************/
extern unsigned short g_acc_sts;			/** from tsk_10ms.c */
extern unsigned short g_allslaves_sts;		/** from tsk_10ms.c */

/********************************************************************/
/*		FUNCTIONS													*/
/********************************************************************/
static int _ecatpdo_set_outputprocessdata(int line_slct);


/********************************************************************/
/*		VARIABLES													*/
/********************************************************************/
/** Task cycle timer variable(this is for count) */
unsigned int g_polling_cyc_tim = ECAT_SEND_POLLING_CYC;	 // us unit

/** Line select mode variables */
char g_sysctrl_lineslct = LINE1_SLCT;
char g_sysctrl_new_linesw = LINE1_SLCT;

/** Operation mode variables */
int g_sysctrl_mode = STOP_2_STOP;
int g_sysctrl_prev_mode = STOP_2_STOP;

/** Switch line time variable */
unsigned int g_sysctrl_swline_time = 0;

/** Repeat time variable */
unsigned int g_sysctrl_repeat_time = 0;

/** Timer counter variables */
unsigned int g_repeat_time_cnt = 0;	/* 0: non-stop auto mode,>0: auto mode with timeout*/
unsigned int g_swline_time_cnt = 0;

/** Process flag variables */
unsigned char g_polling_manual_flg = DIS_FLG;
unsigned char g_polling_auto_flg = DIS_FLG;
unsigned char g_polling_semiauto_flg = DIS_FLG;	/** Added 20221117 */

unsigned char g_man_set_recv_trace_flg = DIS_FLG;
unsigned char g_auto_set_recv_trace_flg = DIS_FLG;
unsigned char g_semiauto_set_recv_trace_flg = DIS_FLG;	/** Added 20221117 */

/** Trace error code variables */
char g_makepdo_err = 0;
char g_writepdo_err = 0;
char g_readpdo_err = 0;

/********************************************************************/
/*		IMPLEMENT SOURCE											*/
/********************************************************************/


/**
 * @brief Prepare processdata by get data from sysctrl receive buffer
 *
 * @param [in] line_slct = Processdata buffer line select
 *
 * @return = 0 if process successful.
 */
static int _ecatpdo_set_outputprocessdata(int line_slct)
{
    int ercd = E_OK;

    if(line_slct == LINE1_SLCT)
    {
        /** Copy to Line1's header buffer and Line1's data buffer */
        memcpy(&g_optical_header_writebuf_line1,&g_optical_system_line1,sizeof(optical_pdo_struct_t));
        memcpy(&g_optical_body_writebuf_line1,&g_optical_system_line1,sizeof(optical_pdo_struct_t));

        /** Only header buffer set wavelength's data bit7 */
        g_optical_header_writebuf_line1.wl_sw1 |= 0x80;
        g_optical_header_writebuf_line1.wl_sw2 |= 0x80;
        g_optical_header_writebuf_line1.wl_sw3 |= 0x80;
    }
    else if(line_slct == LINE2_SLCT)
    {
    	/** Copy to Line2's header buffer and Line2's data buffer */
        memcpy(&g_optical_header_writebuf_line2,&g_optical_system_line2,sizeof(optical_pdo_struct_t));
        memcpy(&g_optical_body_writebuf_line2,&g_optical_system_line2,sizeof(optical_pdo_struct_t));

        /** Only header buffer set wavelength's data bit7 */
        g_optical_header_writebuf_line2.wl_sw1 |= 0x80;
        g_optical_header_writebuf_line2.wl_sw2 |= 0x80;
        g_optical_header_writebuf_line2.wl_sw3 |= 0x80;
    }
    else
    {
    	ercd = E_PARAM;
    }

    return ercd;
}


/**
 * @brief Set processdata trace error code
 *
 * @param [in] type = Type of error code
 * @param [in] error_code = error code
 *
 * @return = 0 if process successful.
 */
int ecatpdo_set_pdo_error(char type ,int error_code)
{
	int ercd = TRC_E_OK;

	/** Store error code */
	switch (type){
	case SET_MAKEPDO_TRC:
		g_makepdo_err = error_code;		/** Set send processdata error code */
		break;
	case SET_WRITEPDO_TRC:
		g_writepdo_err = error_code;	/** Set send processdata error code */
		break;
	case SET_READPDO_TRC:
		g_readpdo_err = error_code;		/** Set receive processdata error code */
		break;
	default:
		ercd = E_PARAM;
		break;
	}
	return ercd;
}


/**
 * @brief Clear all processdata error code
 *
 * @param n/a
 *
 * @return n/a
 */
void ecatpdo_clear_trace_ercd()
{
	g_makepdo_err = 0;
	g_writepdo_err = 0;
	g_readpdo_err = 0;

	return;
}

/**
 * @brief EtherCAT stop process when error occur
 *
 * @param n/a
 *
 * @return n/a
 */
void ecatpdo_stop_ecat_proc()
{
	/** When in manual mode clear process flag */
	if(g_polling_manual_flg == ENA_FLG)
	{
		g_polling_manual_flg = DIS_FLG;
	}

	/** When in auto mode clear process flag */
	if(g_polling_auto_flg == ENA_FLG)
	{
		g_polling_auto_flg = DIS_FLG;
	}

	/** When in semi-auto mode clear process flag */
	if(g_polling_semiauto_flg == ENA_FLG)
	{
		g_polling_semiauto_flg = DIS_FLG;
	}

	/** Set EtherCAT status in sysctrl to stop mode */
	sysctrl_set_linests(NOTI_STOP_STS);

	return;
}


/**
 * @brief Check EtherCAT error and write trace
 *
 * @param n/a
 *
 * @return = 0 ECAT communication ok
 *         = 5 Manual mode ECAT communication error
 *         = 6 Auto mode ECAT communication error
 */
int ecatpdo_set_pdo_trace()
{
	int err = E_PDO_NOREQ;
	int ercd = TRC_E_OK;
	unsigned short get_almfactor = 0;

	/** Check error and write trace log when in manual mode */
	if(g_man_set_recv_trace_flg == ENA_FLG)
	{
		g_man_set_recv_trace_flg = DIS_FLG;

		/** Set timestamp when EtherCAT communication complete */
		trace_set_timestamps(SET_SEND_TIMESTMP);

		/** Write all timestamp to trace region */
		trace_make_log(TRC_RECV_DATA,g_sysctrl_lineslct,TRC_E_OK,TRC_E_OK);

		if(g_makepdo_err != TRC_E_OK) {
			ercd = TRC_E_ERRSND;
		} else {
			ercd = TRC_E_OK;
		}
		trace_make_log(TRC_SET_WRBUF,g_sysctrl_lineslct,ercd,g_makepdo_err);

		if(g_writepdo_err != TRC_E_OK) {
			ercd = TRC_E_ERRSND;
		} else {
			ercd = TRC_E_OK;
		}
		trace_make_log(TRC_SEND_PDO,g_sysctrl_lineslct,ercd,g_writepdo_err);

		if(g_readpdo_err != TRC_E_OK) {
			ercd = TRC_E_ERRRCV;
		} else {
			ercd = TRC_E_OK;
		}
		trace_make_log(TRC_GET_RDBUF,g_sysctrl_lineslct,ercd,g_readpdo_err);

		ecat_get_acc_almfactor(&get_almfactor);
		if( ( get_almfactor & 0x2 ) == 0x2 ) ercd = TRC_E_RCVTMO;
		trace_make_log(TRC_RECV_PDO,g_sysctrl_lineslct,ercd,TRC_E_OK);

		trace_make_log(TRC_ECAT_DONE,g_sysctrl_lineslct,TRC_E_OK,TRC_E_OK);

		trace_write_all_log();

		/** Check error occur */
		if( (g_makepdo_err != TRC_E_OK) || (g_writepdo_err != TRC_E_OK) || (g_readpdo_err != TRC_E_OK) )
		{
			/** When error occur stop process */
			ecatpdo_stop_ecat_proc();
			err = E_MAN_COMM_ERR;
		}

	}

	/** Check error and write trace log when in auto mode */
	if( ( g_auto_set_recv_trace_flg == ENA_FLG ) || 
	    ( g_semiauto_set_recv_trace_flg == ENA_FLG ) )
	{
		ecat_get_acc_almfactor(&get_almfactor);

		/** Check error occur */
		if( (g_makepdo_err != TRC_E_OK) || (g_writepdo_err != TRC_E_OK) || (g_readpdo_err != TRC_E_OK) || ( ( get_almfactor & 0x2 ) == 0x2 ) )
		{
			g_auto_set_recv_trace_flg = DIS_FLG;
			g_semiauto_set_recv_trace_flg = DIS_FLG;

			/** Set timestamp when EtherCAT communication complete */
			trace_set_timestamps(SET_SEND_TIMESTMP);

			/** When error occur set error log to trace region */
			if(g_makepdo_err != TRC_E_OK) {
				ercd = TRC_E_ERRSND;
				trace_make_log(TRC_SET_WRBUF,g_sysctrl_lineslct,ercd,g_makepdo_err);
				trace_write_log(TRC_SET_WRBUF);
			}

			if(g_writepdo_err != TRC_E_OK) {
				ercd = TRC_E_ERRSND;
				trace_make_log(TRC_SEND_PDO,g_sysctrl_lineslct,ercd,g_writepdo_err);
				trace_write_log(TRC_SEND_PDO);
			}


			if(g_readpdo_err != TRC_E_OK) {
				ercd = TRC_E_ERRRCV;
				trace_make_log(TRC_GET_RDBUF,g_sysctrl_lineslct,ercd,g_readpdo_err);
				trace_write_log(TRC_GET_RDBUF);
			}

			ecat_get_acc_almfactor(&get_almfactor);
			if( ( get_almfactor & 0x2 ) == 0x2 )
			{
				ercd = TRC_E_RCVTMO;
				trace_make_log(TRC_RECV_PDO,g_sysctrl_lineslct,ercd,TRC_E_OK);
				trace_write_log(TRC_RECV_PDO);
			}

			/** Stop process request */
			ecatpdo_stop_ecat_proc();
			err = E_AUTO_COMM_ERR;
		}

	}

	return err;
}


/**
 * @brief System controller memory polling process(state-machine)
 *
 * @param n/a
 *
 * @return = 0 No request process
 *         > 0 Request process
 *         < 0 Error occur
 */
int ecatpdo_sysctrl_polling()
{
    int ercd = E_OK;
    int current_state = 0;
#ifdef GUI_DEBUG
    static int dbg1 = 0;
#endif
    /** Check all important variable for this function */
    if( (g_polling_cyc_tim == 0) || (uC3InputSysctrladdr == NULL) || (uC3OutputSysctrladdr == NULL) )
    {
        return E_ERR;
    }

    /** Store previous mode before get current mode */
    g_sysctrl_prev_mode = g_sysctrl_mode;

    /** Get current mode */
    g_sysctrl_mode = (unsigned int)uC3InputSysctrladdr[SYSRECV_MODE_IDX];

    /** Merge into state machine with previous mode and current mode */
    current_state = (short)( (g_sysctrl_prev_mode << 8) | g_sysctrl_mode );

    switch (current_state)
    {
        case STOP_2_MAN:	/** Start manual mode */
#ifdef GUI_DEBUG
        	puts_com_opt("Mode change: STOP to MANUAL\r\n");
#endif
        	/** Set timestamp when receive mode from system controller */
            trace_set_timestamps(SET_RECV_TIMESTMP);
#ifdef IO_DEBUG
			gpio_write(IO_PORT0,0x1);
#endif

            /** Clear all trace buffer for next measurement */
            trace_clear_write_buffer();
            trace_reset_index();
            ecatpdo_clear_trace_ercd();

            /** Get processdata from shared memory */
            sysctrl_get_setup_pdodata();

            /** Set process data to each line send buffer */
        	_ecatpdo_set_outputprocessdata(LINE1_SLCT);
        	_ecatpdo_set_outputprocessdata(LINE2_SLCT);

        	/** Set start line selection to line 1 */
        	g_sysctrl_lineslct = LINE1_SLCT;

        	/** Set return value to line buffer change request */
    		if(g_sysctrl_lineslct == LINE1_SLCT)
    		{
    			ercd = E_PDO_LINE1_WRREQ;
    		}
    		else if(g_sysctrl_lineslct == LINE2_SLCT)
    		{
    			ercd = E_PDO_LINE2_WRREQ;
    		}
    		else
    		{
    			ercd = E_SWLINE_ERR;
    		}

			/** Set current selected line */
			sysctrl_set_linests(g_sysctrl_lineslct + 1);

    		/** Set all manual mode component flag */
            g_polling_manual_flg = ENA_FLG;
        	g_man_set_recv_trace_flg = ENA_FLG;
            break;

        case MAN_2_MAN:
            /** Do nothing wait for next state change */
            break;

        case MAN_2_LINESW:
        case LINESW_2_LINESW:
#ifdef GUI_DEBUG
        	if(!dbg1)
        	{
        		dbg1= 1;
            	puts_com_opt("Mode change: MANUAL to LINESW\r\n");
        	}
#endif
            if(g_polling_manual_flg == ENA_FLG)
            {
            	/** Check line select mode */
                g_sysctrl_new_linesw = uC3InputSysctrladdr[SYSRECV_LINEMODE_IDX];
                if(g_sysctrl_lineslct != g_sysctrl_new_linesw)
                {
                	/** If line mode has been changed store new line mode value and buffer change request */
                	g_sysctrl_lineslct = g_sysctrl_new_linesw;
            		if(g_sysctrl_lineslct == LINE1_SLCT)
            		{
            			ercd = E_PDO_LINE1_WRREQ;
            		}
            		else if(g_sysctrl_lineslct == LINE2_SLCT)
            		{
            			ercd = E_PDO_LINE2_WRREQ;
            		}
            		else
            		{
            			ercd = E_SWLINE_ERR;
            		}

        			/** Set current selected line */
        			sysctrl_set_linests(g_sysctrl_lineslct + 1);

                    /** Clear all trace buffer for next measurement */
                    trace_clear_write_buffer();
                    ecatpdo_clear_trace_ercd();

                    /** Set all manual mode component flag */
            		g_man_set_recv_trace_flg = ENA_FLG;
                }
            }
            else
            {
            	/** When manual mode set to 0. stop process request */
            	ercd = E_PDO_NOREQ;
            }
            break;

        case MAN_2_STOP:
        case LINESW_2_STOP:
#ifdef GUI_DEBUG
        	dbg1 = 0;
        	puts_com_opt("Mode change: LINESW/MANUAL to STOP\r\n");
#endif
        	/** Stop process request */
        	ecatpdo_stop_ecat_proc();
            ercd = E_STOP_PROCESS;
            break;

        case STOP_2_AUTO:	/** Start auto mode */
#ifdef GUI_DEBUG
            puts_com_opt("Mode change: STOP to AUTO\r\n");
#endif
        	/** Get repeat time and switch line time from system controller shared memory */
            g_sysctrl_repeat_time = (unsigned int) ( ( uC3InputSysctrladdr[SYSRECV_REPEAT_TIME_IDX]  * 1000 * 1000 ) / 10 ); // 1 = 10s unit, Convert sec to usec
            g_sysctrl_swline_time = (unsigned int)( ( uC3InputSysctrladdr[SYSRECV_SWLINE_TIME_IDX] | uC3InputSysctrladdr[SYSRECV_SWLINE_TIME_IDX + 1] << 8) * 1000 ) / 10;  // 1 = 500usec, Convert to usec

            /** Set start line selection to line 1 */
            g_sysctrl_lineslct = LINE1_SLCT;
            /** g_sysctrl_repeat_time!=0(auto mode with timeout) :Check all important variables */
            if( (g_sysctrl_repeat_time != 0) &&
                ((g_polling_cyc_tim > g_sysctrl_repeat_time) ||
                  (g_polling_cyc_tim > g_sysctrl_swline_time) ||
                  (g_sysctrl_lineslct < LINE1_SLCT) ||
                  (g_sysctrl_lineslct > LINE2_SLCT)))
            {
                ercd = E_PARAM_ERR;
                goto err_out;
            }
            /** Get processdata from shared memory */
            sysctrl_get_setup_pdodata();

            /** Set process data to each line send buffer */
        	_ecatpdo_set_outputprocessdata(LINE1_SLCT);
        	_ecatpdo_set_outputprocessdata(LINE2_SLCT);

        	/** Set return value to line buffer change request */
    		if(g_sysctrl_lineslct == LINE1_SLCT)
    		{
    			ercd = E_PDO_LINE1_WRREQ;
    		}
    		else if(g_sysctrl_lineslct == LINE2_SLCT)
    		{
    			ercd = E_PDO_LINE2_WRREQ;
    		}
    		else
    		{
    			ercd = E_SWLINE_ERR;
    		}

			/** Set current selected line */
			sysctrl_set_linests(g_sysctrl_lineslct + 1);

            /** Clear all trace buffer for next measurement */
            trace_clear_write_buffer();
            trace_reset_index();
            ecatpdo_clear_trace_ercd();

            /** Set all auto mode component flag */
    		g_polling_auto_flg = ENA_FLG;
            g_auto_set_recv_trace_flg = ENA_FLG;

            /** Time count */
            g_repeat_time_cnt += g_polling_cyc_tim;
            g_swline_time_cnt += g_polling_cyc_tim;
            break;

        case AUTO_2_AUTO:
        	if(g_polling_auto_flg == ENA_FLG)
        	{
        		/** Start auto mode when EtherCAT in OPERATION state */
        		if( g_acc_sts != APP_OPE ) goto err_out;

        		/** Check repeat time for time up */
                if(g_sysctrl_repeat_time != 0)
                {
            		if(g_repeat_time_cnt >= g_sysctrl_repeat_time)
                    {
                    	/** Stop process request */
                    	ecatpdo_stop_ecat_proc();

                        ercd = E_AUTO_TIMEDONE;
                        goto err_out;
                    }
                }

                /** Check switch line time for requst change send buffer */
                if(g_swline_time_cnt >= g_sysctrl_swline_time)
                {
                	g_swline_time_cnt = 0;
                    if(g_sysctrl_lineslct == LINE1_SLCT)
                    {
                    	g_sysctrl_lineslct = LINE2_SLCT;
            			ercd = E_PDO_LINE2_WRREQ;
                    }
                    else
                    {
                    	g_sysctrl_lineslct = LINE1_SLCT;
            			ercd = E_PDO_LINE1_WRREQ;
                    }

        			/** Set current selected line */
        			sysctrl_set_linests(g_sysctrl_lineslct + 1);

                }

                /** Time count */
                g_repeat_time_cnt += g_polling_cyc_tim;
                g_swline_time_cnt += g_polling_cyc_tim;
        	}
        	else
        	{
        		/** Stop process request */
        		ercd = E_PDO_NOREQ;
        	}
            break;

        case AUTO_2_STOP:
#ifdef GUI_DEBUG
            puts_com_opt("Mode change: AUTO to STOP\r\n");
#endif
        	/** Stop process request */
            g_sysctrl_swline_time = 0;
            g_sysctrl_repeat_time = 0;
            g_repeat_time_cnt = 0;
            g_swline_time_cnt = 0;
        	ecatpdo_stop_ecat_proc();
            ercd = E_STOP_PROCESS;
            break;

        case STOP_2_SEMIAUTO:	/** Start semi-auto mode */
#ifdef GUI_DEBUG
        	puts_com_opt("Mode change: STOP to SEMI-AUTO\r\n");
#endif
#ifdef IO_DEBUG
			gpio_write(IO_PORT0,0x1);
#endif
            /** Clear all trace buffer for next measurement */
            trace_clear_write_buffer();
            trace_reset_index();
            ecatpdo_clear_trace_ercd();

            /** Get processdata from shared memory */
            sysctrl_get_setup_pdodata();

            /** Set process data to each line send buffer */
        	_ecatpdo_set_outputprocessdata(LINE1_SLCT);
        	_ecatpdo_set_outputprocessdata(LINE2_SLCT);

        	/** Set start line selection to line 1 */
        	g_sysctrl_lineslct = LINE1_SLCT;
        	ercd = E_PDO_LINE1_WRREQ;

			/** Set current selected line */
			sysctrl_set_linests(g_sysctrl_lineslct + 1);

    		/** Set all semi-auto mode component flag */
            g_polling_semiauto_flg = ENA_FLG;
        	g_semiauto_set_recv_trace_flg = ENA_FLG;
            break;

        case SEMIAUTO_2_SEMIAUTO:
            if(g_polling_semiauto_flg == ENA_FLG)
            {
            	/** Check line select mode */
                g_sysctrl_new_linesw = uC3InputSysctrladdr[SYSRECV_LINEMODE_IDX];
                if(g_sysctrl_lineslct != g_sysctrl_new_linesw)
                {
                	/** If line mode has been changed store new line mode value and buffer change request */
                	g_sysctrl_lineslct = g_sysctrl_new_linesw;
            		if(g_sysctrl_lineslct == LINE1_SLCT)
            		{
            			ercd = E_PDO_LINE1_WRREQ;
            		}
            		else if(g_sysctrl_lineslct == LINE2_SLCT)
            		{
            			ercd = E_PDO_LINE2_WRREQ;
            		}
            		else
            		{
            			ercd = E_SWLINE_ERR;
            		}

        			/** Set current selected line */
        			sysctrl_set_linests(g_sysctrl_lineslct + 1);

                    /** Set all semi-auto mode component flag */
            		g_semiauto_set_recv_trace_flg = ENA_FLG;
                }
            }
            else
            {
            	/** When manual mode set to 0. stop process request */
            	ercd = E_PDO_NOREQ;
            }
            break;

        case SEMIAUTO_2_STOP:
#ifdef GUI_DEBUG
        	dbg1 = 0;
        	puts_com_opt("Mode change: SEMIAUTO to STOP\r\n");
#endif
        	/** Stop process request */
        	ecatpdo_stop_ecat_proc();
            ercd = E_STOP_PROCESS;
            break;

        case STOP_2_STOP:
        	/** Do nothing */
        	break;

        default:
            /** Do nothing */
            break;

    }

err_out:
    return ercd;
}

















