import struct
import pickle
import sys

MTYPE_REGISTER 		= 1
MTYPE_RESGISTER_ACK 	= 2
MTYPE_FLOW_STATS_REQ 	= 3
MTYPE_LOAD_STATS_REQ 	= 4
MTYPE_RATES_REQ 	= 5
MTYPE_CLASSES_REQ	= 6

MTYPE_RESPONSES		= 10
MTYPE_FLOW_STATS 	= 11
MTYPE_LOAD_STATS 	= 12
MTYPE_RATES		= 13
MTYPE_CLASSES		= 14
MTYPE_ENFORCE_POLICY	= 15

def makeReq():
	msg = struct.pack('i', MTYPE_REGISTER)
	return msg

def makeReqAck():
	msg = struct.pack('i', MTYPE_RESGISTER_ACK)
	return msg

def makeFlowStatsReq():
	msg = struct.pack('i', MTYPE_FLOW_STATS_REQ)
	return msg

def makeLoadStatsReq():
	msg = struct.pack('i', MTYPE_LOAD_STATS_REQ)
	return msg

def makeRatesReq():
	msg = struct.pack('i', MTYPE_RATES_REQ)
	return msg

def makeClassesReq():
	msg = struct.pack('i', MTYPE_CLASSES_REQ)
	return msg

def makeFlowStats(stats):
	statsCount = len(stats)
	#print "Appending %d flowstats" %statsCount
	#if statsCount < 1000:
	#	print stats
	msgHdr = struct.pack('ii', MTYPE_FLOW_STATS, statsCount)
	
	msgData = pickle.dumps(stats)
	msg = msgHdr+msgData+"\n\n\n"
	return msg

def makeLoadStats(stats):
	statsCount = len(stats)
	msgHdr = struct.pack('ii', MTYPE_LOAD_STATS, statsCount)
	
	msgData = pickle.dumps(stats)
	msg = msgHdr+msgData+"\n\n\n"
	return msg

def makeClassRates(rates):
	ratesCount = len(stats)
	msgHdr = struct.pack('ii', MTYPE_RATES, ratesCount)
	
	msgData = pickle.dumps(rates)
	msg = msgHdr+msgData+"\n\n\n"
	return msg

def makeClassThresholds(classes):
	classesCount = len(classes)
	msgHdr = struct.pack('ii', MTYPE_CLASSES, classesCount)

	msgData = pickle.dumps(classes)
	msg = msgHdr+msgData+"\n\n\n"
	return msg

def makeClassThresholdsCStr(count, classes):
	msgHdr = struct.pack('ii', MTYPE_CLASSES, count)

	msg = msgHdr+str(classes)+'\0'
	return msg

def makePolicyMsg(policyID, policy):
	msgHdr = struct.pack('ii', MTYPE_ENFORCE_POLICY, policyID)
	
	msgData = pickle.dumps(policy)
	msg = msgHdr+msgData+"\n\n\n"
	return msg

def getMsgType(msg):
	msgType = int(struct.unpack('i',msg[:4])[0])
	return msgType

def getPolicyID(msg):
	policyID = int(struct.unpack('i',msg[4:8])[0])
	return policyID

def getTupleCount(msg):
	dataTupleCount = int(struct.unpack('i',msg[4:8])[0])
	return dataTupleCount

def getMsgData(msg):
	data = pickle.loads(msg[8:])
	return data

