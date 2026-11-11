/**
 * ==============================================================================
 * Sistema de Controlo de Stock de Componentes Eletrónicos - Eletro Kurumin
 * Servidor Principal Node.js / Express
 * Base de Dados: eletro_kurumin_db (MySQL / MariaDB via HeidiSQL)
 * ==============================================================================
 */

const express = require('express');
const session = require('express-session');
const flash = require('connect-flash');
const bcrypt = require('bcryptjs');
const path = require('path');
const db = require('./config/db');

const app = express();
const PORT = process.env.PORT || 3000;

// Configuração do motor de templates EJS
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Middlewares essenciais
app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

app.use(session({
  secret: process.env.SECRET_KEY || 'eletro_kurumin_chave_node_2026',
  resave: false,
  saveUninitialized: false,
  cookie: { maxAge: 1000 * 60 * 60 * 24 } // 24 horas
}));

app.use(flash());

// Funções auxiliares de formatação para os templates (Formato Brasileiro R$)
const helpers = {
  formatCurrency: (val) => {
    const num = parseFloat(val) || 0;
    return 'R$ ' + num.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  },
  formatNumber: (val) => {
    const num = parseInt(val, 10) || 0;
    return num.toLocaleString('pt-BR');
  }
};

// Middleware para disponibilizar variáveis globais em todas as views
app.use((req, res, next) => {
  res.locals.currentUser = req.session.usuario || null;
  res.locals.helpers = helpers;
  res.locals.activeNav = '';

  // Transformar mensagens flash em array uniforme
  const messages = [];
  ['success', 'danger', 'warning', 'info'].forEach(type => {
    const list = req.flash(type);
    list.forEach(text => messages.push({ type, text }));
  });
  res.locals.messages = messages;
  next();
});

// Middleware de proteção de rotas privadas
function requireAuth(req, res, next) {
  if (!req.session.usuario) {
    req.flash('warning', 'Por favor, inicie sessão para aceder a esta funcionalidade.');
    return res.redirect('/login?next=' + encodeURIComponent(req.originalUrl));
  }
  next();
}

// ==============================================================================
// 1. AUTENTICAÇÃO (Login, Logout e Registo)
// ==============================================================================

app.get('/login', (req, res) => {
  if (req.session.usuario) return res.redirect('/componentes');
  res.render('login', {
    title: 'Iniciar Sessão - Eletro Kurumin',
    email: '',
    redirectUrl: req.query.next || ''
  });
});

app.post('/login', async (req, res) => {
  const email = (req.body.email || '').trim().toLowerCase();
  const senha = (req.body.senha || '').trim();

  if (!email || !senha) {
    req.flash('danger', 'Preencha tanto o e-mail como a palavra-passe.');
    return res.render('login', { title: 'Iniciar Sessão', email, redirectUrl: req.query.next || '' });
  }

  try {
    const [rows] = await db.query(
      'SELECT id, nome, email, senha_hash FROM usuarios WHERE email = ?',
      [email]
    );

    if (rows.length === 0) {
      req.flash('danger', 'E-mail ou palavra-passe incorretos.');
      return res.render('login', { title: 'Iniciar Sessão', email, redirectUrl: req.query.next || '' });
    }

    const usuario = rows[0];
    let senhaValida = false;

    // Verificar se o hash é bcrypt ou suportar hash do admin
    if (usuario.senha_hash.startsWith('$2a$') || usuario.senha_hash.startsWith('$2b$')) {
      senhaValida = await bcrypt.compare(senha, usuario.senha_hash);
    } else if (usuario.email === 'admin@kurumin.com' && senha === 'admin123') {
      senhaValida = true;
      // Atualizar para bcrypt
      const novoHash = await bcrypt.hash(senha, 10);
      await db.query('UPDATE usuarios SET senha_hash = ? WHERE id = ?', [novoHash, usuario.id]);
    }

    if (!senhaValida) {
      req.flash('danger', 'E-mail ou palavra-passe incorretos.');
      return res.render('login', { title: 'Iniciar Sessão', email, redirectUrl: req.query.next || '' });
    }

    req.session.usuario = {
      id: usuario.id,
      nome: usuario.nome,
      email: usuario.email
    };

    req.flash('success', `Bem-vindo(a), ${usuario.nome}!`);
    const nextUrl = req.query.next || '/componentes';
    res.redirect(nextUrl);

  } catch (err) {
    console.error('Erro no login:', err);
    req.flash('danger', 'Erro de ligação à base de dados MySQL (HeidiSQL).');
    res.render('login', { title: 'Iniciar Sessão', email, redirectUrl: req.query.next || '' });
  }
});

app.get('/registo', (req, res) => {
  res.render('registo', { title: 'Registo de Utilizador', nome: '', email: '' });
});

app.post('/registo', async (req, res) => {
  const nome = (req.body.nome || '').trim();
  const email = (req.body.email || '').trim().toLowerCase();
  const senha = req.body.senha || '';
  const confirmarSenha = req.body.confirmar_senha || '';

  if (!nome || !email || !senha) {
    req.flash('danger', 'Todos os campos são obrigatórios.');
    return res.render('registo', { title: 'Registo', nome, email });
  }

  if (senha.length < 6) {
    req.flash('warning', 'A palavra-passe deve ter pelo menos 6 caracteres.');
    return res.render('registo', { title: 'Registo', nome, email });
  }

  if (senha !== confirmarSenha) {
    req.flash('danger', 'A confirmação da palavra-passe não coincide.');
    return res.render('registo', { title: 'Registo', nome, email });
  }

  try {
    const [existente] = await db.query('SELECT id FROM usuarios WHERE email = ?', [email]);
    if (existente.length > 0) {
      req.flash('warning', 'Já existe um utilizador registado com este e-mail.');
      return res.render('registo', { title: 'Registo', nome, email });
    }

    const hash = await bcrypt.hash(senha, 10);
    await db.query('INSERT INTO usuarios (nome, email, senha_hash) VALUES (?, ?, ?)', [nome, email, hash]);

    req.flash('success', 'Registo concluído com sucesso! Já pode iniciar sessão.');
    res.redirect('/login');
  } catch (err) {
    console.error('Erro no registo:', err);
    req.flash('danger', 'Erro ao registar utilizador na base de dados.');
    res.render('registo', { title: 'Registo', nome, email });
  }
});

app.get('/logout', (req, res) => {
  req.session.destroy(() => {
    res.redirect('/login');
  });
});

// ==============================================================================
// 2. GESTÃO DE COMPONENTES (CRUD COMPLETO)
// Tabelas: componente, categoria, usuarios, movimentacao
// ==============================================================================

app.get('/', (req, res) => res.redirect('/componentes'));

app.get('/componentes', requireAuth, async (req, res) => {
  res.locals.activeNav = 'stock';
  const termo = (req.query.q || '').trim();
  const id_cat_filtro = (req.query.categoria || '').trim();

  try {
    const [categorias] = await db.query('SELECT DISTINCT id_categoria, nome FROM categoria ORDER BY nome ASC');

    let sql = `
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
    `;
    const params = [];

    if (termo) {
      sql += ' AND (c.nome LIKE ? OR c.descricao LIKE ?)';
      params.push(`%${termo}%`, `%${termo}%`);
    }

    if (id_cat_filtro) {
      sql += ' AND c.id_categoria = ?';
      params.push(id_cat_filtro);
    }

    sql += ' ORDER BY c.nome ASC';
    const [componentes] = await db.query(sql, params);

    res.render('componentes/index', {
      title: 'Stock de Componentes - Eletro Kurumin',
      componentes,
      categorias,
      termo,
      id_cat_filtro
    });

  } catch (err) {
    console.error('Erro ao listar componentes:', err);
    req.flash('danger', 'Erro ao consultar a tabela componente no HeidiSQL.');
    res.render('componentes/index', {
      title: 'Stock de Componentes',
      componentes: [],
      categorias: [],
      termo,
      id_cat_filtro
    });
  }
});

app.get('/componentes/novo', requireAuth, async (req, res) => {
  res.locals.activeNav = 'novo';
  try {
    const [categorias] = await db.query('SELECT DISTINCT id_categoria, nome FROM categoria ORDER BY nome ASC');
    res.render('componentes/form', {
      title: 'Registar Novo Componente',
      acao: 'novo',
      categorias,
      componente: {}
    });
  } catch (err) {
    req.flash('danger', 'Erro ao carregar categorias.');
    res.redirect('/componentes');
  }
});

app.post('/componentes/novo', requireAuth, async (req, res) => {
  res.locals.activeNav = 'novo';
  const { nome, id_categoria, descricao, quantidade_estoque, preco } = req.body;

  const erros = [];
  if (!nome || !nome.trim()) erros.push('O nome do componente é obrigatório.');
  if (!id_categoria) erros.push('A categoria é obrigatória.');

  const qtd = parseInt(quantidade_estoque, 10);
  if (isNaN(qtd) || qtd < 0) erros.push('A quantidade em stock não pode ser negativa (≥ 0).');

  const prc = parseFloat(String(preco).replace(',', '.'));
  if (isNaN(prc) || prc < 0) erros.push('O preço unitário não pode ser negativo (≥ 0,00).');

  const [categorias] = await db.query('SELECT DISTINCT id_categoria, nome FROM categoria ORDER BY nome ASC');

  if (erros.length > 0) {
    erros.forEach(e => req.flash('danger', e));
    return res.render('componentes/form', {
      title: 'Registar Novo Componente',
      acao: 'novo',
      categorias,
      componente: req.body
    });
  }

  try {
    // Inserção na tabela componente conforme o diagrama
    const [result] = await db.query(
      `INSERT INTO componente (id_categoria, id_usuario, nome, descricao, preco, quantidade_estoque)
       VALUES (?, ?, ?, ?, ?, ?)`,
      [id_categoria, req.session.usuario.id, nome.trim(), (descricao || '').trim(), prc, qtd]
    );

    // Se houver stock inicial, registrar na tabela movimentacao
    if (qtd > 0) {
      await db.query(
        `INSERT INTO movimentacao (id_componente, id_usuario, tipo, quantidade, justificativa)
         VALUES (?, ?, 'entrada', ?, 'Entrada de lote inicial ao registar componente')`,
        [result.insertId, req.session.usuario.id, qtd]
      );
    }

    req.flash('success', `Componente '${nome.trim()}' registado com sucesso no inventário!`);
    res.redirect('/componentes');

  } catch (err) {
    console.error('Erro ao criar componente:', err);
    req.flash('danger', 'Erro ao gravar componente na base de dados.');
    res.render('componentes/form', {
      title: 'Registar Novo Componente',
      acao: 'novo',
      categorias,
      componente: req.body
    });
  }
});

app.get('/componentes/:id/editar', requireAuth, async (req, res) => {
  res.locals.activeNav = 'stock';
  const id = req.params.id;

  try {
    const [categorias] = await db.query('SELECT DISTINCT id_categoria, nome FROM categoria ORDER BY nome ASC');
    const [rows] = await db.query('SELECT * FROM componente WHERE id_componente = ?', [id]);

    if (rows.length === 0) {
      req.flash('warning', 'Componente não encontrado.');
      return res.redirect('/componentes');
    }

    res.render('componentes/form', {
      title: 'Editar Componente',
      acao: 'editar',
      id_componente: id,
      categorias,
      componente: rows[0]
    });
  } catch (err) {
    req.flash('danger', 'Erro ao carregar dados do componente.');
    res.redirect('/componentes');
  }
});

app.post('/componentes/:id/editar', requireAuth, async (req, res) => {
  res.locals.activeNav = 'stock';
  const id = req.params.id;
  const { nome, id_categoria, descricao, quantidade_estoque, preco } = req.body;

  const erros = [];
  if (!nome || !nome.trim()) erros.push('O nome é obrigatório.');
  if (!id_categoria) erros.push('A categoria é obrigatória.');

  const qtd = parseInt(quantidade_estoque, 10);
  if (isNaN(qtd) || qtd < 0) erros.push('A quantidade não pode ser negativa.');

  const prc = parseFloat(String(preco).replace(',', '.'));
  if (isNaN(prc) || prc < 0) erros.push('O preço não pode ser negativo.');

  const [categorias] = await db.query('SELECT DISTINCT id_categoria, nome FROM categoria ORDER BY nome ASC');

  if (erros.length > 0) {
    erros.forEach(e => req.flash('danger', e));
    return res.render('componentes/form', {
      title: 'Editar Componente',
      acao: 'editar',
      id_componente: id,
      categorias,
      componente: req.body
    });
  }

  try {
    await db.query(
      `UPDATE componente 
       SET id_categoria = ?, id_usuario = ?, nome = ?, descricao = ?, preco = ?, quantidade_estoque = ?
       WHERE id_componente = ?`,
      [id_categoria, req.session.usuario.id, nome.trim(), (descricao || '').trim(), prc, qtd, id]
    );

    req.flash('success', `Componente '${nome.trim()}' atualizado com sucesso!`);
    res.redirect('/componentes');
  } catch (err) {
    console.error('Erro ao editar:', err);
    req.flash('danger', 'Erro ao atualizar dados no HeidiSQL.');
    res.redirect('/componentes');
  }
});

app.post('/componentes/:id/eliminar', requireAuth, async (req, res) => {
  const id = req.params.id;
  try {
    const [rows] = await db.query('SELECT nome FROM componente WHERE id_componente = ?', [id]);
    if (rows.length > 0) {
      await db.query('DELETE FROM componente WHERE id_componente = ?', [id]);
      req.flash('info', `Componente '${rows[0].nome}' eliminado do inventário.`);
    }
  } catch (err) {
    console.error('Erro ao eliminar:', err);
    req.flash('danger', 'Erro ao eliminar componente.');
  }
  res.redirect('/componentes');
});

app.post('/componentes/:id/movimentar', requireAuth, async (req, res) => {
  const id = req.params.id;
  const tipo = (req.body.tipo || '').toLowerCase();
  const quantidade = parseInt(req.body.quantidade, 10);
  const justificativa = (req.body.justificativa || '').trim();

  if (isNaN(quantidade) || quantidade <= 0) {
    req.flash('danger', 'A quantidade para movimentação deve ser maior que zero.');
    return res.redirect('/componentes');
  }

  if (tipo !== 'entrada' && tipo !== 'saida') {
    req.flash('danger', 'Tipo de movimentação inválido.');
    return res.redirect('/componentes');
  }

  try {
    const [rows] = await db.query('SELECT nome, quantidade_estoque FROM componente WHERE id_componente = ?', [id]);
    if (rows.length === 0) {
      req.flash('warning', 'Componente não encontrado.');
      return res.redirect('/componentes');
    }

    const comp = rows[0];
    const estoqueAtual = comp.quantidade_estoque;

    if (tipo === 'saida' && quantidade > estoqueAtual) {
      req.flash('danger', `Stock insuficiente! Disponível: ${estoqueAtual} un, solicitada saída de ${quantidade} un.`);
      return res.redirect('/componentes');
    }

    const novoEstoque = tipo === 'entrada' ? estoqueAtual + quantidade : estoqueAtual - quantidade;

    // Atualizar tabela componente
    await db.query('UPDATE componente SET quantidade_estoque = ? WHERE id_componente = ?', [novoEstoque, id]);

    // Gravar na tabela movimentacao
    await db.query(
      `INSERT INTO movimentacao (id_componente, id_usuario, tipo, quantidade, justificativa)
       VALUES (?, ?, ?, ?, ?)`,
      [id, req.session.usuario.id, tipo, quantidade, justificativa || null]
    );

    const label = tipo === 'entrada' ? 'Entrada' : 'Saída';
    req.flash('success', `${label} de ${quantidade} un do componente '${comp.nome}' registada com sucesso!`);

  } catch (err) {
    console.error('Erro na movimentação:', err);
    req.flash('danger', 'Erro ao processar movimentação de stock.');
  }

  res.redirect('/componentes');
});

// ==============================================================================
// 3. RELATÓRIOS (Última funcionalidade a ser entregue na solução)
// ==============================================================================

app.get('/relatorios', requireAuth, async (req, res) => {
  res.locals.activeNav = 'relatorios';

  try {
    // 1. Métricas Globais (Valor Total = SUM(quantidade_estoque * preco))
    const [globais] = await db.query(`
      SELECT 
        COUNT(*) AS total_itens_distintos,
        COALESCE(SUM(quantidade_estoque), 0) AS unidades_totais,
        COALESCE(SUM(quantidade_estoque * preco), 0.00) AS valor_total_stock
      FROM componente
    `);
    const metricas = globais[0];

    // 2. Resumo por Categoria
    const [resumo_categorias] = await db.query(`
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
    `);

    const valorTotal = parseFloat(metricas.valor_total_stock) || 0;
    resumo_categorias.forEach(cat => {
      const v = parseFloat(cat.valor_categoria) || 0;
      cat.percentual = valorTotal > 0 ? ((v / valorTotal) * 100).toFixed(2) : '0.00';
    });

    // 3. Tabela Detalhada de Componentes
    const [itens_detalhados] = await db.query(`
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
    `);

    // 4. Itens Críticos (< 50 unidades)
    const [itens_criticos] = await db.query(`
      SELECT c.id_componente, c.nome, cat.nome AS categoria, c.quantidade_estoque
      FROM componente c
      INNER JOIN categoria cat ON c.id_categoria = cat.id_categoria
      WHERE c.quantidade_estoque < 50
      ORDER BY c.quantidade_estoque ASC
    `);

    // 5. Histórico da Tabela movimentacao
    const [movimentacoes_recentes] = await db.query(`
      SELECT 
        m.id_movimentacao,
        c.nome AS componente_nome,
        u.nome AS usuario_nome,
        DATE_FORMAT(m.data_movimentacao, '%d/%m/%Y %H:%i') AS data_formatada,
        m.tipo,
        m.quantidade,
        m.justificativa
      FROM movimentacao m
      INNER JOIN componente c ON m.id_componente = c.id_componente
      INNER JOIN usuarios u ON m.id_usuario = u.id
      ORDER BY m.data_movimentacao DESC
      LIMIT 15
    `);

    res.render('relatorios/index', {
      title: 'Relatório Detalhado de Inventário & Valores',
      metricas,
      resumo_categorias,
      itens_detalhados,
      itens_criticos,
      movimentacoes_recentes
    });

  } catch (err) {
    console.error('Erro ao gerar relatórios:', err);
    req.flash('danger', 'Erro ao processar dados analíticos do relatório.');
    res.redirect('/componentes');
  }
});

// Inicialização do Servidor
app.listen(PORT, () => {
  console.log('==========================================================');
  console.log('  Eletro Kurumin - Servidor Node.js / Express Ativo');
  console.log(`  Aceda em: http://127.0.0.1:${PORT}`);
  console.log('  Base de dados: eletro_kurumin_db (MySQL / HeidiSQL)');
  console.log('  Credenciais: admin@kurumin.com | admin123');
  console.log('==========================================================');
});

