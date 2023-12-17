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

# Funciñon que instala powershell
def instalar_powershell(url_paquete_powershell_deb):

    subprocess.run(['wget', url_paquete_powershell_deb])

    # Obtenemos el nombre del archivo de la URL
    fichero = os.path.basename(url_paquete_powershell_deb)

    # Instalamos Powershell
    subprocess.run(['dpkg', '-i', fichero])

    # Instalamos las dependencias que faltan
    subprocess.run(['apt-get', 'install', '-f'])

    #Borramos el fichero que hemos descargado
    os.remove(fichero)


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
    # Nos conectamos por winrm a la DC (suponemos que somos trusted en el DC)
    session = winrm.Session(maquina_remota, auth=(usuario, password))
    
    # Ejecutamos el cmd-let remotamente para crear el grupo
    result = session.run_ps(f'New-ADGroup -Name "{grupo_a_crear}" -SamAccountName "{grupo_a_crear}" -GroupCategory Security -GroupScope Global -DisplayName "{grupo_a_crear}" -Path "CN={UnidadOrganizativa},DC={dominio},DC=com" -Description "Grupo creado mediante script en debian"')
    
    # Devolvemos la salida del cmd-let en utf-8
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
create mask = 0770
read only = no
valid users = @{GRUPO}
"""

print (SMB_RECURSO)

salida_powershell = crea_grupo_remoto(SERVER, DOMINIO, USUARIO, PASSWORD, OU, GRUPO)
print(salida_powershell)