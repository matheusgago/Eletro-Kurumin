"""
==============================================================================
Sistema de Controlo de Stock de Componentes Eletrónicos - Eletro Kurumin
Base de Dados: eletro_kurumin_db (MySQL / MariaDB via HeidiSQL)
Esquema Exato:
  - categoria (id_categoria, nome, descricao)
  - usuarios (id, nome, email, senha_hash)
  - componente (id_componente, id_categoria, id_usuario, nome, descricao, preco, quantidade_estoque)
  - movimentacao (id_movimentacao, id_componente, id_usuario, data_movimentacao, tipo, quantidade, justificativa)
==============================================================================
"""

import functools
from decimal import Decimal, InvalidOperation
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql

from config import Config
from db import get_db_connection

app = Flask(__name__)
app.config.from_object(Config)


# ============================================================================
# HELPER DE SESSÃO E DECORATOR DE AUTENTICAÇÃO
# ============================================================================

def login_required(view):
    """Garante que a rota só pode ser acedida com sessão iniciada."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'usuario_id' not in session:
            flash('Por favor, inicie sessão para aceder a esta funcionalidade.', 'warning')
            return redirect(url_for('login', next=request.path))
        return view(**kwargs)
    return wrapped_view


@app.context_processor
def inject_user():
    """Disponibiliza os dados do utilizador autenticado em todos os templates."""
    return {
        'current_user': {
            'id': session.get('usuario_id'),
            'nome': session.get('usuario_nome'),
            'email': session.get('usuario_email')
        } if 'usuario_id' in session else None
    }


# ============================================================================
# 1. MÓDULO DE AUTENTICAÇÃO (Tabela: usuarios)
# ============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Autenticação com e-mail e palavra-passe (hash seguro)."""
    if 'usuario_id' in session:
        return redirect(url_for('listar_componentes'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '').strip()

        if not email or not senha:
            flash('Preencha tanto o e-mail como a palavra-passe.', 'danger')
            return render_template('login.html', email=email)

        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, nome, email, senha_hash FROM usuarios WHERE email = %s",
                    (email,)
                )
                usuario = cursor.fetchone()
            conn.close()

            if usuario and check_password_hash(usuario['senha_hash'], senha):
                session.clear()
                session['usuario_id'] = usuario['id']
                session['usuario_nome'] = usuario['nome']
                session['usuario_email'] = usuario['email']
                flash(f'Bem-vindo(a), {usuario["nome"]}!', 'success')
                
                next_url = request.args.get('next')
                return redirect(next_url or url_for('listar_componentes'))
            else:
                flash('E-mail ou palavra-passe incorretos. Verifique os dados.', 'danger')

        except ConnectionError as ce:
            flash(str(ce), 'danger')
        except Exception as e:
            flash(f'Erro de sistema durante a autenticação: {e}', 'danger')

    return render_template('login.html')


@app.route('/registo', methods=['GET', 'POST'])
def registo():
    """Registo de novos colaboradores na tabela 'usuarios'."""
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')

        if not nome or not email or not senha:
            flash('Todos os campos são de preenchimento obrigatório.', 'danger')
            return render_template('registo_usuario.html', nome=nome, email=email)

        if len(senha) < 6:
            flash('A palavra-passe deve conter pelo menos 6 caracteres.', 'warning')
            return render_template('registo_usuario.html', nome=nome, email=email)

        if senha != confirmar_senha:
            flash('A confirmação da palavra-passe não coincide.', 'danger')
            return render_template('registo_usuario.html', nome=nome, email=email)

        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
                if cursor.fetchone():
                    flash('Já existe um utilizador registado com este e-mail.', 'warning')
                    conn.close()
                    return render_template('registo_usuario.html', nome=nome, email=email)

                hash_seguro = generate_password_hash(senha, method='pbkdf2:sha256')
                cursor.execute(
                    "INSERT INTO usuarios (nome, email, senha_hash) VALUES (%s, %s, %s)",
                    (nome, email, hash_seguro)
                )
            conn.close()

            flash('Registo efetuado com sucesso! Já pode iniciar sessão.', 'success')
            return redirect(url_for('login'))

        except ConnectionError as ce:
            flash(str(ce), 'danger')
        except Exception as e:
            flash(f'Erro ao registar utilizador: {e}', 'danger')

    return render_template('registo_usuario.html')


@app.route('/logout')
def logout():
    """Encerra a sessão do utilizador."""
    session.clear()
    flash('A sua sessão foi encerrada com sucesso.', 'info')
    return redirect(url_for('login'))


# ============================================================================
# 2. GESTÃO DE COMPONENTES (CRUD COMPLETO)
# Tabelas: componente, categoria, usuarios, movimentacao
# ============================================================================

@app.route('/')
@app.route('/componentes')
@login_required
def listar_componentes():
    """
    R (Read): Lista os componentes com JOIN na tabela 'categoria' e 'usuarios'.
    Subtotal calculado: quantidade_estoque * preco.
    """
    termo = request.args.get('q', '').strip()
    id_cat_filtro = request.args.get('categoria', '').strip()

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Lista de categorias para o dropdown de filtro
            cursor.execute("SELECT DISTINCT id_categoria, nome FROM categoria ORDER BY nome ASC")
            categorias_existentes = cursor.fetchall()

            query = """
                SELECT 
                    c.id_componente,
                    c.id_categoria,
                    c.id_usuario,
                    c.nome,
                    c.descricao,
                    c.preco,
                    c.quantidade_estoque,
                    cat.nome AS nome_categoria,
                    u.nome AS nome_usuario,
                    (c.quantidade_estoque * c.preco) AS subtotal
                FROM componente c
                INNER JOIN categoria cat ON c.id_categoria = cat.id_categoria
                INNER JOIN usuarios u ON c.id_usuario = u.id
                WHERE 1=1
            """
            params = []

            if termo:
                query += " AND (c.nome LIKE %s OR c.descricao LIKE %s)"
                termo_like = f"%{termo}%"
                params.extend([termo_like, termo_like])

            if id_cat_filtro:
                query += " AND c.id_categoria = %s"
                params.append(id_cat_filtro)

            query += " ORDER BY c.nome ASC"
            cursor.execute(query, params)
            componentes = cursor.fetchall()

        conn.close()
        return render_template(
            'componentes/index.html',
            componentes=componentes,
            termo=termo,
            id_cat_filtro=id_cat_filtro,
            categorias_existentes=categorias_existentes
        )
    except ConnectionError as ce:
        flash(str(ce), 'danger')
        return render_template('componentes/index.html', componentes=[], termo=termo, id_cat_filtro=id_cat_filtro, categorias_existentes=[])
    except Exception as e:
        flash(f'Erro ao carregar componentes: {e}', 'danger')
        return render_template('componentes/index.html', componentes=[], termo=termo, id_cat_filtro=id_cat_filtro, categorias_existentes=[])


@app.route('/componentes/novo', methods=['GET', 'POST'])
@login_required
def criar_componente():
    """C (Create): Insere um novo componente vinculado à categoria e ao utilizador logado."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT DISTINCT id_categoria, nome FROM categoria ORDER BY nome ASC")
        categorias = cursor.fetchall()

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        id_categoria_str = request.form.get('id_categoria', '').strip()
        descricao = request.form.get('descricao', '').strip()
        quantidade_str = request.form.get('quantidade_estoque', '').strip()
        preco_str = request.form.get('preco', '').strip().replace(',', '.')

        erros = []
        if not nome:
            erros.append("O nome do componente é obrigatório.")
        if not id_categoria_str:
            erros.append("A categoria do componente é obrigatória.")

        try:
            quantidade_estoque = int(quantidade_str)
            if quantidade_estoque < 0:
                erros.append("A quantidade em stock não pode ser negativa (≥ 0).")
        except (ValueError, TypeError):
            erros.append("A quantidade em stock deve ser um número inteiro válido.")
            quantidade_estoque = 0

        try:
            preco = Decimal(preco_str)
            if preco < Decimal('0.00'):
                erros.append("O preço unitário não pode ser negativo (≥ 0,00).")
        except (InvalidOperation, TypeError):
            erros.append("O preço deve ser um valor numérico válido (ex: 1.50).")
            preco = Decimal('0.00')

        if erros:
            for erro in erros:
                flash(erro, 'danger')
            conn.close()
            return render_template(
                'componentes/form.html',
                acao='novo',
                categorias=categorias,
                componente={
                    'nome': nome,
                    'id_categoria': id_categoria_str,
                    'descricao': descricao,
                    'quantidade_estoque': quantidade_str,
                    'preco': preco_str
                }
            )

        try:
            with conn.cursor() as cursor:
                # Inserção no banco conforme o diagrama
                cursor.execute("""
                    INSERT INTO componente 
                        (id_categoria, id_usuario, nome, descricao, preco, quantidade_estoque)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (id_categoria_str, session['usuario_id'], nome, descricao, preco, quantidade_estoque))
                
                novo_id = cursor.lastrowid

                # Se houver stock inicial, registrar automaticamente na tabela 'movimentacao'
                if quantidade_estoque > 0:
                    cursor.execute("""
                        INSERT INTO movimentacao
                            (id_componente, id_usuario, tipo, quantidade, justificativa)
                        VALUES (%s, %s, 'entrada', %s, 'Entrada de saldo inicial ao cadastrar componente')
                    """, (novo_id, session['usuario_id'], quantidade_estoque))

            conn.close()
            flash(f"Componente '{nome}' registado com sucesso no inventário!", 'success')
            return redirect(url_for('listar_componentes'))

        except Exception as e:
            flash(f"Erro ao registar componente: {e}", 'danger')

    conn.close()
    return render_template('componentes/form.html', acao='novo', categorias=categorias, componente={})


@app.route('/componentes/<int:id_componente>/editar', methods=['GET', 'POST'])
@login_required
def editar_componente(id_componente):
    """U (Update): Edição dos dados do componente."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT DISTINCT id_categoria, nome FROM categoria ORDER BY nome ASC")
            categorias = cursor.fetchall()

            cursor.execute("SELECT * FROM componente WHERE id_componente = %s", (id_componente,))
            componente = cursor.fetchone()

        if not componente:
            flash('Componente eletrónico não encontrado.', 'warning')
            conn.close()
            return redirect(url_for('listar_componentes'))

        if request.method == 'POST':
            nome = request.form.get('nome', '').strip()
            id_categoria_str = request.form.get('id_categoria', '').strip()
            descricao = request.form.get('descricao', '').strip()
            quantidade_str = request.form.get('quantidade_estoque', '').strip()
            preco_str = request.form.get('preco', '').strip().replace(',', '.')

            erros = []
            if not nome:
                erros.append("O nome é obrigatório.")
            if not id_categoria_str:
                erros.append("A categoria é obrigatória.")

            try:
                quantidade_estoque = int(quantidade_str)
                if quantidade_estoque < 0:
                    erros.append("A quantidade em stock não pode ser negativa.")
            except (ValueError, TypeError):
                erros.append("Quantidade inválida.")
                quantidade_estoque = 0

            try:
                preco = Decimal(preco_str)
                if preco < Decimal('0.00'):
                    erros.append("O preço não pode ser negativo.")
            except (InvalidOperation, TypeError):
                erros.append("Preço inválido.")
                preco = Decimal('0.00')

            if erros:
                for erro in erros:
                    flash(erro, 'danger')
                return render_template(
                    'componentes/form.html',
                    acao='editar',
                    categorias=categorias,
                    componente=request.form,
                    id_componente=id_componente
                )

            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE componente 
                    SET id_categoria = %s, id_usuario = %s, nome = %s,
                        descricao = %s, preco = %s, quantidade_estoque = %s
                    WHERE id_componente = %s
                """, (id_categoria_str, session['usuario_id'], nome, descricao, preco, quantidade_estoque, id_componente))

            conn.close()
            flash(f"Componente '{nome}' atualizado com sucesso!", 'success')
            return redirect(url_for('listar_componentes'))

        conn.close()
        return render_template(
            'componentes/form.html',
            acao='editar',
            categorias=categorias,
            componente=componente,
            id_componente=id_componente
        )

    except Exception as e:
        flash(f'Erro ao atualizar componente: {e}', 'danger')
        return redirect(url_for('listar_componentes'))


@app.route('/componentes/<int:id_componente>/eliminar', methods=['POST'])
@login_required
def eliminar_componente(id_componente):
    """D (Delete): Elimina o componente da tabela 'componente'."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT nome FROM componente WHERE id_componente = %s", (id_componente,))
            comp = cursor.fetchone()
            if comp:
                cursor.execute("DELETE FROM componente WHERE id_componente = %s", (id_componente,))
                flash(f"Componente '{comp['nome']}' eliminado do stock.", 'info')
            else:
                flash("Componente não encontrado para eliminação.", 'warning')
        conn.close()
    except Exception as e:
        flash(f"Erro ao eliminar componente: {e}", 'danger')

    return redirect(url_for('listar_componentes'))


@app.route('/componentes/<int:id_componente>/movimentar', methods=['POST'])
@login_required
def movimentar_componente(id_componente):
    """Registra uma movimentação (entrada ou saída) na tabela 'movimentacao' e atualiza o stock."""
    tipo = request.form.get('tipo', '').strip().lower()
    quantidade_str = request.form.get('quantidade', '').strip()
    justificativa = request.form.get('justificativa', '').strip()

    try:
        quantidade = int(quantidade_str)
        if quantidade <= 0:
            flash("A quantidade para movimentação deve ser maior que zero.", 'danger')
            return redirect(url_for('listar_componentes'))
    except (ValueError, TypeError):
        flash("Quantidade de movimentação inválida.", 'danger')
        return redirect(url_for('listar_componentes'))

    if tipo not in ['entrada', 'saida']:
        flash("Tipo de movimentação inválido (use entrada ou saida).", 'danger')
        return redirect(url_for('listar_componentes'))

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT nome, quantidade_estoque FROM componente WHERE id_componente = %s", (id_componente,))
            comp = cursor.fetchone()
            if not comp:
                flash("Componente não encontrado.", 'warning')
                conn.close()
                return redirect(url_for('listar_componentes'))

            estoque_atual = comp['quantidade_estoque']

            if tipo == 'saida' and quantidade > estoque_atual:
                flash(f"Stock insuficiente! Disponível: {estoque_atual} un, solicitada saída de {quantidade} un.", 'danger')
                conn.close()
                return redirect(url_for('listar_componentes'))

            # Calcular novo estoque
            novo_estoque = estoque_atual + quantidade if tipo == 'entrada' else estoque_atual - quantidade

            # Atualizar estoque no componente
            cursor.execute(
                "UPDATE componente SET quantidade_estoque = %s WHERE id_componente = %s",
                (novo_estoque, id_componente)
            )

            # Inserir registro na tabela movimentacao conforme o diagrama
            cursor.execute("""
                INSERT INTO movimentacao (id_componente, id_usuario, tipo, quantidade, justificativa)
                VALUES (%s, %s, %s, %s, %s)
            """, (id_componente, session['usuario_id'], tipo, quantidade, justificativa or None))

        conn.close()
        tipo_label = "Entrada" if tipo == 'entrada' else "Saída"
        flash(f"{tipo_label} de {quantidade} un do componente '{comp['nome']}' realizada com sucesso!", 'success')
    except Exception as e:
        flash(f"Erro ao registar movimentação: {e}", 'danger')

    return redirect(url_for('listar_componentes'))


# ============================================================================
# 3. RELATÓRIOS (Última funcionalidade a ser entregue na solução)
# ============================================================================

@app.route('/relatorios')
@login_required
def relatorios():
    """
    Apresenta o relatório detalhado com:
    - VALOR TOTAL DOS ITENS EM STOCK (Soma de quantidade_estoque * preco)
    - Totais de unidades e modelos
    - Resumo por Categoria
    - Relatório Analítico Detalhado de Componentes com Subtotais
    - Histórico das Últimas Movimentações (tabela movimentacao)
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 1. Indicadores Globais e Valor Total do Stock
            cursor.execute("""
                SELECT 
                    COUNT(*) AS total_itens_distintos,
                    COALESCE(SUM(quantidade_estoque), 0) AS unidades_totais,
                    COALESCE(SUM(quantidade_estoque * preco), 0.00) AS valor_total_stock
                FROM componente
            """)
            metricas_globais = cursor.fetchone()

            # 2. Resumo por Categoria
            cursor.execute("""
                SELECT 
                    cat.id_categoria,
                    cat.nome AS categoria,
                    COUNT(c.id_componente) AS total_modelos,
                    COALESCE(SUM(c.quantidade_estoque), 0) AS total_unidades,
                    COALESCE(SUM(c.quantidade_estoque * c.preco), 0.00) AS valor_categoria
                FROM categoria cat
                LEFT JOIN componente c ON cat.id_categoria = c.id_categoria
                GROUP BY cat.id_categoria, cat.nome
                HAVING total_modelos > 0
                ORDER BY valor_categoria DESC
            """)
            resumo_categorias = cursor.fetchall()

            # 3. Relatório Detalhado de Todos os Componentes
            cursor.execute("""
                SELECT 
                    c.id_componente,
                    c.nome,
                    c.descricao,
                    cat.nome AS categoria,
                    u.nome AS usuario_responsavel,
                    c.quantidade_estoque,
                    c.preco,
                    (c.quantidade_estoque * c.preco) AS subtotal
                FROM componente c
                INNER JOIN categoria cat ON c.id_categoria = cat.id_categoria
                INNER JOIN usuarios u ON c.id_usuario = u.id
                ORDER BY subtotal DESC, c.nome ASC
            """)
            itens_detalhados = cursor.fetchall()

            # 4. Alertas de Stock Baixo (< 50 unidades)
            cursor.execute("""
                SELECT c.id_componente, c.nome, cat.nome AS categoria, c.quantidade_estoque
                FROM componente c
                INNER JOIN categoria cat ON c.id_categoria = cat.id_categoria
                WHERE c.quantidade_estoque < 50
                ORDER BY c.quantidade_estoque ASC
            """)
            itens_criticos = cursor.fetchall()

            # 5. Histórico Recente de Movimentações (Tabela: movimentacao)
            cursor.execute("""
                SELECT 
                    m.id_movimentacao,
                    c.nome AS componente_nome,
                    u.nome AS usuario_nome,
                    m.data_movimentacao,
                    m.tipo,
                    m.quantidade,
                    m.justificativa
                FROM movimentacao m
                INNER JOIN componente c ON m.id_componente = c.id_componente
                INNER JOIN usuarios u ON m.id_usuario = u.id
                ORDER BY m.data_movimentacao DESC
                LIMIT 15
            """)
            movimentacoes_recentes = cursor.fetchall()

        conn.close()

        # Calcular percentuais por categoria
        valor_total = float(metricas_globais['valor_total_stock'])
        for cat in resumo_categorias:
            cat_val = float(cat['valor_categoria'])
            cat['percentual'] = round((cat_val / valor_total * 100), 2) if valor_total > 0 else 0

        return render_template(
            'relatorios/index.html',
            metricas=metricas_globais,
            resumo_categorias=resumo_categorias,
            itens_detalhados=itens_detalhados,
            itens_criticos=itens_criticos,
            movimentacoes_recentes=movimentacoes_recentes
        )

    except ConnectionError as ce:
        flash(str(ce), 'danger')
        return render_template('relatorios/index.html', metricas={}, resumo_categorias=[], itens_detalhados=[], itens_criticos=[], movimentacoes_recentes=[])
    except Exception as e:
        flash(f'Erro ao gerar relatório de stock: {e}', 'danger')
        return render_template('relatorios/index.html', metricas={}, resumo_categorias=[], itens_detalhados=[], itens_criticos=[], movimentacoes_recentes=[])


# ============================================================================
# FILTROS PERSONALIZADOS PARA JINJA2
# ============================================================================

@app.template_filter('moeda')
def formato_moeda(valor):
    """Formata valores monetários (€ 1.234,56)."""
    if valor is None:
        return "€ 0,00"
    try:
        val = float(valor)
        formatado = f"{val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return f"€ {formatado}"
    except (ValueError, TypeError):
        return str(valor)


@app.template_filter('numero')
def formato_numero(valor):
    """Formata contagens com separador de milhares."""
    if valor is None:
        return "0"
    try:
        return f"{int(valor):,}".replace(',', '.')
    except (ValueError, TypeError):
        return str(valor)


if __name__ == '__main__':
    print("==========================================================")
    print("  Eletro Kurumin - Sistema de Controlo de Stock Ativo")
    print("  Base de dados: eletro_kurumin_db (Tabelas do Diagrama)")
    print("  Aceda em: http://127.0.0.1:5000")
    print("  Credenciais padrão: admin@kurumin.com | admin123")
    print("==========================================================")
    app.run(host='127.0.0.1', port=5000, debug=True)
