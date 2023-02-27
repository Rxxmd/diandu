import pymysql
from sqlalchemy import create_engine
import pandas as pd
import ipdb

class Database:
    def __init__(self, user, password, host, port, database) -> None:
        self.db_con = self.create_connection(
            user, password, host, port, database)

    def create_connection(self, user, password, host, port, database):

        sql_engine = create_engine(
            f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}', pool_recycle=3600)
        
        db_con = sql_engine.connect()
        return db_con

    def close_connection(self):
        self.db_con.close()

    def create_table(self, data, table_name):
        try:
            data.to_sql(table_name, self.db_con, if_exists='fail')

        except Exception as ex:
            print(ex)

        else:
            print(f'Table {table_name} created successfully')

    def read_table(self, table_name):
        # sql = f'select * from {table_name}'
        df = pd.read_sql(table_name, con = self.db_con)
        return df

    # def __del__(self):
    #     self.close_connection()
