# 📅 Sistemática de Manutenção – Django + Docker

Sistema web para controle de sistemáticas de manutenção, inspeções, ajustes e medições em linhas de produção.  
Desenvolvido em **Django** e **PostgreSQL**, com suporte a execução via **Docker Compose** e pronto para deploy no **Azure App Service**.

---

## 🚀 Funcionalidades

- 📆 **Calendário interativo** para visualização das sistemáticas programadas
- 🛠 **Cadastro e edição** de sistemáticas
- 📦 Gestão de peças associadas a cada sistemática
- 📊 Dashboard com indicadores de manutenção
- 🔐 Login, logout e controle de permissões
- 🔍 API interna para integração com outros sistemas

---

## 🏗 Tecnologias utilizadas

- **Backend:** Django 5.x, Python 3.12
- **Banco de dados:** PostgreSQL
- **Frontend:** HTML, Bootstrap, FullCalendar.js
- **Autenticação:** Django Auth (Custom Login View)
- **Deploy:** Docker, Docker Compose, Azure App Service

---

## 📂 Estrutura de pastas

```bash
.
├── core/               # App principal (views, models, urls, templates)
├── sistematica/        # Configurações do projeto
├── templates/          # Templates HTML
├── staticfiles/        # Arquivos estáticos coletados
├── Dockerfile          # Build da aplicação no container
├── docker-compose.yml  # Configuração de serviços (web + db)
├── requirements.txt    # Dependências do Python
└── README.md           # Este arquivo
