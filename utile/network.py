import socket
import time
import pickle
# Constantes
HEADERSIZE = 10
LOCAL_IP = socket.gethostname()
PORT_SERV_CLES = 8380


def start_net_serv(ip=LOCAL_IP, port=PORT_SERV_CLES):
    """
    Démarre un socket qui écoute en mode "serveur" sur ip:port
    :param ip: l'adresse ip à utiliser
    :param port: le port à utilier
    :return: le socket créé en mode "serveur"
    """
    try:
        # Création du socket TCP
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Autorise la réutilisation immédiate de l'adresse après fermeture
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Associe le socket à l'adresse IP et au port
        server.bind((ip, port))

        # Démarre l'écoute avec une file d'attente maximale de 5 connexions
        server.listen(5)

        print(f"[INFO] Serveur en écoute sur {ip}:{port}")
        return server

    except PermissionError:
        print(f"[ERREUR] Permission refusée pour ouvrir le port {port}. "
              f"Utilisez un port > 1024 ou exécutez le programme en tant qu'administrateur/root.")

    except OSError as e:
        if e.errno == 98:
            print(f"[ERREUR] Le port {port} est déjà utilisé. "
                  f"Veuillez fermer l'application qui l'utilise ou choisir un autre port.")
        elif e.errno == 99:
            print(f"[ERREUR] L'adresse IP {ip} est invalide ou non disponible sur cette machine.")
        else:
            print(f"[ERREUR] Erreur système lors de la création du serveur : {e}")

    except Exception as e:
        print(f"[ERREUR] Erreur inattendue lors du démarrage du serveur : {e}")

    return None

def connect_to_serv(ip=LOCAL_IP, port=PORT_SERV_CLES, retry=60):
    """
    Crée un socket qui tente de se connecter sur ip:port.
    En cas d'échec, tente une nouvelle connexion après retry secondes
    :param ip: l'adresse ip où se connecter
    :param port: le port de connexion
    :param retry: le nombre de seconde à attendre avant de tenter une nouvelle connexion
    :return: le socket créé en mode "client"
    """
    try:
        while True:
            try:
                # Création du socket client TCP
                conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                # Tentative de connexion au serveur
                conn.connect((ip, port))
                print(f"[INFO] Connexion établie avec le serveur sur {ip}:{port}")
                return conn

            except ConnectionRefusedError:
                # Le serveur ne répond pas : attente avant nouvel essai
                for i in range(retry, 0, -1):
                    print(f"\r[ATTENTE] Connexion refusée. Nouvel essai dans {i} seconde(s)...", end="")
                    time.sleep(1)
                print("\r", end="")

            except TimeoutError:
                print(f"\n[ERREUR] Délai d’attente dépassé pour la connexion à {ip}:{port}. "
                      f"Nouvel essai dans {retry} seconde(s)...")
                time.sleep(retry)

            except OSError as e:
                print(f"\n[ERREUR] Erreur système lors de la connexion : {e}. "
                      f"Nouvel essai dans {retry} seconde(s)...")
                time.sleep(retry)

    except KeyboardInterrupt:
        print("\n[INTERRUPTION] Tentative de connexion interrompue par l'utilisateur.")
        return None

def send_message(s, msg=b''):
    """
    Envoi un message sur le réseau
    :param s: (socket) pour envoyer le message
    :param msg: (dictionary) message à envoyer
    :return: Néant
    """
    try:
        # Sérialisation du message
        data = pickle.dumps(msg)
        header = f"{len(data):<{HEADERSIZE}}".encode()

        # Envoi du header + message
        s.sendall(header + data)
        print(f"[INFO] Message envoyé ({len(data)} octets)")

    except ConnectionResetError:
        print("[ERREUR] Connexion réinitialisée par l'hôte distant lors de l'envoi.")
    except TimeoutError as e:
        print(f"[ERREUR] Temps d'attente dépassé lors de l'envoi du message : {e}")
    except OSError as e:
        print(f"[ERREUR] Erreur système lors de l'envoi : {e}")
    except Exception as e:
        print(f"[ERREUR] Erreur inattendue lors de l'envoi du message : {e}")

def receive_message(s):
    """
    Réceptionne un message sur le réseau
    :param s: (socket) pour réceptionner le message
    :return: (objet) réceptionné
    """
    try:
        # Lecture du header
        header = b''
        while len(header) < HEADERSIZE:
            chunk = s.recv(HEADERSIZE - len(header))
            if not chunk:
                print("[AVERTISSEMENT] Connexion fermée lors de la lecture du header.")
                return None
            header += chunk

        try:
            data_length = int(header.decode().strip())
        except ValueError:
            print(f"[ERREUR] Header reçu invalide : {header}")
            return None

        # Lecture des données sérialisées
        data = b''
        while len(data) < data_length:
            packet = s.recv(data_length - len(data))
            if not packet:
                print("[AVERTISSEMENT] Connexion fermée pendant la lecture des données.")
                return None
            data += packet

        # Désérialisation
        message = pickle.loads(data)
        print(f"[INFO] Message reçu ({data_length} octets)")
        return message

    except ConnectionResetError:
        print("[ERREUR] Connexion réinitialisée par l'hôte distant lors de la réception.")
    except TimeoutError:
        print("[ERREUR] Temps d'attente dépassé lors de la réception du message.")
    except OSError as e:
        print(f"[ERREUR] Erreur système lors de la réception : {e}")
    except Exception as e:
        print(f"[ERREUR] Erreur inattendue lors de la réception du message : {e}")

    return None
