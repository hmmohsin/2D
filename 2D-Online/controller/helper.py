import os
import struct, socket, fcntl

def readDataFile(fileName):
	dataList = []
	fileHandle = open(fileName,"r")
	for line in fileHandle:
		value = int(line.rstrip())
		dataList.append(value)
	return dataList
	
def getInterfaceList():
	ifaceList = os.listdir("/sys/class/net")
	return ifaceList
	
def getIPbyifname(ifname):
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	ipAddr = socket.inet_ntoa(fcntl.ioctl(s.fileno(),0x8915, \
			struct.pack('256s', ifname[:15]))[20:24])
	return ipAddr

def getIfnamebyIP(ipAddrTarget):
	ifaceList = getInterfaceList()

	for ifname in ifaceList:
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		try:
			ipAddr = socket.inet_ntoa(fcntl.ioctl(s.fileno(),0x8915,\
				struct.pack('256s', ifname[:15]))[20:24])
		except:
			continue

		if ipAddr == ipAddrTarget:
			return ifname
	return ""

def getIfnamebyIPPrefix(ipAddrTargetPrefix):
	ifaceList = getInterfaceList()

	for ifname in ifaceList:
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		ipAddr = socket.inet_ntoa(fcntl.ioctl(s.fileno(),0x8915,\
				struct.pack('256s', ifname[:15]))[20:24])

		if ipAddr.startswith(ipAddrTargetPrefix):
			return ifname
	return ""
