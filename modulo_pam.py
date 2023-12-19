import subprocess
import re

def pam_sm_authenticate(pamh, flags, argv):
    usuario = pamh.get_user(None)
    print (f"Comprobando si el {usuario} está en el dominio: ")
    usuarios = subprocess.check_output("getent passwd", shell = True)
    # Guardamos en una variable la salida de smb.conf
    contenido_smb = subprocess.check_output("cat /etc/samba/smb.conf", shell = True)
   
    # Buscamos coincidencias en la salida de smb
    expresion_regular = r'range\s*=\s*(\d+)-(\d+)'
    coincidencias = re.search(expresion_regular, contenido_smb)

    if coincidencias:
        idmap_inicio = coincidencias.group(1)
        idmap_fin = coincidencias.group(2)

    # Generamos un array con las lineas de la salida de getent
    passwd_lineas = usuarios.strip().split('\n')

    # Recorremos las lineas separado usuaroi e id
    for linea in passwd_lineas:
        partes = linea.split(':')
        usuario_actual = partes[0]
        uid = int(partes[2])

    # Si el usuario actual es igual al usuario y el uid está entre lo que lea
        if usuario_actual == usuario and idmap_inicio <= uid <= idmap_fin:
            return pamh.PAM_SUCCESS
    return pamh.PAM_AUTH_ERR
        
def pam_sm_open_session(pamh, flags, argv):
    return pamh.PAM_SUCCESS

def pam_sm_close_session(pamh, flags, argv):
    return pamh.PAM_SUCCESS

def pam_sm_setcred(pamh, flags, argv):
    return pamh.PAM_SUCCESS

def pam_sm_acct_mgmt(pamh, flags, argv):
    return pamh.PAM_SUCCESS

def pam_sm_chauthtok(pamh, flags, argv):
    return pamh.PAM_SUCCESS