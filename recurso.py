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
def configurar_recurso(recurso):
    edita = True
    
    # Si no existe el recurso lo crea
    # Buscamos el grupo en el texto de salida de getent group (le pasamos el fichero de samba en modo lectura)
    samba = open("/etc/samba/smb.conf", "r")
    patron_recurso = re.compile(rf'\[{re.escape(recurso)}\]')
    coincidencia = patron_recurso.search(samba.read())
    samba.close()
    
    # Si encuentra coincidencias, el recurso estará creado, así que no lo crea
    if coincidencia:
        edita = False
        escribir_en_log("El recurso " + recurso + " ya esta creado")
    else:
        # Lo abrimos en modo adición para que escriba debajo 
        file = open("/etc/samba/smb.conf", "a")
        file.write(SMB_RECURSO)
        file.close()
        

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
    patron_grupo = re.compile(rf"{grupo}:")
    coincidencia = patron_grupo.search(grupos)
    
    if coincidencia:
        existe = True
    return existe
    
    
# Función que crea el grupo en AD
def crea_grupo_remoto(maquina_remota, dominio, usuario, password, UnidadOrganizativa, grupo_a_crear):
    # Ruta del script de creación de grupos en el servidor AD
    RUTA_SCRIPT = r'C:\Users\Administrador\scripts\creacion_grupos.ps1'
    
    # Separamos las componentes del dominio
    componentes = dominio.split(".")

    # Obtener la primera y segunda componente
    primera_componente = componentes[0]
    
    # Nos conectamos por winrm a la DC (suponemos que somos trusted en el DC)
    session = winrm.Session(maquina_remota, auth=(usuario, password))
    
    # Ejecutamos el cmd-let remotamente para crear el grupo
    result = session.run_ps(rf'powershell.exe -File "{RUTA_SCRIPT}" -grupo "{grupo_a_crear}" -dominio "{primera_componente}"')
    
    # Manejamos la salida de PowerShell
    salida = result.std_out
    salida = salida.decode("utf-8", errors='ignore')
    
    return salida


#--------------------------------------------------------------------------
# VARIABLES

# Comprobamos que los argumentos se hayan introducido correctamente
if len(sys.argv) != 3 or type(sys.argv[1]) != str or type(sys.argv[2]) != str:
    print("Error en los argumentos. USO -> recurso <nombre_recurso> <grupo>")
    exit(1)

LOG = "/var/log/log_creacion_recursos"
RECURSO = sys.argv[1]
GRUPO = sys.argv[2]
OU = "MisGrupos"
fecha_hora = (str(get_datetime()).split('.'))[0].replace(":", "·")
DOMINIO = 'navidad.com'
SERVER = 'serverad.' + DOMINIO
USUARIO = 'Administrador'
PASSWORD = 'Departamento1!'


# Platilla para añadir al fichero smb.conf
SMB_RECURSO = f"""
[{RECURSO}]
comment = "Recurso compartido del grupo {GRUPO}"
path = /opt/{RECURSO}
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

# Si estamos en el dominio se acaba el programa
if not unido_Dominio("NAVIDAD.COM"):
    escribir_en_log("La máquina no está unida al dominio")
    exit(2)

# Si el grupo existe configura samba y si no, lo crea y después lo configura
if not existe_grupo(GRUPO):
    # LLamamos a la función que ejecuta el comando remoto por winrm
    escribir_en_log("El grupo no existe, creandolo...")
    salida_powershell = crea_grupo_remoto(SERVER, DOMINIO, USUARIO, PASSWORD, OU, GRUPO)
    escribir_en_log(salida_powershell)

# Si existe no entra en el if y configura directamente el recurso
escribir_en_log("Intentando crear recurso")
configurar_recurso(RECURSO)

# Mostramos la configuración de samba tras la ejecución del script en el log
escribir_en_log("La configuración actual de /etc/samba/smb.conf es:")
samba = open("/etc/samba/smb.conf", "r")
escribir_en_log(samba.read())

# Reiniciamos el servicio de samba
# Reiniciamos smb y nmbd
try:
    subprocess.run(["systemctl", "restart", "smbd", "nmbd"])
    escribir_en_log("Reiniciando los demonios de samba")
except:
    escribir_en_log("Fallo al reiniciar los demonios de samba")


escribir_en_log("FIN DEL PROGRAMA  (" + fecha_hora + ")")