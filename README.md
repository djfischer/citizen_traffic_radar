# Citizen Traffic Monitor

This is a simple traffic monitoring device that uses a Raspberry Pi for acquiring the traffic data. It
utilizes a compact doppler radar to monitor a roadway and captures bi-directional vehicle counts and speeds.
The device can operate continuously as a service and is able to upload the data to the cloud via a simple 
USB 4G stick. An optional camera is added to the device for security purposes and can be used to capture a 
street view.

## History 
Our neighborhood is situated between two artierial steets and receives significant cut-through traffic.
Concerned citizens have formed a neighborhood association and this device was built to help the 
association understand vehicle traffic volumes and patterns. 

## Hardware
Other hardware could be used, but here the subject device is built with:
 * [Raspberry Pi 3B+] - https://www.raspberrypi.com/products/raspberry-pi-3-model-b-plus/ ~$35
 * [Omnipresence OPS-243A doppler radar sensor] - https://omnipresense.com/product/ops243-doppler-radar-sensor/ ~$209
 * [Arducam 8MP Noir camera for Raspberry Pi] https://www.uctronics.com/arducam-noir-8mp-sony-imx219-camera-module-with-cs-lens-2717-for-raspberry-pi.html] ~$60
 * [Polycase WQ-48 hinged waterproof enclosure & mounting panel]  - https://www.polycase.com/wq-48 & https://www.polycase.com/wq-48p ~ $35 & $3.50 
 * [4G WiFi USB Mobile Modem] https://smile.amazon.com/dp/B08NX14VQZ?psc=1&ref=ppx_yo2_dt_b_product_details ~$36
 * [Optional - Voltaic Systems V50 USB battery pack for backup power] - https://voltaicsystems.com/amp/v50/ ~$65
 * 3D printed mounts for Raspberry Pi, OpS-243A Doppler Radar, USB modem, camera, and for mounting unit onto a pole made from electrical conduit
 * Various fasteners
 * Various USB Cables

## Cloud
As built, the device uploads data to a Cloud of your choice using rclone and crontab

## Known Issues
There are a a few issues with the current build:
 * The OPS-243A radar card connects to the Raspberry Pi via USB. This USB connection can drop, so a simple
   routine was developed to check the status of this connection every 5  minutes via a shell script and
   crontab. If the connection drops, the Raspberry Pi is rebooted
 * As the device must be located off the monitored roadway, there is a cosine correction that could be
   applied to the detected speeds. As the mounting position will typically result in a small incident
   angle, this correction is currently ignored in the acquisition software.
