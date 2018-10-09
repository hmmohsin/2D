from __future__ import division

import datetime
INF = 100000000000

class compEngine(object):

	def __init__(self):
		pass
	def compClassThresholds(self, dataList):
		thresholds = []
		thresholdsList = {}
		if len(dataList) < 10:
			print "CompEngine: Not enough flow size information: %s"%thresholds
			thresholdsList[0] = (0,INF)
			return thresholdsList


	        '''Abdullah's code: Starts here'''
		n=0
        	mu=0
        	s=0
        	s2=0
        	cov = 0
	
		dataList.sort()	
		arr = dataList[:]
		

		for i in range(len(arr)):
        	        xn = arr[i]
        	        s+=xn
        	        s2+=(xn*xn)
        	        n+=1
        	        mu = ((n-1.0)*mu + xn)/n
        	        var = (1.0/n)*(s2 + (n*mu*mu) - (mu*2.0*s))

	                cov = var/(mu*mu)
	
	                if cov > 1.0:
	                        thresholds.append(int(arr[i-1]))
	                        n=0
	                        mu=0
	                        s=0
	                        s2=0
		'''Abdullah's Code: Ends here'''

		
		optThresholds = self.backwardprop(thresholds, dataList)
		
		if len(optThresholds) == 0:
			thresholdsList[0] = (0, dataList[-1]) 	
			return thresholdsList

		for itr in range (0, len(optThresholds)+1):
			if itr == 0:
				thresholdsList[itr] = (0, optThresholds[itr])
			elif itr < len(optThresholds):
				thresholdsList[itr] = (optThresholds[itr-1]+1, optThresholds[itr])
			else:
				thresholdsList[itr] = (optThresholds[itr-1]+1, dataList[-1])

		return thresholdsList

	
	def compClassAvg(self, classThresholdsList, dataList):
	
		classIDs = classThresholdsList.keys()
		classCount = len(classIDs)

		classAvgsList = []	
		classAvgs = {}
		
		count =0
		
		for flowSize in dataList:
			for classID in classIDs:
				if flowSize < classThresholdsList[classID][1]:
					if classID not in classAvgs.keys():
						classAvgs[classID] = 1
					else:
						classAvgs[classID] += 1
						break
			count+=1
		classAvgsList.append(classAvgs)	
		print "compEngine: count=%d ClassAvgs: %s"%(count, classAvgs)
		return classAvgsList

	def compClassRates(self, classThresholdsList, classLoadStats):

		classRates = {}
		classLoad = {}
		totalCount = 0

		lClasses = getLkeysSet(classLoadStats)
	
		tClasses = classThresholdsList.keys()
		
		if len(tClasses) != len(lClasses):
			print "CompEngine: Class count mismatch. Switching to default rates for new thresholds."
			for classID in tClasses:
				classRates[classID] = round(1/len(tClasses),4)
			return classRates
			
		for classID in tClasses:
			if classID not in lClasses:
				print "CompEngine: ClassID %d mismatch. Rate Computation Failed." %classID
				return classRates


		for pClassLoadStat in classLoadStats:
			for (classID, load) in pClassLoadStat.iteritems():
				if classID not in classLoad.keys():
					classLoad[classID] = load
				else:	
					classLoad[classID] += load
		
		for (classID, load) in classLoad.iteritems():
			totalCount += load
		
		if totalCount == 0:
			return []

		for (classID, load) in classLoad.iteritems():
			classRates[classID] = round(load/totalCount, 4)
			if classRates[classID] == 0:
				classRates[classID] = 0.00001

		return classRates		

	def covcalc(self, arr):
        	n=0
        	mu=0
        	s=0
        	s2=0
        	cov = 0

        	if(len(arr) == 0):
        	        return 100
	
        	for i in range(len(arr)):
                	xn = arr[i]
                	s+=xn
                	s2+=(xn*xn)
                	n+=1
                	mu = ((n-1.0)*mu + xn)/n
                	var = (1.0/n)*(s2 + (n*mu*mu) - (mu*2.0*s))

        	cov = var/(mu*mu)

        	return cov


	def backwardprop(self, thresholds, data):
	        Is = [0] + thresholds + [int(max(data))]
	        K = len(Is)
	        cnt=0
	        for T in range(K-2,0,-1):
	
	                mincov = [100,-1,-1,-1]
	                i=Is[T-1]
	                j=Is[T+1]
	
	                section = filter(lambda x: x>=float(i) and x<float(j), data)
	
	                for t in range(i,j,res(max(section) - min(section))):
	                        # print t
	                        c1 = self.covcalc(filter(lambda x: x>=float(i) and x<float(t), section))
	                        c2 = self.covcalc(filter(lambda x: x>=float(t) and x<float(j), section))
	
	                        if(c1+c2 < mincov[0] and c1 < 1.0 and c2 < 1.0):
	                                mincov[0] = c1 + c2
	                                mincov[1] = t
	                                mincov[2] = c1
	                                mincov[3] = c2
	
	                if mincov[1]!=-1:
	                        thresholds[T-1] = mincov[1]
	
	                Is = [0] + thresholds + [int(max(data))]
	                cnt+=1
		return thresholds


def res(num):
        if(num<300):
                return 1
        return int(num/300)

def avg(arr):
	if len(arr) == 0:
		return -1
	return sum(arr)/len(arr)
	
'''Abdullah's code: Ends here'''

def getLkeysSet(classLoadStats):
	keysList = []

	for classLoad in classLoadStats:
		keys = classLoad.keys()
		
		for key in keys:
			if key not in keysList:
				keysList.append(key)
	return keysList





