#include <sys/socket.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <pthread.h>

# include "sim.h"

static int sockfd;
static struct args *th_args; 

int initialize(char *ipAddr, int port, queue *q, unsigned int *thresholdsList){

    	struct header *hdr = malloc(sizeof(struct header));
	th_args = malloc(sizeof(struct args));
		
	th_args->g_flowSizeList = malloc(sizeof(struct flowSizeStats));

	th_args->g_flowSizeList->flowSize = malloc(sizeof(int)*200);
	th_args->g_flowSizeList->currCount = 0;
	th_args->g_flowSizeList->maxCount = 10;
	pthread_mutex_init(&(th_args->g_flowSizeList->flowSizeListLock), NULL);
	
	th_args->g_loadStats = malloc(sizeof(struct loadStats));
	th_args->g_loadStats->classLoad = malloc(sizeof(struct classStruct)*10);
	th_args->g_loadStats->classCount = 10;
	pthread_mutex_init(&(th_args->g_loadStats->loadListLock), NULL);
	
	//th_args->g_thresholds = thresholdStatsList;
	
	th_args->g_thresholds = malloc(sizeof(struct thresholdStats));
	th_args->g_thresholds->thresholdsList = malloc(sizeof(struct thresholdsStr)*10);
	th_args->g_thresholds->classCount = 1;
	pthread_mutex_init(&(th_args->g_thresholds->thresholdsLock), NULL);
	

	th_args->g_queue = q;
	th_args->thresholdsList = thresholdsList;

	initClassThresholds();

	int n;
	struct sockaddr_in serv_addr;    
	
	char hdr_buf[HDRSIZE];
	char *data_buf = malloc(MAXDATABUFFLEN);
	char *tmp_buf = malloc(MAXDATABUFFLEN);

	pthread_t thread_id;

	if((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0)
	{
		printf("\n Error : Could not create socket \n");
		return 1;
	}	
	memset(&serv_addr, '0', sizeof(serv_addr));

	serv_addr.sin_family = AF_INET;
	serv_addr.sin_port = htons(port);
	serv_addr.sin_addr.s_addr = inet_addr(ipAddr);

	if( connect(sockfd, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0)
	{
		printf("\n Error : Connect Failed %s\n", strerror(errno));
		return -1;
	}

    	pthread_create(&thread_id, NULL, qMon, (void*)th_args);

	while(1){
		n = read(sockfd, hdr_buf, HDRSIZE);
		memcpy(hdr, hdr_buf, HDRSIZE);
		
		n = read(sockfd, data_buf, MAXDATABUFFLEN);
		memcpy(tmp_buf, data_buf, n);
		
		n = thresholdParser(tmp_buf);
		updateThresholdsList(th_args->g_thresholds, th_args->thresholdsList);
		updateLoadList(th_args->g_thresholds, th_args->g_loadStats);
		
		memset(&hdr_buf, '0', HDRSIZE);
		memset(data_buf, '0', MAXDATABUFFLEN);
		memset(tmp_buf, '0', MAXDATABUFFLEN);
	}
    return 0;

}

void initClassThresholds(){
	
	th_args->g_thresholds->thresholdsList[0].classID = 0;
	th_args->g_thresholds->thresholdsList[0].thStart = 0;
	th_args->g_thresholds->thresholdsList[0].thEnd = 113154;

	th_args->g_thresholds->thresholdsList[1].classID = 1;
	th_args->g_thresholds->thresholdsList[1].thStart = 113155;
	th_args->g_thresholds->thresholdsList[1].thEnd = 5671937;

	th_args->g_thresholds->thresholdsList[2].classID = 2;
	th_args->g_thresholds->thresholdsList[2].thStart = 5671938;
	th_args->g_thresholds->thresholdsList[2].thEnd = 1000000000;

}

void *qMon(void *arguments){
	struct args *th_args = (struct args *) arguments;
	int flowSize = 0, flowClass, classCount;

	classCount = th_args->g_thresholds->classCount;
	while (1){
		tsDequeue(th_args->g_queue, &flowSize);
		
		classCount = th_args->g_thresholds->classCount;
		flowClass = getFlowClass(flowSize, th_args->g_thresholds);

		addLoadStats(flowClass, classCount, th_args->g_loadStats);
		addFlowStats(flowSize, th_args->g_flowSizeList);

	}
}

int getFlowClass(int flowSize, struct thresholdStats *g_thresholds){
	int idx = 0;
	int classCount = g_thresholds->classCount;
	if (classCount == 1)
		return 0;

	for (idx=0; idx<classCount; idx++){
		if (flowSize <= g_thresholds->thresholdsList[idx].thEnd)
			return g_thresholds->thresholdsList[idx].classID;
	}

	return g_thresholds->thresholdsList[classCount].classID;
	return -1;
}
int updateThresholdsList(struct thresholdStats *g_thresholds, unsigned int *thresholdsList)
{
	int i=0, classCount = g_thresholds->classCount;
		

	for (i=0; i<classCount; i++){
		//if (i == 3)
		//	break;	
		thresholdsList[i] = g_thresholds->thresholdsList[i].thEnd;
	}
	printf ("THreshold List: %d %d %d %d %d %d\n", 
				thresholdsList[0], 
				thresholdsList[1], 
				thresholdsList[2], 
				thresholdsList[3], 
				thresholdsList[4], 
				thresholdsList[5]);
	return i;
}
int updateLoadList(struct thresholdStats *g_thresholds, struct loadStats *g_loadStats)
{
	int classID = 0, i=0;
	int classCount = g_thresholds->classCount;
	pthread_mutex_lock(&(g_loadStats->loadListLock));
	for(i=0; i<classCount; i++){
		
		classID = g_thresholds->thresholdsList[i].classID;
	
		g_loadStats->classLoad[i].classID = classID;
		g_loadStats->classLoad[i].count = 0;
		//printf("Updating Thresholds: Class=%d:%d-%d\n", classID, start, end);	
	}
	pthread_mutex_unlock(&(g_loadStats->loadListLock));
	return classCount;
}

int addLoadStats(int classID, int classCount, struct loadStats *g_loadStats){
	int index = 0;

	if (classCount > 0){
		pthread_mutex_lock(&(g_loadStats->loadListLock));
		for (index=0; index<classCount; index++){
			if (g_loadStats->classLoad[index].classID == classID){
				g_loadStats->classLoad[index].count++;
				pthread_mutex_unlock(&(g_loadStats->loadListLock));
				return 1;
			}

		}
		pthread_mutex_unlock(&(g_loadStats->loadListLock));
	}
	return -1;
}

void addFlowStats(int flowSize, struct flowSizeStats *g_flowSizeList){

	int index = 0;
	int *flowSizePtr = g_flowSizeList->flowSize;

	pthread_mutex_lock(&(g_flowSizeList->flowSizeListLock));
	index = g_flowSizeList->currCount;
	
	if (index >= g_flowSizeList->maxCount){
        	flowSizePtr = realloc(g_flowSizeList->flowSize, 2*index*(sizeof(int)));
		
		g_flowSizeList->flowSize = flowSizePtr;
		g_flowSizeList->maxCount = 2*index;
			
	}
	g_flowSizeList->flowSize[index] = flowSize;
	g_flowSizeList->currCount += 1;
	pthread_mutex_unlock(&(g_flowSizeList->flowSizeListLock));	
	
}
int thresholdParser(char *data){

    	int id = 0;
	char *token = strtok(data, ",");
    	while (token != NULL)
    	{
		th_args->g_thresholds->thresholdsList[id].classID = atoi(token);
        	token = strtok(NULL, ",");
	
		th_args->g_thresholds->thresholdsList[id].thStart = atoi(token);
        	token = strtok(NULL, ",");

		th_args->g_thresholds->thresholdsList[id++].thEnd = atoi(token);
        	token = strtok(NULL, ",");
    	}
	th_args->g_thresholds->classCount = id;
    	return id;
}


void sendLoadStats(){

	char *data = malloc(MAXDATABUFFLEN);
	char statsStr[1000];
	char *hdr = malloc(HDRSIZE);

	bzero(data, MAXDATABUFFLEN);
	bzero(statsStr, 1000);

	int i =0, bytesSent, classCount=0, classID = 0, flowCount = 0, msgSize=0;

	classCount = th_args->g_thresholds->classCount;
	if (classCount > 0){
		sprintf(hdr,"%d|%d|",TYPE_LOADSTATS, classCount);
		strcpy(data, hdr);
	
		while(1){
			classID = th_args->g_loadStats->classLoad[i].classID;
			flowCount = th_args->g_loadStats->classLoad[i].count;
			sprintf(statsStr,"%d:%d", classID, flowCount);
			if (i < classCount){
				strcat(data, statsStr); 
				strcat(data,",");
			}
			else{
				strcat(data, "\n\n\n");
				msgSize = strlen(data)+3;
				break;
			}
			th_args->g_loadStats->classLoad[i].count = 0;
			i++;
		}
		bytesSent = write(sockfd, data, msgSize);
		if (bytesSent <= 0)
			printf("Error: Failed to send flow stats\n");

	}
}

void sendFlowStats(){

	int i =0, bytesSent, flowSize, flowCount = 0, msgSize=0;
	char *data = malloc(MAXDATABUFFLEN);
	char statsStr[1000];
	char *hdr = malloc(HDRSIZE);

	bzero(data, MAXDATABUFFLEN);
	bzero(statsStr, 1000);

	flowCount = th_args->g_flowSizeList->currCount;
	sprintf(hdr,"%d|%d|",TYPE_FLOWSTATS, flowCount);
	strcpy(data, hdr);

	while(1){
		flowSize = th_args->g_flowSizeList->flowSize[i];
		sprintf(statsStr, "%d", flowSize);
		
		if (i<flowCount){
			strcat(data, statsStr);
			strcat(data, ",");
		}
		else{
			strcat(data,"\n\n\n");
			msgSize = strlen(data)+3;
			break;
		}
		i++;
	}
	th_args->g_flowSizeList->currCount = 0;
        bytesSent = write(sockfd, data, msgSize);
	if (bytesSent <= 0)
		printf("Error: Failed to send flow stats\n");
}


int flowSizeParser(char *data, int **flowSizeList, int *flowSizeListLen){
	
	int flowSize;
	char *token = strtok(data, ",");

	int *flowSizeListPtr = *flowSizeList;
	int index = 0;

	while(token != NULL){
		flowSize = atoi(token);
		flowSizeListPtr[index++] = flowSize;
		
		if (index > *flowSizeListLen){
			flowSizeListPtr = realloc(*flowSizeList, ((*flowSizeListLen*sizeof(int))+(FLOWSIZELISTLEN*sizeof(int))));
			*flowSizeListLen += FLOWSIZELISTLEN;
		}
        	token = strtok(NULL, ",");
	}
	*flowSizeListLen = index;
	*flowSizeList = flowSizeListPtr;
}

