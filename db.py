import pymysql
from pymysql.cursors import DictCursor
from config import Config

def get_db_connection():
    """
    Estabelece e devolve uma conexão à base de dados MySQL/MariaDB configurada.
    Lança exceção com mensagem clara caso o servidor não esteja acessível.
    """
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            charset=Config.DB_CHARSET,
            cursorclass=DictCursor,
            autocommit=True
        )
        return connection
    except pymysql.MySQLError as err:
        raise ConnectionError(
            f"Erro ao conectar ao banco de dados MySQL ({Config.DB_HOST}:{Config.DB_PORT}). "
            f"Certifique-se de que o serviço MySQL/MariaDB está ativo no HeidiSQL/XAMPP "
            f"e que o script 'database/schema.sql' foi executado. Detalhes: {err}"
        ) from err

def test_db_connection():
    """Testa a conectividade com o banco e retorna (status: bool, mensagem: str)."""
    try:
        conn = get_db_connection()
        conn.close()
        return True, "Conexão com MySQL/HeidiSQL estabelecida com sucesso!"
    except Exception as e:
        return False, str(e)

