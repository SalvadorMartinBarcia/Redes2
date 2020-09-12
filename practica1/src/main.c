#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>
#include <sys/sem.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <semaphore.h>
#include <arpa/inet.h>
#include <errno.h>
#include <time.h>
#include <resolv.h>
#include <unistd.h>
#include <syslog.h>
#include <pthread.h>
#include <assert.h>

#include "processrequest.h"

void *processRequest();
void do_daemon();


#define MAX_TYPES 11
#define BUFF 4096

//Funcion principal
int main(int argc, char const *argv[])
{
    int clientfd = -1, sockfd = -1, i;
    socklen_t addrlen;
    struct sockaddr_in my_addr;
    struct sockaddr_in client_addr;
    pthread_t tid;
    int odin, einherjar;
    char *aux;
    config configuracion;
    //Aqui en caso de utilizarse se activaria el modo daemon
    //do_daemon();

    //Obtenemos la configuracion del servidor del fichero config.conf
    configuracion = getServerConfig();


    //Guardamos el pid del proceso padre
    odin = getpid();

    //Abrimos el socket
    if ((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0)
    {
        fprintf(stdout, "Error al abrir el socket\n");
        return -1;
    }

    //memset(&my_addr, 0, sizeof(struct sockaddr_in));

    //Cargamos la informacion en la estructura de configuracion
    my_addr.sin_family = AF_INET;
    my_addr.sin_port = htons(atoi(configuracion.listen_port));
    my_addr.sin_addr.s_addr = INADDR_ANY;

    //Hacemos el bind con el socket abierto antes y la estructura creada
    if (bind(sockfd, (struct sockaddr *)&my_addr, sizeof(my_addr)) == -1)
    {
        fprintf(stdout, "Error al hacer el bind\n");
        printf("%s\n", strerror(errno));
        return -2;
    }
    //Hacemos listen usando el maximo tamaño de cola extraido de server.conf
    if (listen(sockfd, atoi(configuracion.max_clientes)) != 0)
    {
        perror("Error al hacer el listen");
        exit(errno);
    }
    printf("ESPERANDO CONEXIONES\n");

    //Aceptamos las conexiones creando un nuevo hilo por cada peticion
    while (1)
    {
        addrlen = sizeof(client_addr);

        // Aceptamos conexiones
        clientfd = accept(sockfd, (struct sockaddr *)&client_addr, &addrlen);
        // printf("Conexión desde [%s:%d]\n", inet_ntoa(client_addr.sin_addr), ntohs(client_addr.sin_port));
        pthread_create(&tid, NULL, &processRequest, (void *)&clientfd);
    }

    close(sockfd);
    return 0;
}


/********
* FUNCIÓN: do_daemon()
* DESCRIPCIÓN: Activa el modo daemon del servidor
********/
void do_daemon()
{
    pid_t pid;

    pid = fork();

    if (pid > 0)
        exit(EXIT_SUCCESS); //Si es el proceso padre lo cerramos
    if (pid < 0)
        exit(EXIT_FAILURE); //Si hay error en el fork salimos

    umask(0);
    setlogmask(LOG_UPTO(LOG_INFO)); //Open logs here
    openlog("Server system messages:", LOG_CONS | LOG_PID | LOG_NDELAY, LOG_LOCAL3);
    syslog(LOG_ERR, "Initiating new server.");

    if (setsid() < 0)
    {
        syslog(LOG_ERR, "Error creando un nuevo SID para el proceso hijo.");
        exit(EXIT_FAILURE);
    }

    if (chdir("/") < 0)
    {
        syslog(LOG_ERR, "Error cambiando el directorio actual uwu = \"/\"");
        exit(EXIT_FAILURE);
    }

    syslog(LOG_INFO, "Cerrando los descriptores de ficheros estandar");
    close(STDIN_FILENO);
    close(STDOUT_FILENO);
    close(STDERR_FILENO);
}