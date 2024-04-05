from doctest import script_from_examples
from optparse import Values
import sqlite3
import os
import logging


logger      = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG) # (NOTSET,DEBUG,INFO,WARNING,ERROR,CRITICAL)

db_path 	= 'websites_log.sqlite3'

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class DB:
    def __init__(self, sql_script=None):
        """
        Initialize a new @DB instance

        :param db_path: the name of the database file.  It will be created if it doesn't exist.
        :param sql_script: (file) SQL commands to run if @sqlite3_database is not present
        """
        # Open or create db
        logger.info(f'Importing database: {db_path}')

        db_exists   = os.path.isfile(db_path)
        self.con    = sqlite3.connect(db_path)

        if not db_exists:
            self.create_db()

    def connect_db(self):
        self.con    = sqlite3.connect(db_path)

    def create_db(self):
        script      = resource_path('setup.sql')
        with open(script, 'r') as file:
            logger.info(f'Loading script {script} into database.')
            self.con.executescript(file.read())

    def get_db_data(self, query, dict=True):
        self.connect_db()

        logger.info('Running query: ' + query)
        cur = self.con.execute(query)

        headings            = [i[0] for i in cur.description]

        rows = cur.fetchall()

        # convert array to dict
        if dict:
            data=[]
            for row_nr, row in enumerate(rows):
                # add a dict
                data.append({})
                for col_nr, value in enumerate(row):
                    data[row_nr][headings[col_nr]]  = value
        #conver array of tuples to array of arrays
        else:
            data=[]
            for row_nr, row in enumerate(rows):
                # add a dict
                data.append([])
                for col_nr, value in enumerate(row):
                    data[row_nr].append(value)

        self.close_db()

        return data

    def update_db_data(self, query):
        self.connect_db()

        logger.info('Running query: ' + query)
        cur = self.con.execute(query)
        self.con.commit()

        self.close_db()

        return cur.lastrowid

    def add_db_entry(self, table, names, values):
        self.connect_db()

        query = f'INSERT INTO {table} ('+ names +') VALUES('+values+')'

        print(query)

        logger.info(query)
        cur = self.con.execute(query)
        self.con.commit()
        id  = cur.lastrowid
        
        self.close_db()

        return id

    def update_el_in_db(self, table, column, value, where):     
        self.connect_db()

        query           = f'UPDATE {table} SET {column}= "{value}" WHERE {where}'
        self.update_db_data(query)

        self.close_db()

    def close_db(self):
        self.con.close()
