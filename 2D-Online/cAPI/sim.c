#include <sys/socket.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <errno.h>
#include <pthread.h>

# include "sim.h"

static int sockfd;
static int g_maxClassCount;
static struct globalDataStruct *data; 

int initialize(char *ipAddr, int port, queue *q, unsigned int *thresholdsList){

    	struct header *hdr = malloc(sizeof(struct header));
	data = malloc(sizeof(struct globalDataStruct));

	g_maxClassCount = 10;

	/* check size expansion */		
	data->g_flowSizeList = malloc(sizeof(struct flowSizeStats));


	/*initialize the list to store flow size information*/
	data->g_flowSizeList->flowSize = malloc(sizeof(int)*100);
	data->g_flowSizeList->currCount = 0;
	data->g_flowSizeList->maxCount = 100;
	pthread_mutex_init(&(data->g_flowSizeList->flowSizeListLock), NULL);


	/* check if the class count increase leads to segfault*/	
	data->g_loadStats = malloc(sizeof(struct loadStats));
	data->g_loadStats->classLoad = malloc(sizeof(struct classStruct)*g_maxClassCount);
	data->g_loadStats->classCount = g_maxClassCount;
	pthread_mutex_init(&(data->g_loadStats->loadListLock), NULL);
	

	/* check if the class count increase leads to segfault*/	
	data->g_thresholds = malloc(sizeof(struct thresholdStats));
	data->g_thresholds->thresholdsList = malloc(sizeof(struct thresholdsStr)*g_maxClassCount);
	data->g_thresholds->classCount = g_maxClassCount;
	pthread_mutex_init(&(data->g_thresholds->thresholdsLock), NULL);
	
	data->g_queue = q;
	data->thresholdsList = thresholdsList;

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

    	pthread_create(&thread_id, NULL, qMon, (void*)data);

	while(1){
		n = read(sockfd, hdr_buf, HDRSIZE);
		memcpy(hdr, hdr_buf, HDRSIZE);
		
		n = read(sockfd, data_buf, MAXDATABUFFLEN);
		memcpy(tmp_buf, data_buf, n);
		
		n = thresholdParser(hdr_buf, tmp_buf);
		updateThresholdsList();
		updateLoadList(data->g_thresholds, data->g_loadStats);
		
		memset(&hdr_buf, '0', HDRSIZE);
		memset(data_buf, '0', MAXDATABUFFLEN);
		memset(tmp_buf, '0', MAXDATABUFFLEN);
	}
    return 0;

}

void initClassThresholds(){
	
	data->g_thresholds->thresholdsList[0].classID = 0;
	data->g_thresholds->thresholdsList[0].thStart = 0;
	data->g_thresholds->thresholdsList[0].thEnd = 113154;

	data->g_thresholds->thresholdsList[1].classID = 1;
	data->g_thresholds->thresholdsList[1].thStart = 113155;
	data->g_thresholds->thresholdsList[1].thEnd = 5671937;

	data->g_thresholds->thresholdsList[2].classID = 2;
	data->g_thresholds->thresholdsList[2].thStart = 5671938;
	data->g_thresholds->thresholdsList[2].thEnd = 1000000000;

}

void *qMon(void *arguments){
	struct globalDataStruct *data = (struct globalDataStruct *) arguments;
	int flowSize = 0, flowClass, classCount;

	classCount = data->g_thresholds->classCount;
	while (1){
		tsDequeue(data->g_queue, &flowSize);
		
		classCount = data->g_thresholds->classCount;
		flowClass = getFlowClass(flowSize);

		addLoadStats(flowClass, classCount);
		addFlowStats(flowSize);
	}
}

int getFlowClass(int flowSize){
	int idx = 0, classID, thEnd;
	int classCount = data->g_thresholds->classCount;

	if (classCount == 1)
		return 0;

	for (idx=0; idx<classCount; idx++){
		classID = data->g_thresholds->thresholdsList[idx].classID;
		thEnd = data->g_thresholds->thresholdsList[idx].thEnd;
		if (flowSize <= thEnd)
			return classID;
	}

	return -1;
}

/*Need a database handler here*/

/*Updates the container list of application, passed to API during init*/
int updateThresholdsList()
{
	int i=0;
	int classCount = data->g_thresholds->classCount;
		

	for (i=0; i<classCount; i++){
		/*If the list memory has not been handled properly
		by the application, this may lead to segfault.*/

		data->thresholdsList[i] = data->g_thresholds->thresholdsList[i].thEnd;
	}
	return i;
}
int updateLoadList()
{
	int classID = 0, i=0;
	int thClassCount = data->g_thresholds->classCount;
	int currClassCount = data->g_loadStats->classCount;

	pthread_mutex_lock(&(data->g_loadStats->loadListLock));
	
	if (currClassCount < g_maxClassCount){

		data->g_loadStats->classCount = g_maxClassCount;
		data->g_loadStats->classLoad = malloc(sizeof(struct classStruct)*g_maxClassCount);
	}

	for(i=0; i<thClassCount; i++){
		
		classID = data->g_thresholds->thresholdsList[i].classID;
		
		data->g_loadStats->classLoad[i].classID = classID;
		data->g_loadStats->classLoad[i].count = 0;
	}
	pthread_mutex_unlock(&(data->g_loadStats->loadListLock));
	
	return currClassCount;
}

int addLoadStats(int classID, int thClassCount){
	int index = 0;
	int currClassCount = data->g_loadStats->classCount;
	
	if (thClassCount == currClassCount){
		pthread_mutex_lock(&(data->g_loadStats->loadListLock));
		for (index=0; index<currClassCount; index++){
			if (data->g_loadStats->classLoad[index].classID == classID){
				data->g_loadStats->classLoad[index].count++;
				pthread_mutex_unlock(&(data->g_loadStats->loadListLock));
				return 1;
			}

		}
		pthread_mutex_unlock(&(data->g_loadStats->loadListLock));
	}
	return -1;
}

void addFlowStats(int flowSize){

	int i=0, index = 0, newSize;
	int *flowSizePtr = NULL;

	pthread_mutex_lock(&(data->g_flowSizeList->flowSizeListLock));
	index = data->g_flowSizeList->currCount;

	//HM_Debug: Reallocation system is crashing after few iterations.
	if (index >= data->g_flowSizeList->maxCount){
		newSize = 2*index*sizeof(int);
        	flowSizePtr = realloc(data->g_flowSizeList->flowSize, newSize);
		
		data->g_flowSizeList->flowSize = flowSizePtr;
		data->g_flowSizeList->maxCount = 2*index;
		
	}
	data->g_flowSizeList->flowSize[index] = flowSize;
	data->g_flowSizeList->currCount += 1;
	pthread_mutex_unlock(&(data->g_flowSizeList->flowSizeListLock));	
	
}
int thresholdParser(char *hdr_buf, char *data_buf){

    	int id = 0, newSize, currCount;
	struct header *hdr = malloc(HDRSIZE);
	char *token = strtok(data_buf, ",");
	    
	memcpy(hdr, hdr_buf, HDRSIZE);
	currCount = data->g_thresholds->classCount;

	if (hdr->rrCount > currCount){

		g_maxClassCount = hdr->rrCount;

		newSize = sizeof(struct thresholdsStr)*g_maxClassCount;
		data->g_thresholds->thresholdsList = malloc(newSize);
		data->g_thresholds->classCount = g_maxClassCount;
	}
	
	while (token != NULL)
    	{
		data->g_thresholds->thresholdsList[id].classID = atoi(token);
        	token = strtok(NULL, ",");
	
		data->g_thresholds->thresholdsList[id].thStart = atoi(token);
        	token = strtok(NULL, ",");

		data->g_thresholds->thresholdsList[id++].thEnd = atoi(token);
        	token = strtok(NULL, ",");
    	}
	data->g_thresholds->classCount = id;
    	return id;
}


void sendLoadStats(){

	char *data_buf = malloc(MAXDATABUFFLEN);
	char statsStr[1000];
	char *hdr_buf = malloc(HDRSIZE);

	bzero(data_buf, MAXDATABUFFLEN);
	bzero(statsStr, 1000);

	int i =0, bytesSent=0, classCount=0, classID = 0, flowCount = 0, msgSize=0;

	classCount = data->g_thresholds->classCount;
	if (classCount > 0){
		sprintf(hdr_buf,"%d|%d|",TYPE_LOADSTATS, classCount);
		strcpy(data_buf, hdr_buf);
	
		while(1){
			classID = data->g_loadStats->classLoad[i].classID;
			flowCount = data->g_loadStats->classLoad[i].count;
			sprintf(statsStr,"%d:%d", classID, flowCount);
			if (i < classCount){
				strcat(data_buf, statsStr); 
				strcat(data_buf,",");
			}
			else{
				strcat(data_buf, "\n\n\n");
				msgSize = strlen(data_buf)+3;
				break;
			}
			data->g_loadStats->classLoad[i].count = 0;
			i++;
		}
		bytesSent = write(sockfd, data_buf, msgSize);
	}
}

void sendFlowStats(){

	int i =0, bytesSent=0, flowSize, flowCount = 0, msgSize=0;
	char *data_buf = malloc(MAXDATABUFFLEN);
	char *hdr_buf = malloc(HDRSIZE);
	char statsStr[1000];

	bzero(data_buf, MAXDATABUFFLEN);
	bzero(statsStr, 1000);

	pthread_mutex_lock(&(data->g_flowSizeList->flowSizeListLock));
	flowCount = data->g_flowSizeList->currCount;
	sprintf(hdr_buf,"%d|%d|",TYPE_FLOWSTATS, flowCount);
	strcpy(data_buf, hdr_buf);

	while(1){
		//printf("Accessing %dth element\n",i);
		flowSize = data->g_flowSizeList->flowSize[i];
		sprintf(statsStr, "%d", flowSize);
		
		if (i<flowCount){
			strcat(data_buf, statsStr);
			strcat(data_buf, ",");
		}
		else{
			strcat(data_buf,"\n\n\n");
			msgSize = strlen(data_buf)+3;
			break;
		}
		i++;
	}
	data->g_flowSizeList->currCount = 0;
        bytesSent = write(sockfd, data_buf, msgSize);

	pthread_mutex_unlock(&(data->g_flowSizeList->flowSizeListLock));
}


int flowSizeParser(char *data, int **flowSizeList, int *flowSizeListLen){
	
	int flowSize, count=0;
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
		count++;
	}
	*flowSizeListLen = index;
	*flowSizeList = flowSizeListPtr;
	return count;
}
