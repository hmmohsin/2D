#ifndef SIM_H_INCLUDED
#define SIM_H_INCLUDED

#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>

#include "tsQueue.h"

# define TYPE_FLOWSTATS 11
# define TYPE_LOADSTATS 12
# define TYPE_CLASSTHRESHOLDS 3

# define FLOWSIZELISTLEN 1000
# define MAXDATABUFFLEN 1000
# define HDRSIZE 8




/* This structure is used to communicate stats
to agent. msgType can be either of the two types
specified above. Whereas, rrCount contains the  
count of the records in the message.*/

struct header{
        int msgType;
        int rrCount; 
};




/* This data structure is used to keep track
of the queue occupency of a class in an interval.
Currently the metric is per class count of flow
arrival in an interval*/

struct classStruct{
	int classID;
	int count;
};




/* This structure act as a loadstore, keeping
track of per class load stats*/

struct loadStats{
	int classCount;
	struct classStruct *classLoad;
	pthread_mutex_t loadListLock;
};





/* This structure keeps track of the threshold 
boundaries of a class */

struct thresholdsStr
{
        int classID;
        int thStart;
        int thEnd;
};



/*Just like loadStats, this structure track of 
per class threshold boundaries */

struct thresholdStats{
	struct thresholdsStr *thresholdsList;
	int classCount;
	pthread_mutex_t thresholdsLock;
};



/* This data structure is used to batch the
flow size information, received from the
application, before passing to the agent*/

struct flowSizeStats{
        int *flowSize;
	int currCount;
	int maxCount;
	pthread_mutex_t flowSizeListLock;
	
};


struct globalDataStruct{
	struct thresholdStats *g_thresholds;
        struct loadStats *g_loadStats;
 	
	
	/* Stores the formatted version of
	flow size information received from app*/
	
	struct flowSizeStats *g_flowSizeList;

	unsigned int *thresholdsList;
	queue *g_queue;

};

void initClassThresholds();
int flowSizeParserSimple(char *data, int *flowSize);
int getFlowClass(int flowSize);
int thresholdParser(char *hdr_buf, char *data);
int initialize(char *ipAddr, int port, queue *q, unsigned int *thresholds);
void sendLoadStats();
void sendFlowStats();
void addFlowStats(int flowSize);
int addLoadStats(int classID, int classCount);
int updateLoadList();
int updateThresholdsList();
void *qMon(void *);

#endif
