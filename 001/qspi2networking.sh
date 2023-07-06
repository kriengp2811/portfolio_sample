#!/bin/sh

set -x

## QSPI config location , target mount
QSPI_DEV=/dev/mtdblock2
QSPI_MNT_DIR=/var/qspi_mount

## Create or Overwrite filename
CFG_FILENAME=interfaces


NET_CFG_DIR=/etc/network/

generate_network_config()
{
## Create interfaces and generate default config
cat <<EOF >${QSPI_MNT_DIR}/${CFG_FILENAME}
# /etc/network/interfaces -- configuration file for ifup(8), ifdown(8)

# The loopback interface
auto lo
iface lo inet loopback

# Wired or wireless interfaces
auto eth0
iface eth0 inet static
address 192.168.11.1
netmask 255.255.0.0

EOF

}

install() {

        ## check device existance
        if [ -e ${QSPI_DEV} ]; then

                ## mount device MTDBLOCK
                if mount -o rw,errors=continue ${QSPI_DEV} ${QSPI_MNT_DIR}; then

                        ## check file interfaces existance
                        if ! cat "${QSPI_MNT_DIR}/${CFG_FILENAME}" 2>&1 >/dev/null; then

                                generate_network_config;
                                
                        fi

                        cp -f ${QSPI_MNT_DIR}/${CFG_FILENAME} ${NET_CFG_DIR}

                fi
        fi
}

uninstall() 
{
        ## check device existance
        if [ -e ${QSPI_DEV} ]; then

                ## check file interfaces existance
                if ! cat "${QSPI_MNT_DIR}/${CFG_FILENAME}" 2>&1 >/dev/null; then

                        echo "file not exist."

                 else
                        rm "${QSPI_MNT_DIR}/${CFG_FILENAME}"
                fi
        fi

        stop;
}

start() 
{
        install;
}

stop() 
{
        umount ${QSPI_DEV}
}

restart() 
{
        stop;
        start;
}

case "$1" in
start)
        start
        ;;
stop)
        stop
        ;;
restart)
        restart
        ;;
uninstall)
        uninstall
        ;;
*)
        echo "Usage: $0 {start|stop|restart}"
        exit 1
        ;;
esac
