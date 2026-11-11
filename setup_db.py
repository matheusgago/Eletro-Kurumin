"""
Script utilitário para carregar/reinicializar a base de dados eletro_kurumin_db
Executa o script 'database/schema.sql' no MySQL/MariaDB local (compatível com HeidiSQL).
"""
import pymysql
from config import Config

def inicializar_banco():
    print(f"-> Conectando ao MySQL em {Config.DB_HOST}:{Config.DB_PORT} (Utilizador: {Config.DB_USER})...")
    conn = pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        autocommit=True
    )
    cursor = conn.cursor()

    print("-> Lendo 'database/schema.sql'...")
    with open('database/schema.sql', 'r', encoding='utf-8') as f:
        sql_content = f.read()

    comandos = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip()]
    for cmd in comandos:
        if cmd.strip().upper().startswith('SELECT'):
            continue
        cursor.execute(cmd)

    cursor.execute(f"SELECT COUNT(*) FROM `{Config.DB_NAME}`.`componente`")
    total_comp = cursor.fetchone()[0]

    cursor.execute(f"SELECT email FROM `{Config.DB_NAME}`.`usuarios`")
    usuarios = cursor.fetchall()

    print("\n" + "="*55)
    print(" BASE DE DADOS ATUALIZADA CONFORME O DIAGRAMA!")
    print(f" -> Base: {Config.DB_NAME}")
    print(f" -> Tabelas: categoria, componente, movimentacao, usuarios")
    print(f" -> Componentes cadastrados: {total_comp}")
    print(f" -> Utilizador administrador: {usuarios[0][0]} (Senha: admin123)")
    print("="*55 + "\n")

    conn.close()

if __name__ == '__main__':
    inicializar_banco()
