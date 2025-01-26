import sqlite3
import logging
from sqlite3 import OperationalError
logger = logging.getLogger(__name__)

def raw_sql_from_file(db_cursor, filename):
	# Open and read the file as a single buffer
	fd = open(filename, 'r')
	sql_file = fd.read()
	fd.close()

	# all SQL commands (split on ';')
	sql_commands = sql_file.split(';')

	# Execute every command from the input file
	for command in sql_commands:
		# This will skip and report errors
		# For example, if the tables do not yet exist, this will skip over
		# the DROP TABLE commands
		try:
			db_cursor.execute(command)
		except:
			raise

class SQLite():
	def __init__(self, db_file_path, settings):
		self.file=db_file_path
		self.settings=settings
		self.timeout=self.settings.DB_TIMEOUT_SECONDS
		self.current_table=None
	def __enter__(self):
		self.conn = sqlite3.connect(self.file, timeout=self.timeout)
		self.cursor = self.conn.cursor()
		return self
	def __exit__(self, type, value, traceback):
		self.conn.commit()
		self.conn.close()

	def parse_dict_to_sql(self, where):
		if len(where) < 1: return ""
		q=""
		for k in where:
			q = q + f"{k}="
			if isinstance(where[k], str):
				q = q + f"'{where[k]}', "
			elif where[k] is None:
				q = q + "NULL, "
			else:
				q = q + f"{where[k]}, "
		q=q.rstrip(", ")
		return q

	def insert(self, table: str, values: dict, extra: str=""):
		self.current_table = table
		if not isinstance(values, dict):
			raise TypeError("SQL Insert Values must be in a dictionary.")
		query = f"INSERT INTO {table} ({','.join(values.keys())}) VALUES ("
		for v in values:
			if not v:
				query = query + "NULL, "
			if isinstance(v, str):
				query = query + f"'{values[v]}', "
			else:
				query = query + f"{values[v]}, "
		query = query.rstrip(", ") + f") {extra};"
		logger.debug("SQL Insert Statement: %s", query)
		try:
			self.cursor.execute(query)
		except Exception as e:
			logger.critical("Query: %s", query)
			logger.critical(e)
			raise OperationalError(e)
		self.conn.commit()

	def update(self, table: str, values: dict, where: dict):
		query=f"UPDATE {table} SET {self.parse_dict_to_sql(values)} WHERE {self.parse_dict_to_sql(where)};"
		logger.debug("SQL Update Statement: %s", query)
		try:
			self.cursor.execute(query)
		except Exception as e:
			logger.critical("Query: %s", query)
			logger.critical(e)
			raise OperationalError(e)
		self.conn.commit()
		return self.cursor.fetchall()

	def upsert(self, table: str, values: dict, on_conflict: list=None):
		if on_conflict and len(on_conflict) >= 1:
			extra_sql = "ON CONFLICT DO UPDATE SET"
			for field_key in on_conflict:
				field_value = values[field_key]
				if not field_value:
					extra_sql = f"{extra_sql} {field_key}=NULL,"
				if isinstance(field_value, str):
					extra_sql = f"{extra_sql} {field_key}='{field_value}',"
				else:
					extra_sql = f"{extra_sql} {field_key}={values[field_key]},"
			extra_sql = extra_sql.rstrip(",")
		try:
			return self.insert(table=table, values=values, extra=extra_sql)
		except:
			logger.error("Could not upsert values %s onto table %s", values, table)
			raise

	def select(self, table: str, values: None, where: dict={}):
		if not values:
			values = "*"

		query=f"SELECT {values} FROM {table}"
		where=self.parse_dict_to_sql(where)
		if where: query = f"{query} WHERE {where}"
		logger.debug("SQL Select Statement: %s", query)
		try:
			self.cursor.execute(f"{query};")
		except Exception as e:
			logger.critical("Query: %s", query)
			logger.critical(e)
			raise OperationalError(e)
		return self.cursor.fetchall()

	def delete(self, table: str, where: dict, debug=False):
		query=f"DELETE from {table} WHERE {self.parse_dict_to_sql(where)};"
		logger.debug("SQL Delete Statement: %s", query)
		try:
			self.cursor.execute(query)
		except Exception as e:
			logger.critical("Query: %s", query)
			logger.critical(e)
			raise OperationalError(e)
		return self.conn.commit()

	def show_table_schema(self, table):
		"""Return a string representing the table's CREATE"""
		try:
			cursor = self.cursor.execute(f"SELECT sql FROM sqlite_master WHERE name={table};")
		except Exception as e:
			logger.critical(e)
			raise OperationalError(e)
		sql = cursor.fetchone()[0]
		return sql

if __name__ == '__main__':
	print("You cannot execute this file directly.")
	exit(1)
