import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from cycler import cycler
import numpy as np
import sys


def plot(filename):
	fileHandle = open(filename,"r")
	count = 0
	numPlots = 0
	legend = []

	fig, ax = plt.subplots()
	x_label = "FCT"
	y_label = "CDF"
	title = "2D-Controller Performance" 

	fileList = []
	schemesNames = []
	title = "2D-Controller Analysis"
	for line in fileHandle:
		fttList = []
		if line.startswith("#"):
			continue
		fileName, schemeName = line.split(' ')
		fileList.append(fileName)
		schemesNames.append(schemeName)

		dfh = open(fileName,"r")
		data = dfh.readlines()
		dfh.close()
		filteredData = filter(lambda x: "start" not in x, data)
		fttList.append(sorted(map(lambda x: float(x.split(' ')[1])/1000000.0,filteredData)))
		count = len(fttList)
		
		cdf = []
		t = 0
        	for i in range(count):
        	        t += 1.0/count
        	        cdf.append(t)
	
		ax.plot(fttList,cdf, label=schemeName)
	
	fileHandle.close()
	ax.set(xlabel=x_label, ylabel = y_label, title=title)
        #ax.legend(loc='upper left', shadow=True)
        ax.grid(color='black', linestyle='--', linewidth=1)

        #ax.set_xlim(xlim_min,xlim_max)
        #ax.set_ylim(ylim_min,ylim_max)

	print "Saving Fig"
        plt.savefig(title, dpi=200)
	return

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print "Usage: python plot_line_multi.py <filename>"
		exit(0)
	filename = sys.argv[1]
	plot(filename)
