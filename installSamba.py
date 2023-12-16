###########################################################################
#																		  #
#		SCRIPT DE INSTALACIÓN DE SAMBA Y UNIÓN AL DOMINIO				  #
#																		  #
#		Sergio Pérez Ríos				2º ASIR-A						  #
#                                                                         #
###########################################################################
#--------------------------------------------------------------------------
# BIBLIOTECAS
import sys
import re
import os
import subprocess
import socket
import datetime

#--------------------------------------------------------------------------
# FUNCIONES

# Función para averiguar mi dirección IP
def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip_privada = s.getsockname()[0]
        s.close()
        return ip_privada
    except Exception as e:
        escribir_en_log(f"""Error al obtener la dirección IP privada: {e}""")
        return None

# Función que consulta la hora del sistema
def get_datetime():
	fecha_hora = datetime.datetime.now()
	return fecha_hora

# Función que averigua el nombre de la máquina controladora de dominio
# Si la encuentra, devuelve un array del tipo: salida->0[direccion ip] 1[nombre máquina]
# Suponemos que es red /24
def averiguar_DC(red):
    es_esta = False
    salida = [] # Array que se devolverá a menos que se encuentre el DC
    partes_red = RED.split('.')
    red = '.'.join(partes_red[:3])
    direccion_host = 1
    
    while direccion_host <= 254 and es_esta == False:
        direccion_ip = red + '.' + str(direccion_host)
        
        # Escaneamos los puertos de cada dirección ip
        nmap = "nmap -p- --open -sV "+direccion_ip
        
        # Convierto a texto la salida de nmap
        
        salida_nmap = subprocess.check_output(nmap, shell=True)
        salida_nmap = salida_nmap.decode("utf-8")
        
        # array para guardar los puertos usados por ldap
        puertos_ldap = []
        
        # Analiza la salida de Nmap línea por línea
        for linea in salida_nmap.splitlines():
            
            # Busca la línea que contiene "Microsoft Windows Active Directory LDAP"
            patron_ldap = re.compile(r"Microsoft Windows Active Directory LDAP")
            if patron_ldap.search(linea):
                es_esta=True
                
                # Contador para que solo añada la IP y la máquina una vez
                contador=1
                if contador == 1:
                    salida.append(direccion_ip)
                    
                    # Usamos una expresión regular para consular el nombre del DC
                    exp = re.compile(r"Service Info: Host: (.+?);")
                    coincidencia = exp.search(salida_nmap)
                    if coincidencia:
                        salida.append(coincidencia.group(1))
                contador+=1
                
                # Utiliza una expresión regular para extraer el número del puerto
                match = re.search(r"(\d+)/tcp", linea)
                if match:
                    puerto_ldap = int(match.group(1))
                    puertos_ldap.append(puerto_ldap)
                    
        direccion_host += 1
    
    # Si no está vacío informamos sobre la información recopìlada
    if salida:
        escribir_en_log("Puertos de LDAP en " + salida[1] + ":")
        for puerto in puertos_ldap:
            escribir_en_log(">"+ str(puerto) +"<")
    return salida
    
# Función que escribe en el fichero que le hacemos (solo acepta: smb.conf | krb5.conf | hostname | hosts)
def configurar(fichero):
    if fichero == "smb.conf":
        file = open("/etc/samba/" + fichero, "w")
        file.write(SMB_CONF)
        file.close()
    elif fichero == "krb5.conf":
        file = open("/etc/" + fichero, "w")
        file.write(KRB5_CONF)
        file.close()
    elif fichero == "hosts":
        file = open("/etc/" + fichero, "w")
        file.write(HOSTS)
        file.close()
    elif fichero == "resolv.conf":
        file = open("/etc/" + fichero, "w")
        file.write(RESOLV)
        file.close()
    elif fichero == "nsswitch.conf":
        file = open("/etc/" + fichero, "w")
        file.write(NSSWITCH)
        file.close()
    else:
        escribir_en_log("Archivo incorrecto introducido")

# Función que escribe información sobre lo que va haciendo el programa y los errores
def escribir_en_log(cadena):
    log = open(LOG, "a")
    log.write(cadena + '\n')
    log.close()

#--------------------------------------------------------------------------
# VARIABLES
# Comprobamos que los argumentos se hayan introducido correctamente
if len(sys.argv) != 5 or sys.argv[3] != 'Administrador' or sys.argv[4] != "Departamento1!":
    print("Error en los argumentos. USO -> installSamba <máquina> <dominio> <usuario> <contraseña>")
    exit(1)

LOG = "/var/log/log_union_dominio"
NOMBRE_MAQUINA = sys.argv[1]
DOMINIO = sys.argv[2]
DOMINIO_MAYUS = DOMINIO.upper()
print(DOMINIO_MAYUS)
USUARIO = sys.argv[3]
PASSWORD = sys.argv[4]
MI_IP = get_ip()
# Suponemos que la red es /24
octetos_red = MI_IP.split('.')
RED = '.'.join(octetos_red[:3])
fecha_hora = (str(get_datetime()).split('.'))[0].replace(":", "·")

# Consulto la IP y nombre de la máquina DC
info_DC = []
info_DC = averiguar_DC(RED)
NOMBRE_DC = info_DC[1]
NOMBRE_DC_minus = NOMBRE_DC.lower()

# Si info_DC está vacío nos salimos del programa (no encontro DC)
if not info_DC:
    escribir_en_log("No se ha encontrado ningún controlador de dominio")
    escribir_en_log("Saliendo del programa")
    exit(2)
print("Averigua ip del DC: " + info_DC[0]+"      "+info_DC[1])


# Contenido de smb.conf
SMB_CONF = f"""
[global]
netbios name = {NOMBRE_MAQUINA.upper()}
server role = MEMBER SERVER
workgroup = {DOMINIO_MAYUS.replace(".COM", "")}
realm = {DOMINIO_MAYUS}
security = ADS
winbind refresh tickets = yes
winbind nss info = template
winbind expand groups = 2
winbind nested groups =yes
winbind enum groups = yes
winbind enum users = yes
winbind use default domain = yes
template homedir = /home/%U
template shell = /bin/bash
idmap config * : backend = tdb
idmap config * : range = 10000-20000
idmap config {DOMINIO_MAYUS.replace(".COM", "")} : range = rid
idmap config {DOMINIO_MAYUS.replace(".COM", "")} : range = 30000-40000 
"""

# Contenido de krb5.conf
KRB5_CONF = f"""
[libdefaults]
default_realm = {DOMINIO_MAYUS}
dns_lookup_realm = false
dns_lookup_kdc = true
forwardable = true
[realms]
{DOMINIO_MAYUS} = {{
kdc = {NOMBRE_DC_minus}.{DOMINIO}
admin_server = {NOMBRE_DC_minus}.{DOMINIO}
}}
[domain_realm]
.{DOMINIO} = {DOMINIO_MAYUS}
{DOMINIO} = {DOMINIO_MAYUS}
"""

# Generamos una cabecera para el log
cabecera = '\n' 
cabecera += '[ ' + fecha_hora + ']' + '\n'
cabecera += '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~' + '\n'  
cabecera += '@  FICHERO DE LOG [Unión al dominio]   @' + '\n' 
cabecera += '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~' + '\n'
escribir_en_log(cabecera)

# Contenido de hosts
HOSTS = f"""
127.0.0.1       localhost
{MI_IP}     {NOMBRE_MAQUINA}.{DOMINIO}  {NOMBRE_MAQUINA}
{info_DC[0]}        {info_DC[1]}.{DOMINIO}  {info_DC[1]}
# The following lines are desirable for IPv6 capable hosts
#::1     localhost ip6-localhost ip6-loopback
#ff02::1 ip6-allnodes
#ff02::2 ip6-allrouters
"""

# Contenido de resolv.conf
RESOLV = f"""
domain {DOMINIO}
domain google.com
search {DOMINIO}
nameserver {info_DC[0]}
nameserver 8.8.8.8
"""

# Contenido de nsswitch.conf
NSSWITCH = f"""
passwd: files systemd winbind
group: files systemd winbind
shadow: files
gshadow: files

hosts: files dns 
networks: files

protocols: db files
services: db files
ethers: db files
rpc: db files

netgroup: nis
"""


#--------------------------------------------------------------------------
# PROGRAMA

# Instalamos los paquetes

try:
    subprocess.run(["apt", "update"], stdout=subprocess.PIPE)
    escribir_en_log("Instalando paquetes")
except:
    escribir_en_log("La instalación de paquetes falló")
    
try:
    subprocess.run(["apt", "install", "-y", "realmd", "packagekit", "winbind", "samba", "smbclient", "cifs-utils", "libnss-winbind", "libpam-winbind", "krb5-user", "krb5-kdc", "krb5-config"], stdout=subprocess.PIPE)
    escribir_en_log("Actualizando repositorios")
except:
    escribir_en_log("La actualización de repositorios falló")

# Cambiamos el nombre de la máquina usando hostnamectl
try:
    subprocess.run(["hostnamectl", "set-hostname", NOMBRE_MAQUINA], stdout=subprocess.PIPE)
    escribir_en_log("Instalando paquetes")
except:
    escribir_en_log("La instalación de paquetes falló")


# Configuramos elfichero resolv.conf
configurar("resolv.conf")
escribir_en_log("Se ha configurado el fichero resolv.conf")

# Editamos el fichero de hosts
configurar("hosts")
escribir_en_log("Se ha configurado el fichero hosts")

# Configuramos el fichero de samba
configurar("smb.conf")
escribir_en_log("Se ha configurado el fichero smb.conf")

# Configuramos kerberos
configurar("krb5.conf")
escribir_en_log("Se ha configurado el fichero krb5.conf")

# Configuramos nsswitch.conf
configurar("nsswitch.conf")
escribir_en_log("Se ha configurado el fichero krb5.conf")

# Reiniciamos smb y nmbd
try:
    subprocess.run(["systemctl", "restart", "smbd", "nmbd"])
    escribir_en_log("Reiniciando los demonios de samba")
except:
    escribir_en_log("Fallo al reiniciar los demonios de samba")


# Nos unimos al dominio con las credenciales proporcionadas
try:
    subprocess.run(["net", "ads", "join", "-U", f'{USUARIO}%{PASSWORD}'])
    escribir_en_log("Uniéndonos al domino")
except:
    escribir_en_log("Fallo al unirnos al dominio")


# Reiniciamos winbind
try:
    subprocess.run(["systemctl", "restart", "winbind"], stdout=subprocess.PIPE)
    escribir_en_log("Reiniciando winbind")
except:
    escribir_en_log("Fallo al reiniciar winbind")

escribir_en_log("FIN DEL PROGRAMA  (" + fecha_hora + ")")