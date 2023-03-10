#!/bin/sh
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright (C) 2012 Aleksander Morgado <aleksander@gnu.org>



#ip link set dev wwan0 down
#echo Y > /sys/class/net/wwan0/qmi/raw_ip
#ip link set dev wwan0 up
#qmicli --device=/dev/cdc-wdm0 --device-open-proxy --wds-start-network="ip-type=4,apn=internet,autoconnect=yes" --client-no-release-cid
#udhcpc -q -f -n -i wwan0



print_usage ()
{
#    echo "usage: $0 [DEVICE] [COMMAND]"
    echo "usage: $0 [COMMAND=start|stop]"
}
if [ $# -ne 1 ]; then
    echo "error: missing arguments" 1>&2
    print_usage
    exit 255
fi

#DEVICE=$1
#COMMAND=$2
DEVICE=/dev/cdc-wdm0
COMMAND=$1
STATE_FILE=/tmp/qmi-network-state
PROFILE_FILE=/etc/qmi-network.conf
load_profile ()
{
    if [ -f $PROFILE_FILE ]; then
        echo "Loading profile..."
        source $PROFILE_FILE
        if [ "x$APN" != "x" ]; then
            echo "    APN: $APN"
        fi
    fi
}
save_state ()
{
    KEY=$1
    VAL=$2
    echo "Saving state... ($KEY: $VAL)"
    if [ -f $STATE_FILE ]; then
        PREVIOUS=`cat $STATE_FILE`
        PREVIOUS=`echo "$PREVIOUS" | grep -v $KEY`
        if [ "x$PREVIOUS" != "x" ]; then
            echo $PREVIOUS > $STATE_FILE
        else
            rm $STATE_FILE
        fi
    fi
    if [ "x$VAL" != "x" ]; then
        echo "$KEY=\"$VAL\"" >> $STATE_FILE
    fi
}
load_state ()
{
    if [ -f $STATE_FILE ]; then
        echo "Loading previous state..."
        source $STATE_FILE
        if [ "x$CID" != "x" ]; then
            echo "    Previous CID: $CID"
        fi
        if [ "x$PDH" != "x" ]; then
            echo "    Previous PDH: $PDH"
        fi
    fi
}
clear_state ()
{
    echo "Clearing state..."
    rm -f $STATE_FILE
}
# qmicli -d /dev/cdc-wdm0 --wds-start-network --client-no-release-cid
# [/dev/cdc-wdm0] Network started
# 	Packet data handle: 3634026241
# [/dev/cdc-wdm0] Client ID not released:
# 	Service: 'wds'
# 	    CID: '80'
start_network ()
{
    if [ "x$CID" != "x" ]; then
        USE_PREVIOUS_CID="--client-cid=$CID"
    fi
    if [ "x$PDH" != "x" ]; then
        echo "error: cannot re-start network, PDH already exists" 1>&2
        exit 3
    fi
    START_NETWORK_CMD="qmicli -d $DEVICE --device-open-proxy --wds-start-network=$APN $USE_PREVIOUS_CID --client-no-release-cid"
    echo "Starting network with '$START_NETWORK_CMD'..."
    if [ "x$QMIDEBUG" != "x" ]; then
        START_NETWORK_OUT="\
[/dev/cdc-wdm0] Network started
	Packet data handle: '3634026241'
[/dev/cdc-wdm0] Client ID not released:
	Service: 'wds'
	CID: '80'"
    else
	ip link set dev wwan0 down
	echo Y > /sys/class/net/wwan0/qmi/raw_ip
	ip link set dev wwan0 up
#	qmicli --device=/dev/cdc-wdm0 --device-open-proxy --wds-start-network="ip-type=4,apn=internet,autoconnect=yes" --client-no-release-cid
	START_NETWORK_OUT=`$START_NETWORK_CMD`
    fi
    # Save the new CID if we didn't use any before
    if [ "x$CID" = "x" ]; then
        CID=`echo "$START_NETWORK_OUT" | sed -n "s/.*CID.*'\(.*\)'.*/\1/p"`
        if [ "x$CID" = "x" ]; then
            echo "error: network start failed, client not allocated" 1>&2
            exit 1
        else
            udhcpc -q -f -n -i wwan0
            save_state "CID" $CID
        fi
    fi
    PDH=`echo "$START_NETWORK_OUT" | sed -n "s/.*handle.*'\(.*\)'.*/\1/p"`
    if [ "x$PDH" = "x" ]; then
        echo "error: network start failed, no packet data handle" 1>&2
        # Cleanup the client
        qmicli -d "$DEVICE" --wds-noop --client-cid="$CID"
        clear_state
        exit 2
    else
        save_state "PDH" $PDH
    fi
    echo "Network started successfully"
}
# qmicli -d /dev/cdc-wdm0 --wds-stop-network
stop_network ()
{
    if [ "x$CID" = "x" ]; then
        echo "Network already stopped"
    elif [ "x$PDH" = "x" ]; then
        echo "Network already stopped; need to cleanup CID $CID"
        # Cleanup the client
        qmicli -d "$DEVICE" --wds-noop --client-cid="$CID"
    else
        STOP_NETWORK_CMD="qmicli -d $DEVICE --wds-stop-network=$PDH --client-cid=$CID"
        echo "Stopping network with '$STOP_NETWORK_CMD'..."
        if [ "x$QMIDEBUG" != "x" ]; then
            STOP_NETWORK_OUT="\
[/dev/cdc-wdm0] Network stopped
"
        else
            STOP_NETWORK_OUT=`$STOP_NETWORK_CMD`
        fi
        echo "Network stopped successfully"
    fi
    clear_state
}
# qmicli -d /dev/cdc-wdm0 --wds-get-packet-service-status
packet_service_status ()
{
    if [ "x$CID" != "x" ]; then
        USE_PREVIOUS_CID="--client-cid=$CID --client-no-release-cid"
    fi
    STATUS_CMD="qmicli -d $DEVICE --wds-get-packet-service-status $USE_PREVIOUS_CID"
    echo "Getting status with '$STATUS_CMD'..."
    if [ "x$QMIDEBUG" != "x" ]; then
        STATUS_OUT="\
[/dev/cdc-wdm0] Connection status: 'disconnected'
"
    else
        STATUS_OUT=`$STATUS_CMD`
    fi
    CONN=`echo "$STATUS_OUT" | sed -n "s/.*Connection status:.*'\(.*\)'.*/\1/p"`
    if [ "x$CONN" = "x" ]; then
        echo "error: couldn't get packet service status" 1>&2
        exit 2
    else
        echo "Status: $CONN"
        if [ "x$CONN" != "xconnected" ]; then
            exit 64
        fi
    fi
}
# Main
# Load profile, if any
load_profile
# Load previous state, if any
load_state
# Process commands
case $COMMAND in
    "start")
        start_network
        ;;
    "stop")
        stop_network
        ;;
    "status")
        packet_service_status
        ;;
    *)
        echo "error: unexpected command '$COMMAND'" 1>&2
        print_usage
        exit 255
        ;;
esac
exit 0
