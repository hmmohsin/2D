#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/tcp.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/time.h>
#include <math.h>
#include <sys/stat.h>

#include <pthread.h>
#include "../common/common.h"
#include "udp_conn.h"
#define DEBUG
#define MAXCLASS 11

struct Counter
{
    /* last sample taken to compute duration */
    struct timeval last_sample;
    /* current time stamp */
    struct timeval cur_sample;
    /* lock used for size_ahead */
    pthread_mutex_t counter_lock;
    /* seq */
    unsigned int seq;
    /* active flow */
    unsigned int active;
};

int sequencer_port = TG_SEQ_PORT;
bool verbose_mode = false;  /* by default, we don't give more detailed output */
bool daemon_mode = false;   /* by default, we don't run the server as a daemon */

/* data structures and variables for class based FIFO */
struct Counter *class_counters = NULL;
pthread_t broadcast_manager;
int recv_fd;

/* print usage of the program */
void print_usage(char *program);
/* read command line arguments */
void read_args(int argc, char *argv[]);
/* handle an incomming connection */
void* handle_connection(void* ptr);
/* get usleep overhead in microsecond (us) */
unsigned int get_sleep_overhead(int iter_num);
/* write a flow seq into a socket and return true if it succeeds */
bool write_flow_seq(int fd, unsigned long delta);
/* overhear seq_msg */
void *run_broadcast_manager(void *ptr);
/* Init broadcast manager */
bool init_broadcast_manager();
/* function to send seq_msg */
bool send_seq(unsigned int fc, int fd);
/* initialize per class counts */
bool init_class_counters();

int main(int argc, char *argv[])
{
    pid_t pid, sid;
    int listen_fd;
    struct sockaddr_in serv_addr;   /* local server address */
    struct sockaddr_in cli_addr;    /* remote client address */
    int sock_opt = 1;
    pthread_t serv_thread;  /* server thread */
    int* sockfd_ptr = NULL;
    socklen_t len = sizeof(struct sockaddr_in);

    /* read arguments */
    read_args(argc, argv);

    /* initializing virtual queues and vars*/
    init_class_counters();

    /* init broadcast manager */
    init_broadcast_manager();

    /* initialize local server address */
    memset(&serv_addr, 0, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = INADDR_ANY;    
    serv_addr.sin_port = htons(sequencer_port);

    /* initialize sequencer socket */
    listen_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (listen_fd < 0)
        error("Error: initialize socket");

    /* set socket options */
    if (setsockopt(listen_fd, SOL_SOCKET, SO_REUSEADDR, &sock_opt, sizeof(sock_opt)) < 0)
        error("Error: set SO_REUSEADDR option");
    if (setsockopt(listen_fd, IPPROTO_TCP, TCP_NODELAY, &sock_opt, sizeof(sock_opt)) < 0)
        error("ERROR: set TCP_NODELAY option");

    if (bind(listen_fd,(struct sockaddr *)&serv_addr,sizeof(struct sockaddr)) < 0)
        error("Error: bind");

    if (listen(listen_fd, TG_SERVER_BACKLOG_CONN) < 0)
        error("Error: listen");

    printf("Traffic Generator Sequencer listens on 0.0.0.0:%d\n", sequencer_port);

    /* if we run the server as a daemon */
    if (daemon_mode)
    {
        /* fork off the parent process */
        pid = fork();
        /* no child process is created */
        if (pid < 0)
            exit(EXIT_FAILURE);
        /* if we get the process ID of the child process, then we can exit the parent process */
        if (pid > 0)
        {
            printf("Running Traffic Generator Server as a daemon\n");
            printf("The daemon process ID: %d\n", pid);
            exit(EXIT_SUCCESS);
        }

        /* change the file mode mask */
        umask(0);

        /* create a new SID for the child process */
        sid = setsid();
        if (sid < 0)
            exit(EXIT_FAILURE);

        /* change the current working directory */
        if ((chdir("/")) < 0)
            exit(EXIT_FAILURE);

        /* close out the standard file descriptors */
        close(STDIN_FILENO);
        close(STDOUT_FILENO);
        close(STDERR_FILENO);
    }

    

    while (1)
    {
        sockfd_ptr = (int*)malloc(sizeof(int));
        if (!sockfd_ptr)
            error("Error: malloc");

        *sockfd_ptr = accept(listen_fd, (struct sockaddr *)&cli_addr, &len);
        if (*sockfd_ptr < 0)
        {
            close(listen_fd);
            free(sockfd_ptr);
            error("Error: accept");
        }
        else if (pthread_create(&serv_thread, NULL, handle_connection, (void*)sockfd_ptr) < 0)
        {
            close(listen_fd);
            free(sockfd_ptr);
            error("Error: create pthread");
        }
    }

    return 0;
}

/* handle an incomming connection */
void* handle_connection(void* ptr)
{
    struct flow_metadata flow;
    int sockfd = *(int*)ptr;
    free(ptr);
    while (1)
    {

        /* read meta data from the request */
        if (!read_flow_metadata(sockfd, &flow))
        {
            if (verbose_mode)
                printf("Cannot read metadata from the request\n");
            break;
        }

        if (verbose_mode)
            printf("Flow request: ID: %u Size: %u bytes ToS: %u Rate: %u Mbps\n", flow.id, flow.size, flow.tos, flow.rate);

        // printf("DEBUG: sequencing request recvd\n");

        /* here TOS refers to flow class */
        if (!send_seq(flow.tos, sockfd))
        {
            if (verbose_mode)
                printf("Cannot generate seq\n");
            break;
        }
    }

    close(sockfd);
    pthread_detach(pthread_self()); //musa: for virtual memory
    return (void*)0;
}

/* Print usage of the program */
void print_usage(char *program)
{
    printf("Usage: %s [options]\n", program);
    printf("-p <port>   port number (default %d)\n", TG_SERVER_PORT);
    printf("-v          give more detailed output (verbose)\n");
    printf("-d          run the server as a daemon\n");
    printf("-h          display help information\n");
}

/* Read command line arguments */
void read_args(int argc, char *argv[])
{
    int i = 1;

    while (i < argc)
    {
        if (strlen(argv[i]) == 2 && strcmp(argv[i], "-p") == 0)
        {
            if (i+1 < argc)
            {
                sequencer_port = atoi(argv[i+1]);
                if (sequencer_port < 0 || sequencer_port > 65535)
                    error("Invalid port number");
                i += 2;
            }
            /* cannot read port number */
            else
            {
                printf("Cannot read port number\n");
                print_usage(argv[0]);
                exit(EXIT_FAILURE);
            }
        }
        else if (strlen(argv[i]) == 2 && strcmp(argv[i], "-v") == 0)
        {
            verbose_mode = true;
            i += 1;
        }
        else if (strlen(argv[i]) == 2 && strcmp(argv[i], "-d") == 0)
        {
            daemon_mode = true;
            i += 1;
        }
        else if (strlen(argv[i]) == 2 && strcmp(argv[i], "-h") == 0)
        {
            print_usage(argv[0]);
            exit(EXIT_SUCCESS);
        }
        else
        {
            printf("Invalid option %s\n", argv[i]);
            print_usage(argv[0]);
            exit(EXIT_FAILURE);
        }
    }
}

/* initialize class counters */
bool init_class_counters()
{
    class_counters = calloc(MAXCLASS, sizeof(struct Counter));
    unsigned int i;
    for(i=0;i<MAXCLASS;i++)
    {
        pthread_mutex_init(&(class_counters[i].counter_lock), NULL);
        class_counters[i].seq = 0;
        class_counters[i].active = 0;
    }

    if(!class_counters)
        return false;
    return true;
}

/* send per class sequence in us for flow */
bool send_seq(unsigned int fc, int fd){

    struct seq_msg smsg;
    pthread_mutex_lock(&(class_counters[fc].counter_lock));

    smsg.seq = class_counters[fc].seq;
    smsg.active = class_counters[fc].active;
    class_counters[fc].seq += 1;
    
    printf("DEBUG: class:%u seq:%u active:%u\n",fc,class_counters[fc].seq,class_counters[fc].active);

    pthread_mutex_unlock(&(class_counters[fc].counter_lock));
    
    char buf[SEQ_MSG_SIZE] = {0};   /* buffer to hold metadata */
    /* fill in metadata */
    seq_msg2buf(smsg, buf);
    /* write the request into the socket */
    if (!(write_exact(fd, buf, SEQ_MSG_SIZE, SEQ_MSG_SIZE, 0, 0, 0, false) == SEQ_MSG_SIZE))
        return false;
    printf("DEBUG: Sending.. seq: %u\n", smsg.seq);
    return true;
}

/* write a flow seq into a socket and return true if it succeeds */
bool write_flow_seq(int fd, unsigned long delta)
{
    char buf[TG_SEQDATA_SIZE] = {0};   /* buffer to hold metadata */

    
    /* fill in metadata */
    memcpy(buf, &(delta), sizeof(delta));
    
    /* write the request into the socket */
    if (write_exact(fd, buf, TG_SEQDATA_SIZE, TG_SEQDATA_SIZE, 0, 0, 0, false) == TG_SEQDATA_SIZE)
        return true;
    else
        return false;
}

bool init_broadcast_manager(){
    /* setup UDP socket for SEQ msg broadcast and bind to it */
    printf("recv socket successful: %d\n",init_UDP_socket(&recv_fd, -1, true, true));
    pthread_create(&(broadcast_manager), NULL, run_broadcast_manager, (void *)NULL);
    return true;
}

/* run broad cast manager */
void *run_broadcast_manager(void *ptr){
    struct seq_msg smsg;
    unsigned int fc;
    while(1){
        recv_UDP_seq_msg(recv_fd, &smsg);
        fc = smsg.fc;
        pthread_mutex_lock(&(class_counters[fc].counter_lock));
        if(smsg.seq+1 > class_counters[fc].active)
            class_counters[fc].active = smsg.seq+1;
        pthread_mutex_unlock(&(class_counters[fc].counter_lock));
    }
}