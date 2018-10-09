import os
import sys
import helper
import compEngine
import commManager
import dataStore
import manager
import time 
import threading
import logging

os.system("rm -rf classRatios.log")
logging.basicConfig(filename="classRatios.log", level=logging.INFO)
log = logging.getLogger("ex")

def getWMA(newClassRatios, oldClassRatios):
	classRatios = {}
	alpha = 0.1

	if len(newClassRatios) == len(oldClassRatios):

		for (classID, nRatio) in newClassRatios.iteritems():
			oRatio = oldClassRatios[classID]
			ratio = round((nRatio*alpha + oRatio*(1-alpha)),4)
			classRatios[classID] = ratio
		return classRatios
	else:
		return newClassRatios

def getRatios(classRatios):
	ratioList = []
	for (classID, ratio) in classRatios.iteritems():
		ratioList.append(ratio)
	data = " ".join(map(str,ratioList))
	return data

def formatClassThresh(classThresholdsList):
	thList = []
	for (key,val) in classThresholdsList.iteritems():
		thList.append(val[1])
	output = " ".join(map(str,thList))
	return output

def calClassThresh(managerCtrl, timer):
	count = 10
	maxCount = 1000
	while True:
		clause = {'count':count}
		flowSizeList = []
		flowSizeData = managerCtrl.getFlowStats(clause)
		if len(flowSizeData) >= count:
			if count < maxCount:
				count = count*2
			else:
				count = maxCount
		for flowSizeTuple in flowSizeData:
			flowSize = int(flowSizeTuple.split('|')[1]) 
			flowSizeList.append(flowSize)

		classThresholdsList = managerCtrl.compClassThresholds(flowSizeList)
		managerCtrl.setClassThresholds(classThresholdsList)
		output = formatClassThresh(classThresholdsList)
		log.info(output)
		time.sleep(timer)	

if __name__=="__main__":
	
	managerCtrl = manager.manager()
	managerCtrl.initialize('10.1.1.28', 50010)

	classThresholdsList = [113154, 5671937]
	classRatiosList = [0.544,0.353,0.103]

	#classThresholdsList = [0]
	#classRatiosList = [1]

	managerCtrl.initClassThresholds(classThresholdsList)
	managerCtrl.initClassRatios(classRatiosList)

	threshCalc = threading.Thread(name='threshCalc', target=calClassThresh, args=(managerCtrl,10,))
	threshCalc.setDaemon(True)
	threshCalc.start()
	
	'''Fetches load stats from last 5 events of every class'''
	load_clause = {'pc_count':5}
	while True:
	
		loadStats = managerCtrl.getLoadStats(load_clause)
		classThresholds = managerCtrl.getClassThresholds()

		if len(loadStats) != 0:
			classRatios = managerCtrl.compClassRatios(classThresholds, loadStats)
			
			if classRatios is "":
				'''If failed to compute new class ratios, use last computed'''
				classRatios = managerCtrl.getClassRatios()
				if classRatios is "":
					continue
				policy = managerCtrl.enforcePolicy(classThresholds, classRatios)
			else:
					pClassRatios = managerCtrl.getClassRatios()
					fClassRatios = getWMA(classRatios, pClassRatios)
					managerCtrl.setClassRatios(fClassRatios)
						

					print "---------------------------------------------"
					print "Last Ratios: %s" %pClassRatios
					print "New Ratios: %s" %fClassRatios
					print "---------------------------------------------"
					
					''' Sends the policy to the connected agents. Does not guarantee
					   Enforcement as there is no auto mechanism to determine whether
					   the agent was able to successfully enforce these limits or not'''
	
					policy = managerCtrl.enforcePolicy(classThresholds, fClassRatios)
		time.sleep(2)
