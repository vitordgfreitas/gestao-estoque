# Como Configurar Domínio Customizado no Render

## Opções de Domínio

### 1. Subdomínio do Render (Gratuito - Padrão)
- URL padrão: `crm-backend-ghly.onrender.com`
- Você pode personalizar o nome do serviço
- Vá em **Settings** → **Name** → Mude para algo mais amigável
- Nova URL: `seu-nome.onrender.com`

### 2. Domínio Customizado (Recomendado para Produção)

#### Passo a Passo:

**1. No Render:**
   - Vá em **Settings** do seu serviço
   - Role até **"Custom Domains"**
   - Clique em **"Add Custom Domain"**
   - Digite seu domínio (ex: `api.seudominio.com`)

**2. Configure DNS no seu provedor:**
   
   **Para subdomínio (api.seudominio.com):**
   ```
   Tipo: CNAME
   Nome: api
   Valor: crm-backend-ghly.onrender.com
   TTL: 3600 (ou padrão)
   ```

   **Para domínio raiz (seudominio.com):**
   - Alguns provedores: Use ALIAS ou ANAME
   - Ou use CNAME se suportado
   - Render fornecerá instruções específicas

**3. Aguarde propagação DNS:**
   - Pode levar de alguns minutos a 48 horas
   - Render verificará automaticamente
   - Você receberá notificação quando estiver pronto

**4. SSL Automático:**
   - Render configura SSL/HTTPS automaticamente
   - Certificado Let's Encrypt gratuito
   - Renovação automática

## Exemplo Completo

### Backend:
- **Domínio Render:** `crm-backend-ghly.onrender.com`
- **Domínio Customizado:** `api.seudominio.com`
- **DNS:** CNAME `api` → `crm-backend-ghly.onrender.com`

### Frontend:
- **Domínio Render:** `crm-frontend-nbrm.onrender.com`
- **Domínio Customizado:** `app.seudominio.com` ou `seudominio.com`
- **DNS:** CNAME `app` → `crm-frontend-nbrm.onrender.com`
- **Atualizar:** `VITE_API_URL` = `https://api.seudominio.com`

## Provedores de DNS Comuns

### Cloudflare:
1. Adicione seu domínio no Cloudflare
2. Vá em **DNS** → **Records**
3. Adicione CNAME:
   - Name: `api`
   - Target: `crm-backend-ghly.onrender.com`
   - Proxy: Desligado (cinza) ou Ligado (laranja)

### Google Domains / Namecheap:
1. Vá em **DNS Management**
2. Adicione registro CNAME
3. Configure conforme instruções do Render

### Registro.br:
1. Acesse o painel
2. Vá em **DNS**
3. Adicione registro CNAME

## Verificação

Após configurar:
1. Verifique DNS: `nslookup api.seudominio.com` (deve apontar para Render)
2. Render mostrará status em "Custom Domains"
3. Quando estiver verde, está funcionando!
4. Acesse `https://api.seudominio.com` (com HTTPS)

## Troubleshooting

**DNS não propaga:**
- Aguarde até 48 horas
- Verifique se o registro está correto
- Use ferramentas como `dnschecker.org`

**SSL não funciona:**
- Render configura automaticamente
- Pode levar alguns minutos após DNS propagar
- Verifique se está usando HTTPS

**Frontend não conecta ao backend:**
- Atualize `VITE_API_URL` no Render (Environment Variables)
- Use o novo domínio do backend
- Faça novo deploy do frontend

## Dicas

- **Subdomínios são mais fáceis:** Use `api.` e `app.` ao invés de domínio raiz
- **Cloudflare é gratuito:** Oferece DNS rápido e gratuito
- **SSL automático:** Render cuida de tudo
- **Backup:** Mantenha a URL do Render como backup
