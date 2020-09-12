
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
#include "picohttpparser.h"

//Constantes Numericas
#define MAX_TYPES 11
#define BUFF 4096


//Cadenas con dias y meses en el formato especificado
const char *months[12] = {"Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"};
const char *days[7] = {"Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"};

// Estructura para almacenar los tipos de archivos
struct
{
    char *type;
    char *ext;
} types[] = {
    {"text/plain", "txt"},
    {"text/html", "html"},
    {"text/html", "htm"},
    {"image/gif", "gif"},
    {"image/jpeg", "jpeg"},
    {"image/jpeg", "jpg"},
    {"video/mpeg", "mpeg"},
    {"video/mpeg", "mpg"},
    {"application/msword", "doc"},
    {"application/msword", "docx"},
    {"application/pdf", "pdf"}};

//Variable global para almacenar informacion del archivo config.conf
config configuracion;


/********
* FUNCIÓN: char *processRequest(char *request)
* ARGS_IN: void *clientfd socket donde se esta procesando el cliente
* DESCRIPCIÓN: Procesa la petición de entrada, y devuelve una respuesta
********/
void *processRequest(void *clientfd)
{
    //
    struct sockaddr_in client_addr;
    socklen_t addrlen;
    time_t t = time(NULL);
    struct tm *t_stand = localtime(&t);
    struct tm *last_mod_time;
    struct stat filestat;
    char type[20], script[50], script_aux[50];
    int cfd = *((int *)clientfd);
    int file_exist = 0;
    char *aux;

    //
    struct phr_header headers[500];
    int pret, minor_version = -1, i, len_ext, file_id, file_len;
    char buf[BUFF], path_root[BUFF], path_file[BUFF], path_file_aux[BUFF];
    const char *method, *path;
    ssize_t ret_size, buflen = 0, prevbuflen = 0;
    size_t method_len, path_len, num_headers;
    memset(buf, '\0', BUFF);
    memset(path_root, '\0', BUFF);
    memset(path_file, '\0', BUFF);
    memset(path_file_aux, '\0', BUFF);

    //Separamos el hilo del padre de forma que pueda funcionar independientemente
    //sin tener que volver al padre
    pthread_detach(pthread_self());

    //Recogemos la IP del usuario que se ha conectado al servidor
    addrlen = sizeof(client_addr);
    getpeername(cfd, (struct sockaddr *)&client_addr, &addrlen);

    //Obtenemos la configuracion del servidor del fichero config.conf
    configuracion = getServerConfig();
    while (1)
    {
        // while ((ret_size = read(cfd, buf + buflen, sizeof(buf) - buflen)) == -1 && errno == EINTR);
        //Recibimos el mensaje
        ret_size = recv(cfd, buf, sizeof(buf) - 1, 0);
        if (ret_size <= 0)
        {
            close(cfd);
            pthread_exit(NULL);
        }

        prevbuflen = buflen;
        buflen += ret_size;
        num_headers = 500;

        //Parseamos con el picoparser la peticion
        pret = phr_parse_request(buf, buflen, &method, &method_len, &path, &path_len,
                                 &minor_version, headers, &num_headers, prevbuflen);

        //Si se ha parseado correctamente salimos del while, sino devolvemos error
        if (pret > 0)
            break; /* successfully parsed the request */
        else if (pret == -1)
        {
            sendBadRequest(cfd, buf);
        }

        assert(pret == -2);
        if (buflen == sizeof(buf))
        {
            sendBadRequest(cfd, buf);
        }
    }
    strcpy(path_root, configuracion.server_root);
    //Aniadimos el resto del path al root del servidor
    if (!strncmp(path, "/", path_len))
    {
        strcat(path_root, "/index.html");
    }
    else
    {
        strncat(path_root, path, path_len); //Aniadimos el server_root al inicio del path
    }
    path_len = strlen(path_root);

    if (!strncmp(method, "OPTIONS ", 7) || !strncmp(method, "options ", 7))
    {
        sendOptions(cfd, buf);
    }
    //con este if convertimos el metodo post en uno get y procesamos igual ambos
    if (!strncmp(method, "POST ", 4) || !strncmp(method, "post ", 4))
    {

        char *body = strstr(buf, "\r\n\r\n");
        body += 4 * sizeof(char); //Quitamos los retorno de carro y los saltos de linea
        if (!strstr(path_root, "?"))
        {
            //Ponemos un ? porque es lo que se pone en las peticiones GET para los argumentos
            strcat(path_root, "?");
        }
        else
        {
            strcat(path_root, "&");
        }
        strcat(path_root, body);
        path_len += 1 + strlen(body);
    }
    strcpy(script_aux, path_root);
    strcpy(script, strtok(script_aux, "?"));

    if (!strcmp(script + strlen(script) - 3, ".py") || !strcmp(script + strlen(script) - 4, ".php"))
    {
        char command[BUFF];
        //Miramos que tipo de script es
        if (!strcmp(script + strlen(script) - 3, ".py"))
        {
            strcpy(command, "python3 ");
        }
        else
        {
            strcpy(command, "php ");
        }

        //le concatenamos el nombre del fichero a ejecutar
        strcat(command, script);
        //le concatenamos los argumentos
        while (strtok(NULL, "=") != NULL)
        {
            strcat(command, " ");
            strcat(command, strtok(NULL, "&"));
        }
        // concatenamos el volcado a un fichero
        strcat(command, " > ./htmlfiles/file.txt");
        if (system(command) == -1)
        {
            sendBadRequest(cfd, buf);
        }
        else
        {
            //ponemos la variable a uno para borrar mas tarde el fichero
            file_exist = 1;
        }
        //ponemos el path_file con file.txt
        strcpy(path_file, "./htmlfiles/file.txt");
    }
    else
    {
        // quitamos los argumentos si los tiene y lo metemos en path file
        strcpy(path_file_aux, path_root);
        strcpy(path_file, strtok(path_file_aux, "?"));
    }
    path_len = strlen(path_file);

    // creamos una estructura con la ultima modificacion del archivo
    if (stat(path_file, &filestat) < 0)
    {
        if (file_exist == 1)
        {
            system("rm ./htmlfiles/file.txt");
        }
        sendNotFound(cfd, buf);
    }

    //pasamos a estandar la fecha
    last_mod_time = gmtime(&filestat.st_mtim.tv_sec);

    //miramos si soportamos el tipo de archivo
    strcpy(type, "none");

    for (i = 0; i < MAX_TYPES; i++)
    {
        len_ext = strlen(types[i].ext);

        if (!strncmp(path_file + path_len - len_ext, types[i].ext, len_ext))
        {
            strcpy(type, types[i].type);
            break;
        }
    }
    // si no era ninguno de los ficheros que soportamos devolvemos un error
    if (!strcmp(type, "none"))
    {
        if (file_exist == 1)
        {
            system("rm ./htmlfiles/file.txt");
        }
        sendBadRequest(cfd, buf);
    }

    // abrimos el fichero en modo lectura para ver su tamanio y enviarlo
    file_id = open(path_file, O_RDONLY);
    if (file_id == -1)
    {
        if (file_exist == 1)
        {
            system("rm ./htmlfiles/file.txt");
        }
        sendNotFound(cfd, buf);
    }

    file_len = lseek(file_id, 0, SEEK_END);
    lseek(file_id, 0, SEEK_SET);

    sprintf(buf, "HTTP/1.%d 200 OK\r\n"
                 "Date: %s, %d %s %d %d:%d:%d\r\n"
                 "Server: %s\r\n"
                 "Last-Modified: %s, %d %s %d %d:%d:%d\r\n"
                 "Content-Lenght: %d\r\n"
                 "Content-Type: %s\r\n\r\n",
            minor_version,
            days[t_stand->tm_wday],
            t_stand->tm_mday, months[t_stand->tm_mon], t_stand->tm_year + 1900,
            t_stand->tm_hour, t_stand->tm_min, t_stand->tm_sec,
            configuracion.server_signature,
            days[last_mod_time->tm_wday],
            last_mod_time->tm_mday, months[last_mod_time->tm_mon], last_mod_time->tm_year + 1900,
            last_mod_time->tm_hour, last_mod_time->tm_min, last_mod_time->tm_sec,
            file_len,
            type);
    send(cfd, buf, strlen(buf), 0);

    while ((file_len = read(file_id, buf, BUFF)) > 0)
    {
        send(cfd, buf, file_len, 0);
    }

    close(file_id);
    sleep(1);
    if (file_exist == 1)
    {
        system("rm ./htmlfiles/file.txt");
    }
    close(cfd);
    pthread_exit(NULL);
}


/********
* FUNCIÓN: void sendBadRequest(int cfd, char *buf)
* ARGS_IN: int cfd socket donde se esta procesando el cliente
*          char *buf buffer donde se almacena la respuesta a enviar
* DESCRIPCIÓN: Envia un error 400 bad request al cliente
********/
void sendBadRequest(int cfd, char *buf)
{
    time_t t = time(NULL);
    int minor_version = -1;
    struct tm *t_stand = localtime(&t);
    sprintf(buf, "HTTP/1.%d 400 Bad Request\r\n"
                 "Date: %s, %d %s %d %d:%d:%d\r\n"
                 "Server:%s\r\n"
                 "Content-Lenght:%d\r\n"
                 "Connection: Closed\r\n"
                 "Content-Type: text/html\r\n\r\n"
                 "<html><head>\n<title>400 Bad Request</title>\n</head><body>\n<h1>400-Bad Request</h1></body></html>",
            minor_version,
            days[t_stand->tm_wday],
            t_stand->tm_mday, months[t_stand->tm_mon], t_stand->tm_year + 1900,
            t_stand->tm_hour, t_stand->tm_min, t_stand->tm_sec,
            configuracion.server_signature,
            96);
    send(cfd, buf, strlen(buf), 0);
    close(cfd);
    pthread_exit(NULL);
}

/********
* FUNCIÓN: void sendNotFound(int cfd, char *buf)
* ARGS_IN: int cfd socket donde se esta procesando el cliente
*          char *buf buffer donde se almacena la respuesta a enviar
* DESCRIPCIÓN: Envia un error 404 not found al cliente
********/
void sendNotFound(int cfd, char *buf)
{
    time_t t = time(NULL);
    int minor_version = -1;
    struct tm *t_stand = localtime(&t);
    sprintf(buf, "HTTP/1.%d 404 Not Found\r\n"
                 "Date: %s, %d %s %d %d:%d:%d\r\n"
                 "Server:%s\r\n"
                 "Content-Lenght:%d\r\n"
                 "Connection: Closed\r\n"
                 "Content-Type: text/html\r\n\r\n"
                 "<html><head>\n<title>404 Not Found</title>\n</head><body>\n<h1>404-Not Found</h1></body></html>",
            minor_version,
            days[t_stand->tm_wday],
            t_stand->tm_mday, months[t_stand->tm_mon], t_stand->tm_year + 1900,
            t_stand->tm_hour, t_stand->tm_min, t_stand->tm_sec,
            configuracion.server_signature,
            92);
    send(cfd, buf, strlen(buf), 0);
    close(cfd);
    pthread_exit(NULL);
}
/********
* FUNCIÓN: void sendOptions(int cfd, char *buf)
* ARGS_IN: int cfd socket donde se esta procesando el cliente
*          char *buf buffer donde se almacena la respuesta a enviar
* DESCRIPCIÓN: Envia la respuesta a las peticiones OPTIONS del cliente
********/
void sendOptions(int cfd, char *buf)
{
    time_t t = time(NULL);
    int minor_version = -1;
    struct tm *t_stand = localtime(&t);
    sprintf(buf, "HTTP/1.%d 200 OK\r\n"
                 "Allow: OPTIONS, GET, POST\r\n"
                 "Date: %s, %d %s %d %d:%d:%d\r\n"
                 "Server:%s\r\n"
                 "Content-Lenght:%d\r\n\r\n",
            minor_version,
            days[t_stand->tm_wday],
            t_stand->tm_mday, months[t_stand->tm_mon], t_stand->tm_year + 1900,
            t_stand->tm_hour, t_stand->tm_min, t_stand->tm_sec,
            configuracion.server_signature,
            0);
    send(cfd, buf, strlen(buf), 0);
    close(cfd);
    pthread_exit(NULL);
}

/********
* FUNCIÓN: config getServerConfig()
* DESCRIPCIÓN: Carga la informacion del archivo de configuracion en una 
*              variable 
* ARGS_OUT: Devuelve una estructura config con la configuracion extraida del fichero
********/
config getServerConfig()
{
    config conf;
    //Abrimos el fichero de configuracion (./server.conf) y extraemos
    //root, signature, puerto y maximo de clientes, guardandolos en
    //sus respectivas variables
    FILE *c = NULL;
    int i;
    char *aux;
    c = fopen("server.conf", "r");

    aux = malloc(sizeof(conf.server_root) * sizeof(char));
    fgets(aux, sizeof(conf.server_root), c);
    strtok(aux, "=");
    strcpy(conf.server_root, strtok(NULL, "="));
    free(aux);
    for (i = 0; conf.server_root[i] != '\n'; i++)
        ;
    conf.server_root[i] = '\0'; //quitamos el salto de linea que esta en server_root

    aux = malloc(sizeof(conf.max_clientes) * sizeof(char));
    fgets(aux, sizeof(conf.max_clientes), c);
    strtok(aux, "=");
    strcpy(conf.max_clientes, strtok(NULL, "="));
    free(aux);
    fgets(conf.listen_port, sizeof(conf.listen_port), c);
    conf.listen_port, strtok(conf.listen_port, "=");
    strcpy(conf.listen_port, strtok(NULL, "="));

    fgets(conf.server_signature, sizeof(conf.server_signature), c);
    strtok(conf.server_signature, "=");
    strcpy(conf.server_signature, strtok(NULL, "="));
    
    fclose(c);
    return conf;
}