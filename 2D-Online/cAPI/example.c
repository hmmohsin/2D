# include <stdio.h>
# include <stdlib.h>
# include <unistd.h>
# include <pthread.h>
# include <time.h>

# include "sim.h"
unsigned int *thresholdsList = NULL;

int get_rand(int min, int max)
{
	return (rand() %(max + 1 - min) + min);
}

void *print_thresholds(void *args)
{
	int itr=0;
	while(1)
	{
		printf("Info: print_threshold\n");
		for (itr=0; itr<10; itr++){
			printf("%d: %d\n",itr,thresholdsList[itr]);
			sleep(1);
		}
	}
}

void *q_replay(void *args)
{
	queue *controller_queue = (queue*)args;

	int count = 0, flowSize = 0, max=10000, min=1, iat=0;
	int cidx=0, classCount =0, thStart=0, thEnd=0, classID=0;
	srand(time(NULL));
	char tuple[100];
	FILE *fp = fopen("arrival.txt","r");

	while (fgets(tuple, sizeof(tuple), fp) != NULL){
		printf("Flow Info: %s\n",tuple);
                sscanf(tuple, "%d %d", &flowSize, &iat);
		tsEnqueue(controller_queue, &flowSize);
		count++;
		usleep(iat);
        }
}

void *send_stats(void *args)
{
	do{
		printf("Info: send_stats\n");
		sendLoadStats();
		sendFlowStats();
		sleep(2);
	}while(1);
}

int main(){

	queue *q = malloc(sizeof(queue));
	queue_init(q, sizeof(int));
	char *ipAddr = "10.1.1.28";
	int port = 50011;
	pthread_t thread_id;

	thresholdsList = (unsigned int*)calloc(10, sizeof(unsigned int));

	//pthread_create(&thread_id, NULL, print_thresholds, (void*)q);
	pthread_create(&thread_id, NULL, q_replay, (void*)q);
	pthread_create(&thread_id, NULL, send_stats, NULL);
	initialize(ipAddr, port, q, thresholdsList);

	do{
		sleep(4);
	}while(1);
		
	/*Call this function to initialize the library
	 queue is implemented in a  thread safe, producer-
	consumer fashion. so don't worry about the lock and mutex.
	You can acquire an integrated lock of thresholdsStatsList
	before reading the class thresholds to avoid any transient
	stat issue*/
}

