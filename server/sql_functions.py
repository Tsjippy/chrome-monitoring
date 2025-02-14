import sqlite3
import os
import logging

logger      = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG) # (NOTSET,DEBUG,INFO,WARNING,ERROR,CRITICAL)

def resource_path(relative_path=''):
    base_path   = os.path.dirname(os.path.realpath(__file__))+'/'

    return os.path.join(base_path, relative_path)
    
db_path 	= resource_path('db.sqlite3')

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

        if db_exists and not os.access(db_path, os.W_OK):
            raise Exception("Database is not writable!")

        if not db_exists:
            self.create_db()
        else:
            self.connect_db()
    
    def __del__(self):
        self.close_db()

    def connect_db(self):
        if os.path.isfile(db_path) and not os.access(db_path, os.W_OK):
            raise Exception("Database is not writable!")
        
        self.con    = sqlite3.connect(db_path, check_same_thread=False)

    def create_db(self):
        if not os.access(resource_path(), os.W_OK):
            raise Exception("Database folder is not writable!")
        
        try:
            self.connect_db()

            script      = resource_path('setup.sql')

            with open(script, 'r') as file:
                logger.info(f'Loading script {script} into database.')
                self.con.executescript(file.read())
        except:
            print('do I have permission to write to '+db_path+'?')

    def get_db_data(self, query, dict=True):

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

        return data

    def update_db_data(self, query):

        logger.info('Running query: ' + query)

        print(query)
        
        cur = self.con.execute(query)
        self.con.commit()

        return cur.lastrowid

    def add_db_entry(self, table, names, values):
        try:

            query = f'INSERT INTO {table} ({names}) VALUES({values})'

            print(query)

            logger.info(query)
            cur = self.con.execute(query)
            self.con.commit()
            id  = cur.lastrowid

            return id
        except:
            print(f'do I have permission to write to {db_path}?')

    def update_el_in_db(self, table, column, value, where):     

        query           = f'UPDATE {table} SET {column}= "{value}" WHERE {where}'
        self.update_db_data(query)

    def close_db(self):
        self.con.close()
