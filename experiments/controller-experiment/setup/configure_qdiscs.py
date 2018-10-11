import os, sys

traffic = "DCTCP_CDF.txt"
interface = "lo"
serverIP = "127.0.0.1"
serverPort = "5001"
seqIP = "127.0.0.1"
seqPort = "6001"

def readargs(args):
	global link_rate
	global thresholds
	global ratios

	i=0

	while(i<len(args)):
		if(args[i]=='-l'):
			link_rate = int(args[i+1])
		elif(args[i]=='-t'):
			thresholds=args[i+1]
			thresholds = map(lambda x: int(x),thresholds.split(','))
		elif(args[i]=='-r'):
			ratios=args[i+1]
			ratios = map(lambda x: float(x),ratios.split(','))
		i+=2

os.system("cat /var/emulab/boot/ifmap > ifmapinfo.dat")
fd = open("ifmapinfo.dat",'r')
ft = fd.readlines()
fd.close()
os.system("rm ifmapinfo.dat")

interface = ft[0].split(' ')[0]
serverIP = ft[0].split(' ')[1]
seqIP = serverIP

link_rate=-1
thresholds=[]
ratios=[]

readargs(sys.argv[1:])

print "PRINTING STATS"
print "link rate: %d Mbps" % link_rate
print "thresholds: %s" % str(thresholds)
print "ratios: %s" % str(ratios)


#toythresholds=[50001,10000001]
# thresholds=[3400,16176,545316,5159030,129372452]
# ratio=[0.71,0.097,0.1,0.045,0.028,0.020]

#dctcpthresholds=[113154,5671937]
#thresholds=[528,2711]

# ratio=[0.71,0.097,0.1,0.045,0.028,0.020]

#dctcpratio=[0.544,0.353,0.103]
#ratio=[0.643,0.061,0.296]

#print sum(ratio)
tos = [4,32,40,56,72,128,152,184,192,224]

# tos = [4,100,200,300,400,500,600,700,800,900]
num_classes = len(ratios)

# assert len(sys.argv) == 9

sratio = int(round(sum(ratios)))
assert sratio == 1
assert len(ratios) == len(thresholds) + 1

print "Interface: %s" % interface
print "Traffic: %s" % traffic
print "Server IP %s" % serverIP
print "Server port: %s" % serverPort

# setting up filters
print "Setting up qdiscs..."
os.system("tc qdisc delete dev %s root" % interface)
os.system("tc qdisc add dev %s root handle 1: htb default 1%d" % (interface,num_classes-1))
os.system("tc class add dev %s parent 1: classid 1:1 htb rate %dmbit ceil %dmbit" % (interface,link_rate,link_rate))

for r in range(len(ratios)):
	os.system("tc class add dev %s parent 1:1 classid 1:1%d htb rate %dmbit ceil %dmbit" % \
		(interface,r,int(ratios[r]*link_rate), link_rate))
	os.system("tc filter add dev %s protocol ip parent 1:0 prio 1 u32 match ip tos %d 0xff flowid 1:1%d" % \
		(interface,tos[r],r))
	print "Tos:%d Rate:%d" % (tos[r],int(ratios[r]*link_rate))
	# os.system("tc qdisc add dev %s parent 1:1%d handle 1%d: sfq perturb 10" % (interface,r,r))


# creating config files
print "Creating config file..."
fd = open('/tmp/2D/conf/client_config2.txt','w')
print >> fd , "server %s %s" % (serverIP,serverPort)
print >> fd , "sequencer %s %s" % (seqIP,seqPort)
print >> fd , "req_size_dist %s" % traffic
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
