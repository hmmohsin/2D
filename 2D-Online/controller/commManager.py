import socket
import select
import multiprocessing
import proto
import errors
import time

EOFM = "\n\n\n"
MAXMSGLEN = 10000

class commManager(object):
	def __init__(self, nodesInfo, ipAddr, port, dataStoreHandle):
		self.nodesInfo = nodesInfo
		self.ipAddr = ipAddr
		self.port = port
		self.dataStoreHandle = dataStoreHandle

		self.servSock = None

		self.agentAddrMap = {}
		self.agentsConnList = {}

		self.sMsgList = {}
		self.rMsgList = {}

		self.epoll = None		
		self.shutdown = 0
		self.policyID = 0

		try:
			self.servSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.servSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.servSock.bind((self.ipAddr, self.port))
		except socket.error, msg:
			print "Error: Failed to initialize Communication Manager %s" %msg
			exit(0)
		''' Handle connection initialization here '''
		
	def init_connection(self):
    		connObj, addr = self.servSock.accept()
    		connObj.setblocking(0)

		agentAddr = addr[0]
		print "CommManager: Received connection request from %s" %agentAddr
    		sockDesc = connObj.fileno()
    		self.epoll.register(sockDesc, select.EPOLLIN | select.EPOLLERR |select.EPOLLHUP)
	
		self.agentsConnList[sockDesc] = connObj		
		self.agentAddrMap[sockDesc] = agentAddr

		self.rMsgList[sockDesc] = ""
		self.sMsgList[sockDesc] = ""
	
		currClassThresholds = self.dataStoreHandle.getClassThresholds()
		currClassRatios = self.dataStoreHandle.getClassRatios()
		if currClassThresholds == "" or currClassRatios == "":
			return
		self.policyDispatcher(currClassThresholds, currClassRatios)
		

	def closeConnection(self, agentSockDesc):
        
		if self.isLive(agentSockDesc):
	
			agentAddr = self.agentAddrMap[agentSockDesc]
			agentConnObj = self.agentsConnList[agentSockDesc]
			
			del self.agentsConnList[agentSockDesc]
			del self.agentAddrMap[agentSockDesc]
			del self.rMsgList[agentSockDesc]
			del self.sMsgList[agentSockDesc]
		
			self.epoll.modify(agentSockDesc, 0)
			agentConnObj.close()
			print "CommManager: Connection closed %s"%agentAddr
		
	def recvMsg(self, agentSockDesc):
		agentConnObj = self.agentsConnList[agentSockDesc]
		
		agentAddr = ""
		data = ""
		if self.isLive(agentSockDesc):
			agentAddr = self.agentAddrMap[agentSockDesc]

		try:
			data = agentConnObj.recv(MAXMSGLEN)
			if not data:
				self.closeConnection(agentSockDesc)
				return
			else:
				self.rMsgList[agentSockDesc] += data
		except socket.error:
        	        print "CommManager: Error occurred on connection %s" %agentAddr
			self.closeConnection(agentSockDesc)
			return			
		
		msg = self.getMessages(agentSockDesc)
			
		if len(msg) >= 4:
			msgType = proto.getMsgType(msg)

			if (msgType == proto.MTYPE_REGISTER):
				print "CommManager: Received register request from %s" %agentAddr
				response = proto.makeReqAck()
				self.sendMsg(agentSockDesc, response)
			
				self.rMsgList[agentSockDesc] = ""

			if (msgType == proto.MTYPE_FLOW_STATS and msg.endswith(EOFM)):
				statsCount = proto.getTupleCount(msg)
				#print "commManager: %d Flow Stats Received from %s" %(statsCount, agentAddr)
				
				statsData = proto.getMsgData(msg)
			
				count = self.dataStoreHandle.addFlowStats(statsData)
				self.rMsgList[agentSockDesc] = ""

			if (msgType == proto.MTYPE_LOAD_STATS and msg.endswith(EOFM)):
				statsCount = proto.getTupleCount(msg)
				#print "commManager: %d Load Stats Received from %s" %(statsCount, agentAddr)
				
				statsData = proto.getMsgData(msg)
				
				count = self.dataStoreHandle.addLoadStats(statsData)
				self.rMsgList[agentSockDesc] = ""

		
		''' Process the message here '''
	
	def sendMsg(self, agentSockDesc, msg):
		if self.isLive(agentSockDesc):
			self.sMsgList[agentSockDesc] += msg
		else:
			return errors.ERROR_NODENOTFOUND
		try:
			self.epoll.modify(agentSockDesc,select.EPOLLOUT)
			return 1
		except socket.error:
			return errors.ERROR_EPOLLMOD_EPOLLOUT_FAILED

	def _sendMsg(self, agentSockDesc):
		
		if self.isLive(agentSockDesc):
			agentConnObj = self.agentsConnList[agentSockDesc]
			msg = self.sMsgList[agentSockDesc]
			
			try:
				bytes_sent = agentConnObj.send(msg)
				self.epoll.modify(agentSockDesc, select.EPOLLIN)
				self.sMsgList[agentSockDesc] = ""
				return bytes_sent
			except:
				return errors.ERROR_SENDFAILED

	def eventHandler(self):
		self.servSock.listen(10)
		self.epoll = select.epoll()
		self.epoll.register(self.servSock.fileno(), select.EPOLLIN)
		
		while True:
		   try:
		      events = self.epoll.poll(1)
		   except socket.error, msg:
		      print "CommManager: epoll polling issue %s" %msg
			
		   for sockDesc, event in events:
		      if sockDesc == self.servSock.fileno():
		         self.init_connection()
		      elif event & select.EPOLLIN:
			 self.recvMsg(sockDesc)
		      elif event & select.EPOLLOUT:
                         self._sendMsg(sockDesc)
	
	def policyDispatcher(self, thresholdsList, ratesList):
		if thresholdsList == "" or len(thresholdsList) == 0:
			return
		if ratesList == "" or len(ratesList) == 0:
			return

		thresholdsCount = len(thresholdsList.keys())
		ratesCount = len(ratesList.keys())
		
		if ratesCount != thresholdsCount:
			print "CommManager: Policy Conflict-1"
			return errors.ERROR_POLICYCONFLICT_1
		
		policy = {}
		for classID in thresholdsList.keys():
			if classID not in ratesList.keys():
				print "CommManager: Policy Conflict-2"
				return errors.ERROR_POLICYCONFLICT_2
				
			policy[classID] = (thresholdsList[classID], ratesList[classID])
		
		msg = proto.makePolicyMsg(self.policyID, policy)	

		for (sockDesc, connObj) in self.agentsConnList.iteritems():
			agentAddr = self.agentAddrMap[sockDesc]

			retVal = self.sendMsg(sockDesc, msg)
			if retVal in errors.ERRORSLIST:
				print "CommManager: Failed to send policy to %s" %agentAddr
			else:
				print "CommManager: Policy Message Sent to %s" %agentAddr

		#self.policyID += 1
	
	def isLive(self, agentSockDesc):
		if agentSockDesc in self.agentsConnList.keys():
			return True
		return False

	def getMessages(self, agentSockDesc):
		if EOFM in self.rMsgList[agentSockDesc]:
			msg, data = self.rMsgList[agentSockDesc].split(EOFM, 1)
			self.rMsgList[agentSockDesc] = data
			msg = msg+EOFM
			return msg
		return self.rMsgList[agentSockDesc]
		
			

