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
struct thresholdsStr
{
        int classID;
        int thStart;
        int thEnd;
};

struct header{
        int msgType;
        int rrCount; //Tells about the number of total records in buffer
};

struct classStruct{
	int classID;
	int count;
};

struct thresholdStats{
	struct thresholdsStr *thresholdsList;
	int classCount;
	pthread_mutex_t thresholdsLock;
};

struct flowSizeStats{
        int *flowSize;
	int currCount;
	int maxCount;
	pthread_mutex_t flowSizeListLock;
	
};

struct loadStats{
	struct classStruct *classLoad;
	int classCount;
	pthread_mutex_t loadListLock;
};

struct args{
	struct thresholdStats *g_thresholds;
 	struct flowSizeStats *g_flowSizeList;
        struct loadStats *g_loadStats;

	unsigned int *thresholdsList;
	queue *g_queue;

};

int flowSizeParserSimple(char *data, int *flowSize);
int getFlowClass(int flowSize, struct thresholdStats *g_thresholds);
int thresholdParser(char *data);
int initialize(char *ipAddr, int port, queue *q, unsigned int *thresholds);
void initClassThresholds();
//void *loadStatsSender(void *args);
//void *flowStatsSender(void *args);
void sendLoadStats();
void sendFlowStats();
void addFlowStats(int flowSize, struct flowSizeStats *flowSizeList);
int addLoadStats(int classID, int classCount, struct loadStats *loadList);
int updateLoadList(struct thresholdStats *g_thresholds, struct loadStats *g_loadStats);
int updateThresholdsList(struct thresholdStats *g_thresholds, unsigned int *thresholdsList);
void *qMon(void *);

#endif
