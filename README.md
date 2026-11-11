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
🥇 use: npm init -y
npm install express mysql2
Aceda à aplicação no seu navegador:  
👉 **[http://127.0.0.1:3000](http://127.0.0.1:3000)**

---

## 4. Credenciais Padrão de Teste

- **E-mail:** `admin@kurumin.com`
- **Palavra-passe:** `admin123`

---

## 5. Tabela ( banco) 
<img width="464" height="717" alt="image" src="https://github.com/user-attachments/assets/0d669328-7918-4c1f-9bbc-e04dc3d57138" />

---


## 6. HEIDESQL
<img width="276" height="111" alt="image" src="https://github.com/user-attachments/assets/e9ac698b-bf05-4e04-be94-e113aea640fd" />

<img width="723" height="99" alt="image" src="https://github.com/user-attachments/assets/a69c7f2b-58c6-4c29-97ce-b15450711ad9" />

---

##7. Testes
<img width="1247" height="619" alt="image" src="https://github.com/user-attachments/assets/1112d876-cf7a-450f-803f-2a024927819b" />
---
<img width="860" height="617" alt="image" src="https://github.com/user-attachments/assets/37e0a7c0-8be6-4bbf-99b5-93ed8a900f7a" />
---

<img width="693" height="675" alt="image" src="https://github.com/user-attachments/assets/19cded4f-605d-4aba-961c-cffefd275392" />

---
<img width="1337" height="811" alt="image" src="https://github.com/user-attachments/assets/555105a6-4606-40c0-a954-d4778a48a987" />

---
<img width="569" height="598" alt="image" src="https://github.com/user-attachments/assets/fe2af263-b0e3-4dc2-a4b7-7c4e6888deba" />


---
## 8.Postman
<img width="645" height="775" alt="image" src="https://github.com/user-attachments/assets/7e976f02-6b7f-4ca4-86a7-741bac8e0e56" />
---
<img width="804" height="878" alt="image" src="https://github.com/user-attachments/assets/2b63d6f0-1e4b-43ca-8adf-59cff3744dbd" />
<img width="703" height="326" alt="image" src="https://github.com/user-attachments/assets/32e1bd53-2e3c-45aa-beaa-1cea5484f721" />
## tem todos os itens.
---
<img width="794" height="802" alt="image" src="https://github.com/user-attachments/assets/fe95a976-fe61-48aa-8b4b-786a17fee304" />
<img width="716" height="847" alt="image" src="https://github.com/user-attachments/assets/aac10f94-82d0-41f4-9e2b-0c98b03425c1" />

---
 <img width="779" height="790" alt="image" src="https://github.com/user-attachments/assets/ded0e784-53ca-4dfa-924f-1ee963dd220b" />







