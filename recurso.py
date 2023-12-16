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
import socket
import datetime
import winrm

#--------------------------------------------------------------------------
# FUNCIONES

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

# Función que comprueba si el grupo que le pasemos existe en AD
def existe_grupo(grupo):
    # Nos conectamos por winrm a la DC (suponemos que somos trusted en el DC)
    s = winrm.Session('serverad.navidad.com', auth=('Administrador', 'Departamento1!'))
    r = s.run_cmd('ipconfig', ['/all'])
    
        
    

# Función que crea el grupo en AD
def crea_grupo_remoto(grupo):
    print("Creando grupo")

#--------------------------------------------------------------------------
# VARIABLES

# Comprobamos que los argumentos se hayan introducido correctamente
if len(sys.argv) != 3 or type(sys.argv[1]) != str or type(sys.argv[2]) != str:
    print("Error en los argumentos. USO -> recurso <nombre_recurso> <grupo>")
    exit(1)

RECURSO = sys.argv[1]
GRUPO = sys.argv[2]
LOG = "/var/log/log_creacion_recursos"

# Comprobamos si el grupo especificado existe
if not existe_grupo(GRUPO):
    crea_grupo_remoto(GRUPO)

if not :

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
