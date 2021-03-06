import os, sys

def makecdf(length):
	t = 0
	cdf=[]

	for i in range(length):
		t += 1.0/length
		cdf.append(t)
	return cdf


#files = ["fifo_fct","ps_fct","2d_fct","aalo_fct"]
files = ["CACHE_Offline.txt","CACHE_Online.txt",]
cdfpair=[]
N=0
i=0
for file in files:

		# tfile = file.split('.')[0]+str(run)+'.txt'
	tf = open(file,'r')
	ft = tf.readlines()
	tf.close()
		# ft = filter(lambda x: not cond(x), ft)
	ft = filter(lambda x: "start" not in x, ft)
	N = len(ft)
	cdfpair.append(sorted(map(lambda x: float(x.split(' ')[1])/1000000.0,ft)))

	i+=1

cdfpair.append(makecdf(N))
print len(cdfpair)

fd = open("output.txt",'w')
for i in range(N):
	#print >> fd, "%0.5f %0.5f %0.5f %0.5f %0.5f" % (cdfpair[0][i],cdfpair[1][i],cdfpair[2][i],cdfpair[3][i],cdfpair[4][i])
	print >> fd, "%0.5f %0.5f %0.5f" % (cdfpair[0][i], cdfpair[1][i], cdfpair[2][i])
fd.close()

os.system("gnuplot cdfplot.plt")
