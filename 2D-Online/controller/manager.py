import os
import dataStore
import compEngine
import commManager
import helper
import proto

import threading
import signal

INF = 100000000000

class manager(object):
	def __init__(self):
		self.dataStoreHandle = None
		self.commHandle = None
		self.compEngine = None
			

	def initialize(self, ipAddr, port):
		tmp = []
		signal.signal(signal.SIGTERM, signal_handler)

		self.dataStoreHandle = dataStore.dataStore()
		self.compEngine = compEngine.compEngine()
		self.commHandle = commManager.commManager(tmp, ipAddr, port, self.dataStoreHandle)
	
		eventHandler = threading.Thread(name='comEventHandler', target=self.commHandle.eventHandler)
		eventHandler.setDaemon(True)	
		eventHandler.start()
	
	def initClassThresholds(self, classThresholds):
		classCount = len(classThresholds)
		classThresholdsList = {}
		classID = 0
		thStart = 0
		thEnd = 0
		for thresholds in classThresholds:
			thEnd = thresholds
			classThresholdsList[classID] = (thStart, thEnd)
			thStart = thEnd+1
			classID += 1
		classThresholdsList[classID] = (thStart, INF)	
	
		self.setClassThresholds(classThresholdsList)

		return
	
	def initClassRatios(self, classRatios):
		classCount = len(classRatios)
		classRatiosList = {}
		classID = 0
		for classRatio in classRatios:
			classRatiosList[classID] = classRatio
			classID += 1
		
		self.setClassRatios(classRatiosList)
		
		return

	def setClassThresholds(self, classThresholds):
		self.dataStoreHandle.setClassThresholds(classThresholds)

	def setClassRatios(self, classRatios):
		self.dataStoreHandle.setClassRatios(classRatios)

	def getClassThresholds(self):
		classThresholds = self.dataStoreHandle.getClassThresholds()
		return classThresholds

	def getClassRatios(self):
		classRatios = self.dataStoreHandle.getClassRatios()
		return classRatios

	def getFlowStats(self, clauses):
		flowStats = self.dataStoreHandle.getFlowStats(clauses)
		return flowStats

	def getLoadStats(self, clauses):
		loadStats = self.dataStoreHandle.getLoadStats(clauses)
		return loadStats

        def compClassThresholds(self, dataList):
                classThresholds = self.compEngine.compClassThresholds(dataList)
		return classThresholds

	def compClassAvg(self, classThresholds, dataList):
		classAvgs = self.compEngine.compClassAvg(classThresholds, dataList)
		return classAvgs
	
        def compClassRatios(self, thresholdsList, loadList):
                classRates = self.compEngine.compClassRates(thresholdsList, loadList)
		return classRates
        def enforcePolicy(self, thresholdsList, classRates):
		#print "Manager: enforcePolicy(): thresholdsList: %s" %thresholdsList
		#print "Manager: enforcePolicy(): classRates: %s" %classRates
		status = self.commHandle.policyDispatcher(thresholdsList, classRates)
		return status

def signal_handler():
	print "Interrupt Signal Received."
	exit(0)
	''' Exit all the threads here '''	
