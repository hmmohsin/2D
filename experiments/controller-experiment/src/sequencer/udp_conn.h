#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <stdbool.h>
#include <stddef.h>

struct seq_msg
{
	unsigned int seq;
	unsigned int fc;
	unsigned int active;
};

#define BROADCAST 6666	// BROADCAST port clients will bind to
#define SEQ_MSG_SIZE (sizeof(struct seq_msg))

bool init_UDP_socket(int *fd, int port, bool bindto, bool broadcast);
bool send_UDP_seq_msg(char *ip, int port, int fd, struct seq_msg smsg);
bool recv_UDP_seq_msg(int fd, struct seq_msg *smsg);
void seq_msg2buf(struct seq_msg smsg,char *buf);
void buf2seq_msg(char *buf, struct seq_msg *smsg);

bool init_UDP_socket(int *fd, int port, bool bindto, bool broadcast)
{

	int sock_opt, sockfd;
	struct sockaddr_in src_addr;

	if ((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) == -1) {
	    perror("socket");
        return false;
	}

	if(broadcast){
		if (setsockopt(sockfd, SOL_SOCKET, SO_BROADCAST, &sock_opt,
	        sizeof sock_opt) == -1) {
	        perror("setsockopt (SO_BROADCAST)");
	        return false;
    	}
	}

    if(bindto){
    	memset(&src_addr, 0, sizeof(src_addr));
	    src_addr.sin_family = AF_INET;
	    src_addr.sin_addr.s_addr = INADDR_ANY;
	    if(broadcast)
	    	src_addr.sin_port = htons(BROADCAST);
	    else
	    	src_addr.sin_port = htons(port);

	    if (bind(sockfd,(struct sockaddr *)&src_addr,sizeof(struct sockaddr)) < 0){
        	perror("Error: bind");
            return false;
	    }
    }

    *fd = sockfd;
    return true;
}

bool send_UDP_seq_msg(char *ip, int port, int fd, struct seq_msg smsg)
{

	struct sockaddr_in dst_addr;
	int numbytes;
	char buf[SEQ_MSG_SIZE] = {0};

	memset(&dst_addr, 0, sizeof(dst_addr));
    dst_addr.sin_family = AF_INET;
    dst_addr.sin_addr.s_addr = inet_addr(ip);
    dst_addr.sin_port = htons(port);

    seq_msg2buf(smsg,buf);

    /*DEBUGGING*/
    /*

    int sock_opt, rv, sock_opt_len;
    sock_opt_len = sizeof(sock_opt);
    rv = getsockopt(fd, SOL_SOCKET, SO_BROADCAST, (char *) &sock_opt, &sock_opt_len);

    if(rv == 0){
        if(sock_opt == 1)
            printf("INFO: BROADCASTING IS ENABLED\n");
        else
            printf("INFO: BROADCASTING IS DISABLED\n");

    } else
        printf("CANT GET GETSOCKOPT\n");
    */

    /*DEBUGGING END*/

    if ((numbytes=sendto(fd, buf, SEQ_MSG_SIZE, 0, (struct sockaddr *)&dst_addr, sizeof dst_addr)) == -1) {
        perror("sendto");
        return false;
    }

    return true;
}

bool recv_UDP_seq_msg(int fd, struct seq_msg *smsg)
{

	struct sockaddr_in dst_addr;
	socklen_t addr_len;
	addr_len = sizeof dst_addr;
	int numbytes;
	
	char buf[SEQ_MSG_SIZE] = {0};

	if ((numbytes = recvfrom(fd, buf, SEQ_MSG_SIZE, 0,
		(struct sockaddr *)&dst_addr, &addr_len)) == -1) {
		perror("recvfrom");
		return false;
	}

	buf2seq_msg(buf,smsg);

	#ifdef DEBUG
	printf("numbytes: %d\n", numbytes);
	#endif

	return true;
}

void seq_msg2buf(struct seq_msg smsg,char *buf){
	
	/* constructing a message */
    memcpy(buf + offsetof(struct seq_msg, seq), &(smsg.seq), sizeof(smsg.seq));
    memcpy(buf + offsetof(struct seq_msg, fc), &(smsg.fc), sizeof(smsg.fc));
    memcpy(buf + offsetof(struct seq_msg, active), &(smsg.active), sizeof(smsg.active));
}

void buf2seq_msg(char *buf, struct seq_msg *smsg){
	/* copying content of buf into smsg */
	memcpy(&(smsg->seq), buf + offsetof(struct seq_msg, seq), sizeof(smsg->seq));
    memcpy(&(smsg->fc), buf + offsetof(struct seq_msg, fc), sizeof(smsg->fc));
    memcpy(&(smsg->active), buf + offsetof(struct seq_msg, active), sizeof(smsg->active));

	#ifdef DEBUG
	printf("Seq number recv'd: %u\n", smsg->seq);
	printf("Class recv'd: %u\n", smsg->fc);
	#endif
}
