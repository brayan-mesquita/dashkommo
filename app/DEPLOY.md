# 🚀 Guia de Implementação: Dashboard Kommo no Easypanel

Este documento descreve o passo a passo para realizar o deploy do Dashboard de Inteligência de Vendas na sua VPS utilizando o **Easypanel**.

---

## 📋 Pré-requisitos

1.  **Repositório Git:** O código já está em `https://github.com/brayan-mesquita/dashkommo`.
2.  **VPS com Easypanel:** Acesso administrativo ao painel.
3.  **Credenciais Kommo:** Token de Acesso de longa duração e subdomínio da conta.

---

## 🛠️ Passo a Passo no Easypanel

### 1. Criar o Serviço
1.  Acesse seu Easypanel.
2.  Clique em **"Create Project"** (ou escolha um projeto existente).
3.  Clique em **"Create Service"** e selecione a opção **"App"**.

### 2. Configurar o Repositório (Source)
1.  Na aba **Source**, conecte sua conta do GitHub.
2.  Selecione o repositório `dashkommo`.
3.  Branch: `main`.

### 3. Configurar o Build (Dockerfile)
1.  Vá para a aba **Build**.
2.  Em **Build Method**, selecione **Dockerfile**.
3.  Em **Dockerfile Path**, digite: `app/Dockerfile`.
4.  Clique em **Save**.

### 4. Configurar Variáveis de Ambiente (Environment)
Vá para a aba **Environment** e adicione as seguintes chaves (exatamente como estão no seu `.env.kommo` local):

*   `KOMMO_SUBDOMAIN`: `crmfbcpvh`
*   `KOMMO_ACCESS_TOKEN`: `SEU_TOKEN_AQUI`

> **Importante:** Estas variáveis permitem que o script `scheduler.py` busque os dados reais da API do Kommo a cada 6 horas.

### 5. Configurar Armazenamento Persistente (Volumes)
Para evitar que os dados do dashboard sejam perdidos sempre que o serviço reiniciar:
1.  Vá para a aba **Storage**.
2.  Clique em **Add Volume**.
3.  **Mount Path:** `/app/app`
4.  **Host Path:** `/var/lib/easypanel/projects/SEU_PROJETO/dash-kommo/db_data` (ou similar conforme seu padrão).
5.  Isso garante que o arquivo `kommo_poc.db` fique salvo no disco da VPS.

### 6. Configurar Rede (Network)
1.  Vá para a aba **Network**.
2.  **Port:** Certifique-se de que a porta interna é `8501`.
3.  **Domain:** O Easypanel gerará uma URL automática (ex: `app-dash.seudominio.com`).

---

## 🔐 Acesso ao Dashboard

Assim que o deploy for concluído e a URL estiver ativa:
*   **Link:** A URL fornecida pelo Easypanel.
*   **Usuário:** `admin`
*   **Senha:** `febracis2026`

---

## 🔄 Como funciona a atualização?

*   O **Scheduler** roda automaticamente dentro do container.
*   Horários de atualização: **06h, 12h, 18h e 00h**.
*   Ao atualizar, ele baixa os novos JSONs do Kommo e recria o banco de dados interno.

---

## 🐳 Comandos Úteis (Console do Easypanel)

Se precisar verificar se a sincronização está ocorrendo, você pode abrir o **Terminal/Logs** no Easypanel e verá mensagens como:
`[2026-05-08 18:00:00] Iniciando sincronização com Kommo CRM...`
`[2026-05-08 18:05:00] Sincronização concluída com sucesso!`

---

### Suporte
Se encontrar algum erro de build, verifique se o arquivo `requirements.txt` está correto e se o Token do Kommo não expirou.
