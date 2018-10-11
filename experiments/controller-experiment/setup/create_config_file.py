import os, sys

traffic = "VL2_CDF.txt"
interface = "lo"
serverIP = "127.0.0.1"
serverPort = "5001"
seqIP = "127.0.0.1"
seqPort = "6001"

def readargs(args):
	global traffic
	global interface
	global serverIP
	global serverPort

	i=0

	while(i<len(args)):
		if(args[i]=='-t'):
			traffic = args[i+1]
		elif(args[i]=='-i'):
			interface = args[i+1]
		elif(args[i]=='-sp'):
			serverPort = args[i+1]
		elif(args[i]=='-sip'):
			serverIP = args[i+1]
		i+=2


os.system("cat /var/emulab/boot/ifmap > ifmapinfo.dat")
fd = open("ifmapinfo.dat",'r')
ft = fd.readlines()
fd.close()
os.system("rm ifmapinfo.dat")

interface = ft[0].split(' ')[0]
serverIP = ft[0].split(' ')[1]
seqIP = serverIP

link_rate = 1000

#toythresholds=[50001,10000001]
thresholds=[3400,16176,545316,5159030,129372452]
#dctcpthresholds=[113154,5671937]
#thresholds=[528,2711]

tos = [4,32,40,56,72,128]
num_classes = len(ratio)

print "Traffic: %s" % traffic
print "Server IP %s" % serverIP
print "Server port: %s" % serverPort

# creating config files
print "Creating config file..."
fd = open("/tmp/2D/conf/client_config2.txt",'w')
print >> fd , "server %s %s" % (serverIP,serverPort)
print >> fd , "sequencer %s %s" % (seqIP,seqPort)
print >> fd , "req_size_dist conf/%s" % traffic
print >> fd , "rate %dMbps 100" % link_rate
for t in thresholds:
	print >> fd , "threshold %d" % t

fd.close()



# 	if [[ ${scheme} -eq 1 ]]; then
# 		mv *.txt fifo/
# 	fi

# 	if [[ ${scheme} -eq 2 ]]; then
# 		mv *.txt fq/
# 	fi

# 	if [[ ${scheme} -eq 3 ]]; then
# 		mv *.txt 2d/
# 	fi

# 	rm *.txt

# done;
