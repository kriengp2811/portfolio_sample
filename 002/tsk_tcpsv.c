/*
 * @file    : tsk_tcpsv.c
 * @brief   : Task for TCP Server Source File
 * @version : 1.0.0
 * @date    : xxxxxxxxxxxxx
 * @authors : Krienglit
 */

#include <arpa/inet.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <strings.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/mman.h>
#include <unistd.h>
#include <stdbool.h>
#include <errno.h>
#include <syslog.h>
#include <rtdk.h>
#include <pthread.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <rtdm/rtdm.h>
#include <native/task.h>
#include <native/sem.h>
#include "reg_sys_init.h"
#include "msg_protocol.h"
#include "acoustic_sensor.h"
#include "temp_sensor.h"
#include "fpga_io.h"
#include "wdt_acc.h"
#include "hps_io.h"
#include "qspi_acc.h"
#include "string_man.h"
#include "err_lib.h"
#include "logger_module.h"

/************************************************
 * Definitions
 ***********************************************/
#define MAXLINE                 4096
#define MAX_ACCEPT              10
#define MAX_FD(x,y)             (x>y?x:y)
#define RECV_TIMEOUT            600


/************************************************
 * Global Variables
 ***********************************************/
extern struct buf_info *g_slct_msg_buf;

extern struct eth_config g_cfg_info;

extern bool g_is_app_run;

/**
 *  @brief socket accepted file distributor
 * */
int g_snd_connfd = 0;
int g_last_connfd = 0;

/************************************************
 * Functions
 ***********************************************/
int tsk_sndmsg(void);
int eth_var_config(int argc, char *argv[]);     /*!< ethernet configuration setting on QSPI */

int tsk_tcpsv(void)
{
    int ret = 0;
    socklen_t len;
    int snd_listenfd, nready, maxfdp1, conn_request_skt;
    struct sockaddr_in snd_cliaddr, snd_servaddr;
    struct timeval tv;
    int size, optlen;
    fd_set rset;
    fd_set tmp_rset;

    /**! create listening TCP socket */
    snd_listenfd = socket(AF_INET, SOCK_STREAM, 0);
    if (snd_listenfd < 0)
    {
        ERROR_TRACE("snd_listenfd socket failed %d\n",ret);
        goto end_tcpsvtsk;
    }
    INFO_TRACE("snd_listenfd socket ok\n",0);

    /**! 
     * send server config 
     * ip_address = up to linux ip config [INADDR_ANY]
     * */
    bzero(&snd_servaddr, sizeof(snd_servaddr));
    snd_servaddr.sin_family = AF_INET;
    snd_servaddr.sin_addr.s_addr = INADDR_ANY;
    snd_servaddr.sin_port = htons(ETH_DEFAULT_SND_PORT);

    /**! set socket to non-blocking state */
    fcntl(snd_listenfd, F_SETFL, O_NONBLOCK);

    /**! binding server addr structure to snd_listenfd */
    ret = bind(snd_listenfd, (struct sockaddr*)&snd_servaddr, sizeof(snd_servaddr));
    if (ret == -1)
    {
        ERROR_TRACE("snd_listenfd bind failed %d\n",ret);
        goto end_tcpsvtsk;
    }
    INFO_TRACE("snd_listenfd bind ok\n",0);

    ret = listen(snd_listenfd, MAX_ACCEPT);
    if (ret == -1) 
    {
        ERROR_TRACE("snd_listenfd listen failed %d\n",ret);
        goto end_tcpsvtsk;
    }
    INFO_TRACE("snd_listenfd listen ok\n",0);

    maxfdp1 = snd_listenfd + 1;
    
    /**! clear the descriptor set */
    FD_ZERO(&rset);

    /**! set snd_listenfd in readset */
    FD_SET(snd_listenfd, &rset);

    tmp_rset = rset;
    
    while(1) 
    {
        rset = tmp_rset;
 
        /**! wait for select the ready descriptor */
        nready = select(maxfdp1, &rset, NULL, NULL, NULL);
        if(nready<0)
        {
            ERROR_TRACE("select() failed\n",0);
        }
        if(nready>0)
        {
            /**! 
             * if tcp socket is readable then handle it
             * by accepting the connection 
             */
            if (FD_ISSET(snd_listenfd, &rset)) {
                conn_request_skt = snd_listenfd;
                len = sizeof(snd_cliaddr);
                g_snd_connfd = accept(conn_request_skt, (struct sockaddr*)&snd_cliaddr, &len);

                DEBUG_TRACE("start Send Socket\n",0);

                if (g_snd_connfd < 0)
                {
                    ERROR_TRACE("accept() failed\n",0);
                    g_snd_connfd = 0;
                }
                else if (g_snd_connfd > 0)
                {
                    if ((g_snd_connfd != g_last_connfd) && (g_last_connfd != 0)) 
                    {
                        /**!
                         * when duplicate connection detected
                         * connect to lastest connection instead
                        */
                        INFO_TRACE("Duplicate on socket %d set to lastest connection on socket %d\n", g_last_connfd, g_snd_connfd);
                        close(g_last_connfd);
                    }
                    else
                    {
                        INFO_TRACE("Start new connection on socket %d\n", g_snd_connfd);
                    }

                    g_last_connfd = g_snd_connfd;
                }
            }

        }
    }
end_tcpsvtsk:
    if (g_snd_connfd > 0) {
        close(g_snd_connfd);
    }
    INFO_TRACE("tsk tcpsv exit\n",0);
    g_is_app_run = false;
}



int tsk_sndmsg(void)
{
    int ret;
    int buf_cnt;
    int buf_no = 0;
    unsigned char *snd_buf_addr;

    INFO_TRACE("start %s\n", __func__);

    while(1)
    {
        rt_task_sleep_until(TM_INFINITE);

        for (buf_cnt = 0; buf_cnt < MSG_BUF_NUM; buf_cnt++)
        {
            if (*(g_slct_msg_buf[buf_cnt].buf_sts) == STS_SENDING)
            {
                buf_no = buf_cnt;
                break;
            }
        }
        snd_buf_addr = (unsigned char *)g_slct_msg_buf[buf_no].snd_buf;

        /**
         * @attention please do not change value in MSG_PTCL_SIZE !!
         *          because client's software always check message size before receive
        */
        ret = send(g_snd_connfd, snd_buf_addr, MSG_PTCL_SIZE, MSG_NOSIGNAL);
        if (ret < 0)
        {
            if(errno == EPIPE)
            {
                INFO_TRACE("Client req  %d, socket  %d closed\n", errno, g_snd_connfd);
            }
            else
            {
                INFO_TRACE("Send error %d, socket  %d closed\n", errno, g_snd_connfd);
            }
            goto err_tcpsv;
        }
        else if (ret == 0)
        {
            INFO_TRACE("Send connection closed by party on socket %d\n", g_snd_connfd);
            goto err_tcpsv;
        }
        else
        {
            /**! 
             * send complete case 
             * do nothing 
             * */
        }

        *(g_slct_msg_buf[buf_no].buf_sts) = STS_NOT_USE;
        continue;

err_tcpsv:
        if(g_snd_connfd > 0)
        {
            close(g_snd_connfd);
            g_snd_connfd = 0;
            g_last_connfd = 0;
        } 

        *(g_slct_msg_buf[buf_no].buf_sts) = STS_NOT_USE;
    }

}