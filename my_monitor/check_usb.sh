#!/bin/bash
# Check to see if radar device present at /dev/ttyACM0
usb_chk=`ls  /dev/ttyACM0`

printf "Current usb device for radar is: %s\n" "$usb_chk"
 
if [ "$usb_chk" == "/dev/ttyACM0" ];then 
   printf "Found device for radar at: %s\n" "$usb_chk"
elif [ "$usb_chk" == "" ];then
   # reboot
   sudo systemctl stop persist
   sudo /usr/sbin/reboot -f
fi
