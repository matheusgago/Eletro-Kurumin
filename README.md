# Eletro Kurumin — Sistema de Controlo de Stock de Componentes Eletrónicos (Node.js)

Sistema web completo para gestão e controlo de inventário de componentes eletrónicos desenvolvido para a **Eletro Kurumin**, construído em **Node.js**, **Express**, **EJS** e **MySQL / MariaDB (gerido via HeidiSQL)** através de um `package.json` oficial.

---

## 1. Estrutura do Projeto (Node.js & Express)

```text
Eletro Kurumin/
├── config/
│   └── db.js                   # Pool de conexões assíncronas com MySQL2 (eletro_kurumin_db)
├── database/
│   └── schema.sql              # Script SQL compatível com HeidiSQL (tabelas do diagrama)
├── public/
│   └── css/
│       └── style.css           # Estilos corporativos e otimização de impressão (@media print)
├── views/
│   ├── partials/
│   │   ├── header.ejs          # Barra de navegação corporativa e alertas flash
│   │   └── footer.ejs          # Rodapé e scripts Bootstrap
│   ├── login.ejs               # Ecrã de início de sessão
│   ├── registo.ejs             # Cadastro de novos colaboradores
│   ├── componentes/
│   │   ├── index.ejs           # Listagem, busca, filtros de categoria e modais (movimentação e exclusão)
│   │   └── form.ejs            # Formulário de registo e edição de componentes
│   └── relatorios/
│       └── index.ejs           # Relatório analítico detalhado e Valor Total em Stock
├── package.json                # Ficheiro de dependências e scripts npm
├── server.js                   # Servidor Express, rotas, regras de negócio e validações
└── README.md                   # Manual de instalação e execução
```

---

## 2. Diagrama de Dados no HeidiSQL (`eletro_kurumin_db`)

A base de dados segue à risca as quatro tabelas relacionais com integridade referencial:

1. **`categoria`**: `id_categoria` (PK), `nome`, `descricao`
2. **`usuarios`**: `id` (PK), `nome`, `email`, `senha_hash` (bcrypt seguro)
3. **`componente`**: `id_componente` (PK), `id_categoria` (FK), `id_usuario` (FK), `nome`, `descricao`, `preco`, `quantidade_estoque`
4. **`movimentacao`**: `id_movimentacao` (PK), `id_componente` (FK), `id_usuario` (FK), `data_movimentacao`, `tipo` ('entrada'/'saida'), `quantidade`, `justificativa`

---

## 3. Instruções de Instalação e Execução

### Passo 1: Base de Dados no HeidiSQL
1. Abra o **HeidiSQL** e conecte-se à sua sessão local (normalmente `127.0.0.1:3306`, utilizador `root`).
2. Abra o ficheiro `database/schema.sql` (`Ctrl + O`) e carregue em **F9** para criar as tabelas e dados de teste.

### Passo 2: Instalar Dependências (`package.json`)
Abra a pasta do projeto no terminal e execute:
```bash
npm install
```

### Passo 3: Iniciar o Servidor
```bash
npm start
```
*(Ou `npm run dev` para desenvolvimento com recarregamento automático).*

Aceda à aplicação no seu navegador:  
👉 **[http://127.0.0.1:3000](http://127.0.0.1:3000)**

---

## 4. Credenciais Padrão de Teste

- **E-mail:** `admin@kurumin.com`
- **Palavra-passe:** `admin123`
