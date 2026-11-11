import os

class Config:
    """Configurações centrais do sistema Eletro Kurumin."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'eletro_kurumin_chave_secreta_super_segura_2026')
    
    # Parâmetros de conexão com o servidor MySQL/MariaDB (HeidiSQL)
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')  # Padrão local típico
    DB_NAME = os.environ.get('DB_NAME', 'eletro_kurumin_db')
    DB_CHARSET = 'utf8mb4'
