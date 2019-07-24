import datetime, time
import select, socket, threading
import random, math
import os, sys
import logging

import proto
import macro
import helper
#import rmpDB


'''os.system("rm -rf classRatios.log")
logging.basicConfig(filename="classRatios.log", level=logging.INFO)
log = logging.getLogger("ex")
'''

def thresholdsToCString(policyMap):
	dataStr=""
	count = 0
	#Policy Format: {classID: ((thStart,thEnd), rate )}

	for (classID, threshold) in policyMap.iteritems():
		if count> 0:
			dataStr += ","
		dataStr += str(classID)+","+str(threshold[0][0])+","+str(threshold[0][1])
		count += 1
	return dataStr	

def getClassRates (policy):
        ratesList = []
        for classID in policy.keys():
                rates = policy[classID][1]
                ratesList.append(rates)
        return ratesList


def getClassThresholds(policyMap):
	classThresholds = {}
	for (classID, threshold) in policyMap.iteritems():
                classThresholds[classID] = (threshold[0][0], threshold[0][1])
        return classThresholds


class agent(object):
	def __init__(self, config):
		self.classThresholds = []
		self.classRates = []
		self.perClassLoad = {}
		self.flowSizeStats = []
		self.config = config
		self.epoll = None
		
		self.flowStatsList = []
		self.loadStatsList = {}
	
		self.sockType = {}
		self.sockList = {}

		self.rMsgList = {}
		self.sMsgList = {}		

		self.currentPolicyID = 0
		
		self.agentListenSock = None
		self.ctrlrSock = None	


	def run(self, ipAddr):
		ctrlrIPAddr = self.config['controllerIPAddr']
		ctrlrPort = int(self.config['controllerPort'])
		agentPort = int(self.config['agentPort'])
		agentIPAddr = self.config['agentIPAddr']
		
		dbHost = self.config['db_host']
		dbUsername = self.config['db_username']
		dbPasswd = self.config['db_passwd']
		dbName = self.config['db_dbname']
		
		#self.dbHandle = rmpDB.connect(dbHost, dbUsername, dbPasswd, dbName)
						

		agentIPAddr = ipAddr
		self.tosMap = self.config['tosMap'].split(',')
		self.flowStatDispInterval = self.config['flowStatsInterval']
		self.loadStatDispInterval = self.config['loadStatsInterval']

		self.workingMode = self.config['workingMode']
		
		try:
			self.agentListenSock = socket.socket(socket.AF_INET, \
							socket.SOCK_STREAM)
			self.agentListenSock.setsockopt(socket.SOL_SOCKET, \
							socket.SO_REUSEADDR, 1)
			self.agentListenSock.bind((agentIPAddr, agentPort))

			sockDesc = self.agentListenSock.fileno()	
			self.sockType[sockDesc] = macro.TYPE_SOCK_AGENTLISTEN
			self.sockList[sockDesc] = self.agentListenSock
			
			
			print "Listen socket created. socketDesc is %d" %sockDesc
			
		except socket.error:
			print "Error: Failed to setup agent socket."
			exit(0)
		try:
			self.ctrlrSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.ctrlrSock.connect((ctrlrIPAddr, ctrlrPort))
			
			sockDesc = self.ctrlrSock.fileno()
			self.sockType[sockDesc] = macro.TYPE_SOCK_CONTROLLER
			self.sockList[sockDesc] = self.ctrlrSock

			self.rMsgList[sockDesc] = ""
			self.sMsgList[sockDesc] = ""

			print "Controller socket created. socketDesc is %d" %sockDesc
		

		except socket.error, msg:
			print "Error: Failed to connect with controller. %s"%msg
			exit(0)

		agent = threading.Thread(name='eventHandler', \
					target=self.eventHandler)
		agent.setDaemon(True)
		agent.start()
				
	def eventHandler(self):
		self.agentListenSock.listen(10)
		self.epoll = select.epoll()
		
		sockDesc = self.agentListenSock.fileno()
		self.epoll.register(sockDesc, select.EPOLLIN)
		
		sockDesc = self.ctrlrSock.fileno()
		self.epoll.register(sockDesc, select.EPOLLIN)

		while True:
			try:
				events = self.epoll.poll(1)
			except socket.error, msg:
				print "Error: epoll polling issue %s" %msg
		
			for sockDesc, event in events:
				if sockDesc == self.agentListenSock.fileno():
					self.initNorthBoundCom()
				elif event & select.EPOLLERR:
					print "EPOLLERR OCCURRED"
					self.closeConnection(sockDesc)

				elif event & select.EPOLLIN:
					self.recvMsg(sockDesc)
				elif event & select.EPOLLOUT:
					self._sendMsg(sockDesc)
				elif event & select.EPOLLHUP:
					print "EPOLLHUP received"
					self.closeConnection(sockDesc)

		return 1
	
	def initNorthBoundCom(self):
		print "NorthBound Interface is up"
		connObj, appAddr = self.agentListenSock.accept()
		print "Received New Connection. SockDesc is %d" %connObj.fileno()
		connObj.setblocking(0)
		
		sockDesc = connObj.fileno()
		self.epoll.register(sockDesc, select.EPOLLIN | select.EPOLLHUP)
		self.sockList[sockDesc] = connObj
		self.sockType[sockDesc] = macro.TYPE_SOCK_APPLICATION
		
		self.rMsgList[sockDesc] = ""
		self.sMsgList[sockDesc] = ""

        def closeConnection(self, sockDesc):

		if self.isLive(sockDesc):
                	connObj = self.sockList[sockDesc]

               	 	del self.sockList[sockDesc]
                	del self.rMsgList[sockDesc]
                	del self.sMsgList[sockDesc]

                	self.epoll.modify(sockDesc, 0)
                	connObj.close()
			print "Connection Closed on socket %d" %sockDesc
		return

	def recvMsg(self, sockDesc):
		data = ""
		if self.isLive(sockDesc):
			connObj = self.sockList[sockDesc]
			try:
				data = connObj.recv(1000)
			except socket.error:
				self.closeConnection(sockDesc)
		else:
			self.closeConnection(sockDesc)
			return

		if not data:
			self.closeConnection(sockDesc)	
			return
		else:
			self.rMsgList[sockDesc] += data
		
		msgs = self.getMessage(sockDesc)
		for msg in msgs:
			if msg.endswith(macro.TYPE_EOFM):
				if self.sockType[sockDesc]==macro.TYPE_SOCK_APPLICATION:
					self.handleNorthBoundRC(msg)
				elif self.sockType[sockDesc]==macro.TYPE_SOCK_CONTROLLER:
					self.handleSouthBoundRC(msg)
	

        def sendMsg(self, sockDesc, msg):
		if self.isLive(sockDesc):
                	self.sMsgList[sockDesc] += msg
			self.epoll.modify(sockDesc, select.EPOLLOUT)
			return 1
		return -1
			

        def _sendMsg(self, sockDesc):
		retVal = 0
                if self.isLive(sockDesc):
			connObj = self.sockList[sockDesc]
                	msg = self.sMsgList[sockDesc]
			try:
                		retVal = connObj.send(msg)
                		self.epoll.modify(sockDesc, select.EPOLLIN)
				self.sMsgList[sockDesc] = ""
				return retVal
			except socket.error:
				return -1
		
		return -1

		

	def getMessage(self, sockDesc):
		msgs = []
		data = self.rMsgList[sockDesc]
		while (1):
			if "\n\n\n" in data:
				msg, data = data.split("\n\n\n",1)
				msg = msg+"\n\n\n"
				msgs.append(msg)
			else:
				self.rMsgList[sockDesc] = data
				break
		return msgs

	def handleNorthBoundRC(self, msg):

		if msg.endswith("\n\n\n"):
		
			pMsg = msg.rstrip('\n').lstrip('\x00').split('|')
			msgType = int(pMsg[0])
			msgCount = int(pMsg[1])
			msgData = pMsg[2]
	
			if msgType == proto.MTYPE_FLOW_STATS:
				count = self.addFlowStats(msgData)				

			elif msgType == proto.MTYPE_LOAD_STATS:
				count = self.addLoadStats(msgData)

	def handleSouthBoundRC(self, msg):
		msgType = proto.getMsgType(msg)
		if msgType == proto.MTYPE_ENFORCE_POLICY:

			policyID = proto.getPolicyID(msg)
			policy = proto.getMsgData(msg)

			#HM_Debug: ClassThreshold Old Format 
			#classThresholds = getClassThresholds(policy)

			classRatios = getClassRates(policy)

			self.currentPolicyID = policyID	
			self.pushClassThresholds(policy)

			self.enforceClassRatios(classRatios)
			self.logClassRatios(classRatios)

		return
	
	def addFlowStats(self, data):
		flowSizes = data.split(",")
		count = 0
	
		#print "Received New Flow Stats."

		for flowSize in flowSizes:
			if flowSize is not "" and int(flowSize)>0:
				timeStamp = str(datetime.datetime.now())
				flowStat = timeStamp+"|"+flowSize
				self.flowStatsList.append(flowStat)
				count += 1
		return count
	
	def addLoadStats(self, data):
		load = data.split(",")
		count = 0

		#print "Received New Load Stats."
		
		for loadStat in load:
			if loadStat is not "":
				classID, loadVal = loadStat.split(':')
				classID = int(classID)
				if classID in self.loadStatsList.keys():
					self.loadStatsList[classID] += int(loadVal)
				else:
					self.loadStatsList[classID] = int(loadVal)
				count += 1
		return count

	def getFlowStats(self):
		return self.flowStatsList
	
	def getLoadStats(self):
		return self.loadStatsList


	def postLoadStats(self, loadStats):
		msg = proto.makeLoadStats(loadStats)
		sockDesc = self.ctrlrSock.fileno()
		self.sendMsg(sockDesc, msg)
		return
	
	def postFlowStats(self, flowStats):
		msg = proto.makeFlowStats(flowStats)
		sockDesc = self.ctrlrSock.fileno()
		self.sendMsg(sockDesc, msg)
		return

	def pushClassThresholds(self, policy):
		#print "Class Thresholds to be pushed to application"
		for sockDesc in self.sockList.keys():
			
			if self.sockType[sockDesc] == macro.TYPE_SOCK_APPLICATION:
				connObj = self.sockList[sockDesc]
			
				classThresholds = getClassThresholds(policy)
				#rmpDB.insert_thresholds(self.dbHandle, classThresholds)
				
				policyCString = thresholdsToCString(policy) 
				count = len(policy)
				msg = proto.makeClassThresholdsCStr(count, policyCString)
				self.sendMsg(sockDesc, msg)

	def enforceClassRatios(self, classRatios):
	
		agentIPAddr = self.config['agentIPAddr']	

		linkRate = int(self.config['linkRate'])
		classCount = len(classRatios)
		if classCount > len(self.tosMap):
			print "TOS Map does not have sufficient mappings. Exiting Now"		
			exit(0)
		
		ifname = helper.getIfnamebyIP(agentIPAddr)
		_enforceClassRatios(ifname, linkRate, classRatios, self.tosMap)
	
	def isLive(self, sockDesc):
		if sockDesc in self.sockList.keys():
			return True
		return False
	
	def logClassRatios(self, classRatios):
		data = " ".join(map(str, classRatios))
		#log.info(data)
		
def _enforceClassRatios(ifname, linkRate, classRatios, tosMap):

	classRates = []
	linkRate = linkRate*1000
	for ratio in classRatios:
		rate = int(float(ratio)*linkRate)
		classRates.append(rate)
	
	numClasses = len(classRates)

	print "Enforcing Rates on %s: %s" %(ifname, classRates)
	os.system("tc qdisc delete dev %s root" % ifname)
	os.system("tc qdisc add dev %s root handle 1: htb default 1%d" \
					% (ifname,numClasses-1))
	os.system("tc class add dev %s parent 1: classid 1:1 htb rate %dkbit ceil %dkbit" \
					% (ifname,linkRate,linkRate))

	for cid in range(numClasses):
		os.system("tc class add dev %s parent 1:1 classid 1:1%d htb rate %dkbit ceil %dkbit" % \
			(ifname,cid,classRates[cid], linkRate))
		os.system("tc filter add dev %s protocol ip parent 1:0 prio 1 u32 match ip tos %d 0xff flowid 1:1%d" % \
			(ifname,int(tosMap[cid]),cid))




def loadConfig():
	fh = open("config_agent.txt")
	config = {}
	for line in fh:
		key, value = line.rstrip().split(' ')
		config[key] = value
	return config


def sendFlowStats(agentHandle, timer):
	while True:
		flowStatsList = []
		flowStatsList = agentHandle.getFlowStats()
		if len(flowStatsList) != 0:
			agentHandle.postFlowStats(flowStatsList)
			agentHandle.flowStatsList = []
		time.sleep(timer)

if __name__ == "__main__":
	
	modes = ["host", "switch"]
	if len(sys.argv) < 4:
		print "Usage: python agent.py <ipAddr> -m <mode>"
		exit(0)
	if sys.argv[2] != "-m":
		print "Usage: python agent.py <ipAddr> -m <mode>"
		exit(0)
	if sys.argv[3] not in modes:
		print "Error: Unknown mode of operation. Choose 'host' or 'switch'"
		exit(0)

	ipAddr = sys.argv[1]	
	config = loadConfig()	
	tosMap = config['tosMap'].split(',')
	classRatios = config['initClassRatios'].split(',')
	linkRate = int(config['linkRate'])
	ifname = helper.getIfnamebyIP(ipAddr)
	
	config["agentIPAddr"] = ipAddr

	_enforceClassRatios(ifname, linkRate, classRatios, tosMap)
	
	#Starts an agent as a daemon	
	agentHandle = agent(config)	
	agentHandle.run(ipAddr)

	fssTimer = int(config['flowStatsInterval'])
	lssTime = int(config['loadStatsInterval'])


	'''Needs to send flow stats and load stats perdiodically
	The interval of both transmissions could be different so
	we need to run both transmissions as two separate daemons.
	flowStatsSender send flow stats to the controller. The
	load stats transmission is done in the main program in a
	while loop
	'''
	

	flowStatsSender = threading.Thread(name='eventHandler', \
				target=sendFlowStats, args=(agentHandle,fssTimer,))
	flowStatsSender.setDaemon(True)
	flowStatsSender.start()

	while True:
		post = False
		loadStatsList = {}
		loadStatsList = agentHandle.getLoadStats()
		for (classID, val) in loadStatsList.iteritems():
			if val > 0:
				post = True
				break
		if post == True:
			agentHandle.postLoadStats(loadStatsList)
			#needs a wrapper here to reset the loadStatsList
			agentHandle.loadStatsList = {}
		time.sleep(lssTime)
