import pickle
import sys

CLAUSE_COUNT = "count"
CLAUSE_PC_COUNT = "pc_count"
CLAUSE_TIME_BEFORE = "time_before"
CLAUSE_TIME_AFTER = "time_after"
CLAUSE_TIME_BETWEEN = "time_between"

class dataStore(object):
	def __init__(self):
		self.flowStats = []
		self.loadStats = []

		self.classThresholds = None
		self.classRatios = None
	
		self.flowStatsCount = 0
		self.loadStatsCount = 0
		self.policyID = 0
		
	
	def addFlowStats(self, flowStats):
		''' <timeStamp|flowSize> '''

		count = len(flowStats)
		for stat in flowStats:
			self.flowStats.append(stat)
		self.flowStatsCount += count
		return count

	def addLoadStats(self, loadStats):
		''' {classID1:load1, classID2:load2 } '''
		classes = loadStats.keys()
		count = len(classes)
	
		for classID in classes:
			stat = {}
			stat[classID] = loadStats[classID]
			self.loadStats.append(stat)
		self.loadStatsCount += count	


	def getFlowStats(self, clauses):
		for (clause, val) in clauses.iteritems():
			if clause == CLAUSE_COUNT:
				condition = int(val)*(-1)
				data = self.flowStats[condition:]
		return data
				
	def getLoadStats(self, clauses):
		data = []
		for (clause, val) in clauses.iteritems():
			if clause == CLAUSE_COUNT:
				condition = int(val)*(-1)
				data = self.loadStats[condition:]
			elif clause == CLAUSE_PC_COUNT:
				classPolicy = self.getClassThresholds()
			
				if classPolicy is None:
					return data
				elif len(classPolicy) == 0:
					return data
				classIDList = classPolicy.keys()
				pcCountReq = int(val)
				
				revLoadStats = list(reversed(self.loadStats))
				
				if len(revLoadStats) == 0:
					return data
				for classID in classIDList:
					pcCountCurr = 0
					for stat in revLoadStats:

						key = stat.keys()[0]

						if key == classID:
							data.append(stat)
							pcCountCurr += 1
								
						if pcCountCurr == pcCountReq:
							break
		return data

	def setClassThresholds(self, classThresholds):
		self.classThresholds = None
		self.classThresholds = classThresholds

	def setClassRatios(self, classRatios):
		self.classRatios = None
		self.classRatios = classRatios

	def getClassThresholds(self):
		return self.classThresholds

	def getClassRatios(self):
		return self.classRatios
