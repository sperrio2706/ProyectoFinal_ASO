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
import subprocess
import datetime

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
def configurar_recurso():
    edita = True
    
    # Si no existe el recurso lo crea
    # Buscamos el grupo en el texto de salida de getent group (le pasamos el fichero de samba en modo lectura)
    samba = open("/etc/samba/smb.conf", "r")
    patron_recurso = re.compile(rf'\[{re.escape(USUARIO)}\]')
    coincidencia = patron_recurso.search(samba.read())
    samba.close()
    
    # Si encuentra coincidencias, el recurso estará creado, así que no lo crea
    if coincidencia:
        edita = False
        escribir_en_log("El recurso de " + USUARIO + " ya esta creado")
    else:
        # Lo abrimos en modo adición para que escriba debajo 
        file = open("/etc/samba/smb.conf", "a")
        file.write(SMB_RECURSO)
        file.close()
    
    
    
#--------------------------------------------------------------------------
# VARIABLES

# Comprobamos que los argumentos se hayan introducido correctamente
if len(sys.argv) != 3 or type(sys.argv[1]) != str or type(sys.argv[2]) != str:
    print("Error en los argumentos. USO -> recurso <nombre_recurso> <grupo>")
    exit(1)


LOG = "/var/log/log_creacion_recursos"
fecha_hora = (str(get_datetime()).split('.'))[0].replace(":", "·")
USUARIO = subprocess.check_output(['whoami']).decode("utf-8")  # guardamos el nombre del usuario
GRUPO = "usuarios del dominio"

# Platilla para añadir al fichero smb.conf
SMB_RECURSO = f"""
[{USUARIO}]
comment = "Recurso compartido del usuario del dominio {USUARIO}"
path = /home/{USUARIO}
create mask = 0770
read only = no
valid users = @{GRUPO}
"""

#--------------------------------------------------------------------------
# PROGRAMA 

# Generamos una cabecera para el log
cabecera = '\n' 
cabecera += '[ ' + fecha_hora + ']' + '\n'
cabecera += '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~' + '\n'  
cabecera += '@  FICHERO DE LOG [Unión al dominio]   @' + '\n' 
cabecera += '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~' + '\n'
escribir_en_log(cabecera)

# Creamos el recurso
escribir_en_log("Intentando crear recurso")
configurar_recurso()


# Reiniciamos el servicio de samba
# Reiniciamos smb y nmbd
try:
    subprocess.run(["systemctl", "restart", "smbd", "nmbd"])
    escribir_en_log("Reiniciando los demonios de samba")
except:
    escribir_en_log("Fallo al reiniciar los demonios de samba")

escribir_en_log("FIN DEL PROGRAMA  (" + fecha_hora + ")")