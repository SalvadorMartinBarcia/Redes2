#ifndef PROCESSREQUEST_H
#define PROCESSREQUEST_H


typedef struct
{

    char server_root[30];
    char server_signature[40];
    char max_clientes[30];
    char listen_port[30];

} config;

config getServerConfig();
void sendBadRequest(int cfd, char * buf);
void sendNotFound(int cfd, char * buf);
void sendOptions(int cfd, char *buf);
void *processRequest(void *clientfd);
#endif