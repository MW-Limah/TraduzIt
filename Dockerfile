FROM python:3.11-slim

# Atualiza e instala dependências necessárias
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto para o container
COPY . .

# Instala as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Define o comando padrão para iniciar a aplicação
CMD ["python", "app.py"]