# Intellinet IP smart PDU API [163682]

A python API wrapper for Intellinet IP smart PDU [163682] that allows you to do anything
that the web interface provides.

You can:
* read all sensors (humidity, temperature)
* read voltages
* get states of outlets
* turn outlets on/off/toggle
* read and set warning levels
* ...


Install from GitHub:

```
pip3 install git+https://github.com/oe-fet/Intellinet_163682_IP_smart_PDU_API
```

Example usage:

```
from intellinet_pdu import IPU

pdu = IPU("192.168.1.123")
pdu.disable_outlets("outlet0")
```