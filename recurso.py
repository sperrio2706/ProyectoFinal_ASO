###########################################################################
#																		  #
#		SCRIPT DE CREACIÓN DE RECURSOS	PARA GRUPOS EN EL DOMINIO		  #
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
import datetime
import winrm

#--------------------------------------------------------------------------
# FUNCIONES

# Función que consulta la hora del sistema
def get_datetime():
	fecha_hora = datetime.datetime.now()
	return fecha_hora

# Función que escribe en el log
def escribir_en_log(cadena):
    log = open(LOG, "a")
    log.write(cadena + '\n')
    log.close()

# Función que añade la plantilla al fichero
def configurar(fichero):
    if fichero == "smb.conf":
        # Lo abrimos en modo adición para que sobre escriba
        file = open("/etc/samba/" + fichero, "a")
        file.write(SMB_RECURSO)
        file.close()
    else:
        escribir_en_log("Archivo incorrecto introducido")

# Función que comprueba si tienes instalado el paquete python3-winrm
# Si no está instalado lo instala
def instala_pywinrm():
    print("instlando pywinrm")

# Función que comprueba si estas unido al dominio
def unido_Dominio(dominio):
    unido = False
    comando = "net ads info"
    salida = subprocess.check_output(comando, shell=True)
    salida = salida.decode("utf-8")
    
    # Buscamos el grupo en el texto de salida de getent group
    patron_realm = re.compile(r'Realm:\s+(\S+)')
    coincidencia = patron_realm.search(salida)
    
    if coincidencia:
        unido = True
    return unido
    
    
# Función que comprueba si el grupo que le pasemos existe en AD (devuelve true o fale)
def existe_grupo(grupo):
    existe = False
    comando = "getent group"
    grupos = subprocess.check_output(comando, shell=True)
    grupos = grupos.decode("utf-8")
    
    # Utilizar expresión regular para buscar el grupo en la salida
    patron_grupo = re.compile(rf'^{re.escape(grupo)}(?=:)')
    coincidencia = patron_grupo.search(grupos)
    
    if coincidencia:
        existe = True
    return existe
    
    
    
# Función que crea el grupo en AD
def crea_grupo_remoto(grupo):
    # Nos conectamos por winrm a la DC (suponemos que somos trusted en el DC)
    s = winrm.Session('serverad.navidad.com', auth=('Administrador', 'Departamento1!'))
    r = s.run_cmd('ipconfig', ['/all'])
    return r

#--------------------------------------------------------------------------
# VARIABLES

# Comprobamos que los argumentos se hayan introducido correctamente
if len(sys.argv) != 3 or type(sys.argv[1]) != str or type(sys.argv[2]) != str:
    print("Error en los argumentos. USO -> recurso <nombre_recurso> <grupo>")
    exit(1)

RECURSO = sys.argv[1]
GRUPO = sys.argv[2]
LOG = "/var/log/log_creacion_recursos"
fecha_hora = (str(get_datetime()).split('.'))[0].replace(":", "·")

# si estamos unidos al dominio

# Comprobamos si el grupo especificado existe
#if not existe_grupo(GRUPO):
#    crea_grupo_remoto(GRUPO)

if unido_Dominio("NAVIDAD.COM"):
    print ("unido")
else:
    print("no unido")

if existe_grupo(GRUPO):
    print ("existe")
else:
    print("no existe")
# Platilla para añadir al fichero smb.conf
SMB_RECURSO = f"""
[{RECURSO}]
comment = "Recurso compartido samba"
path = /opt/{RECURSO}
browsable = yes
writable = yes
guest ok = yes
create mask = 0770
read only = no
valid users = @{GRUPO}
"""

print (SMB_RECURSO)