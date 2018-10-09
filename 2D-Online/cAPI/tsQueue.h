#ifndef QUEUE_H_INCLUDED
#define QUEUE_H_INCLUDED

# include <semaphore.h>
# include <pthread.h>

typedef struct tsQNode
{
	void *data;
  	struct tsQNode *next;
}node;

typedef struct tsQueue
{
	unsigned int queue_size;
	unsigned int obj_size;

	pthread_mutex_t queue_lock;	
	sem_t queue_sem;

	node *head;
	node *tail;
}queue;

int queue_init(queue *q, unsigned int obj_size);
int tsEnqueue(queue *, const void *);
void tsDequeue(queue *, void *);
void delete_queue(queue *);
unsigned int get_queue_size(queue *);

#endif /* QUEUE_H_INCLUDED */
