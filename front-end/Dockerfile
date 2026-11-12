# Estágio 1: Build da aplicação Angular utilizando Bun
FROM oven/bun:1 AS builder

WORKDIR /app

# Instalação das dependências com cache de camada
COPY package.json bun.lock* ./
RUN bun install --frozen-lockfile

# Cópia do código-fonte e build de produção
COPY . ./
RUN bun run build

# Estágio 2: Imagem de runtime com Nginx Alpine
FROM nginx:alpine

# Remove configuração padrão do Nginx
RUN rm -rf /usr/share/nginx/html/*

# Copia os artefatos compilados da SPA Angular
COPY --from=builder /app/dist/automacao-front/browser /usr/share/nginx/html

# Copia configuração customizada com suporte a SPA e proxy reverso para o back-end
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://127.0.0.1/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
