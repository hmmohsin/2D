#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <semaphore.h>
#include <pthread.h>
#include <unistd.h>
#include "tsQueue.h"

int queue_init(queue *q, unsigned int obj_size)
{
	if (obj_size < 1)
		return -1; 
	q->obj_size = obj_size;
	q->queue_size = 0;
	q->head = q->tail = NULL;
	
	pthread_mutex_init(&(q->queue_lock), NULL);
	sem_init(&(q->queue_sem), 0, 0);

	return 1;
}

int tsEnqueue(queue *q, const void *data)
{
	node *new_node = (node *)malloc(sizeof(node));

    	if(new_node == NULL)
    	{
		return -1;
    	}

    	new_node->data = malloc(q->obj_size);

    	if(new_node->data == NULL)
    	{
        	free(new_node);
        	return -1;
    	}

    	new_node->next = NULL;

    	memcpy(new_node->data, data, q->obj_size);

	pthread_mutex_lock(&(q->queue_lock));
    	if(q->queue_size == 0)
    	{
        	q->head = q->tail = new_node;
    	}
    	else
    	{
        	q->tail->next = new_node;
        	q->tail = new_node;
    	}

    	q->queue_size = q->queue_size+1;
	pthread_mutex_unlock(&(q->queue_lock));
	sem_post(&(q->queue_sem));

    	return 0;
}

void tsDequeue(queue *q, void *data)
{
	sem_wait(&(q->queue_sem));
	pthread_mutex_lock(&(q->queue_lock));
    	if(q->queue_size > 0)
    	{
		node *temp = q->head;
		memcpy(data, temp->data, q->obj_size);
 
        	if(q->queue_size > 1)
        	{
            		q->head = q->head->next;
        	}
        	else
        	{
            		q->head = NULL;
            		q->tail = NULL;
        	}

        	q->queue_size = q->queue_size-1;
        	free(temp->data);
        	free(temp);
    	}
	else
		printf("queue is empty\n");
	
	pthread_mutex_unlock(&(q->queue_lock));
}

void delete_queue(queue *q)
{
	pthread_mutex_lock(&(q->queue_lock));
  	node *temp;

  	while(q->queue_size > 0)
  	{
      		temp = q->head;
      		q->head = temp->next;
      		free(temp->data);
      		free(temp);
      		q->queue_size--;
  	}

  	q->head = q->tail = NULL;
	pthread_mutex_unlock(&(q->queue_lock));
}

unsigned int get_queue_size(queue *q)
{
	int size = 0;	
	pthread_mutex_lock(&(q->queue_lock));
	size = q->queue_size;
	pthread_mutex_unlock(&(q->queue_lock));
	
	return size;
}
