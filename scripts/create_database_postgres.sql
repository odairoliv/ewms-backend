-- Versão Postgres do schema (porte de create_database.sql, usado pelo MySQL local).
-- Não usa CREATE DATABASE/USE: no Postgres o banco já é criado pela env var
-- POSTGRES_DB do container (ver docker-compose.yml) ou manualmente no Supabase.

CREATE OR REPLACE FUNCTION set_atualizado_em()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS tb_empresas (
    id VARCHAR(20) PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Ativo',
    cnpj VARCHAR(18),
    telefone VARCHAR(20),
    email_contato VARCHAR(150),
    endereco VARCHAR(255),
    status_aprovacao VARCHAR(20) NOT NULL DEFAULT 'Aprovado',
    dados_pendentes TEXT,
    solicitado_por VARCHAR(150),
    solicitado_em TIMESTAMP,
    justificativa_rejeicao TEXT,
    custom01 DATE,
    custom02 VARCHAR(255),
    custom03 VARCHAR(255),
    custom04 DECIMAL(12, 2),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
DROP TRIGGER IF EXISTS trg_empresas_atualizado_em ON tb_empresas;
CREATE TRIGGER trg_empresas_atualizado_em BEFORE UPDATE ON tb_empresas
    FOR EACH ROW EXECUTE FUNCTION set_atualizado_em();

CREATE TABLE IF NOT EXISTS tb_fornecedores (
    id VARCHAR(20) PRIMARY KEY,
    empresa_id VARCHAR(20) NOT NULL,
    razao_social VARCHAR(150) NOT NULL,
    nome_fantasia VARCHAR(150),
    cnpj VARCHAR(18) NOT NULL UNIQUE,
    segmento VARCHAR(100),
    cidade VARCHAR(100),
    uf VARCHAR(2),
    status VARCHAR(20) NOT NULL DEFAULT 'Ativo',
    contato VARCHAR(150),
    telefone VARCHAR(20),
    email VARCHAR(150),
    custom01 DATE,
    custom02 VARCHAR(255),
    custom03 VARCHAR(255),
    custom04 DECIMAL(12, 2),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_fornecedor_empresa FOREIGN KEY (empresa_id) REFERENCES tb_empresas (id)
);
DROP TRIGGER IF EXISTS trg_fornecedores_atualizado_em ON tb_fornecedores;
CREATE TRIGGER trg_fornecedores_atualizado_em BEFORE UPDATE ON tb_fornecedores
    FOR EACH ROW EXECUTE FUNCTION set_atualizado_em();

CREATE TABLE IF NOT EXISTS tb_usuarios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    perfil VARCHAR(30) NOT NULL,
    cpf VARCHAR(14),
    telefone VARCHAR(20),
    departamento VARCHAR(100),
    cargo VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'Ativo',
    empresa_id VARCHAR(20) NOT NULL,
    id_fornecedor VARCHAR(20),
    custom01 DATE,
    custom02 VARCHAR(255),
    custom03 VARCHAR(255),
    custom04 DECIMAL(12, 2),
    edicao_status VARCHAR(20) NOT NULL DEFAULT 'Nenhuma',
    dados_pendentes TEXT,
    solicitado_em TIMESTAMP,
    justificativa_edicao TEXT,
    tentativas_login_falhas INT NOT NULL DEFAULT 0,
    bloqueado_until TIMESTAMP,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_usuario_empresa FOREIGN KEY (empresa_id) REFERENCES tb_empresas (id),
    CONSTRAINT fk_usuario_fornecedor FOREIGN KEY (id_fornecedor) REFERENCES tb_fornecedores (id)
);
DROP TRIGGER IF EXISTS trg_usuarios_atualizado_em ON tb_usuarios;
CREATE TRIGGER trg_usuarios_atualizado_em BEFORE UPDATE ON tb_usuarios
    FOR EACH ROW EXECUTE FUNCTION set_atualizado_em();

CREATE TABLE IF NOT EXISTS tb_consultores (
    id VARCHAR(20) PRIMARY KEY,
    usuario_id INT NOT NULL,
    cargo VARCHAR(100),
    departamento VARCHAR(100),
    valor_hora DECIMAL(10, 2) NOT NULL,
    horas_previstas_semana DECIMAL(6, 2) NOT NULL DEFAULT 0,
    id_fornecedor VARCHAR(20) NOT NULL,
    lideranca_id INT,
    status VARCHAR(20) NOT NULL DEFAULT 'Ativo',
    data_inicio DATE,
    data_fim DATE,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    revisao INT NOT NULL DEFAULT 0,
    custom01 DATE,
    custom02 VARCHAR(255),
    custom03 VARCHAR(255),
    custom04 DECIMAL(12, 2),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_consultor_usuario FOREIGN KEY (usuario_id) REFERENCES tb_usuarios (id),
    CONSTRAINT fk_consultor_fornecedor FOREIGN KEY (id_fornecedor) REFERENCES tb_fornecedores (id),
    CONSTRAINT fk_consultor_lideranca FOREIGN KEY (lideranca_id) REFERENCES tb_usuarios (id)
);
DROP TRIGGER IF EXISTS trg_consultores_atualizado_em ON tb_consultores;
CREATE TRIGGER trg_consultores_atualizado_em BEFORE UPDATE ON tb_consultores
    FOR EACH ROW EXECUTE FUNCTION set_atualizado_em();

CREATE TABLE IF NOT EXISTS tb_apontamentos (
    id VARCHAR(20) PRIMARY KEY,
    id_consultor VARCHAR(20) NOT NULL,
    id_fornecedor VARCHAR(20) NOT NULL,
    id_projeto VARCHAR(20),
    nome_projeto VARCHAR(150),
    data_reporte DATE NOT NULL,
    semana VARCHAR(8) NOT NULL,
    horas_trabalhadas DECIMAL(6, 2) NOT NULL,
    valor_hora DECIMAL(10, 2) NOT NULL,
    valor_total DECIMAL(12, 2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Em Análise',
    justificativa TEXT,
    edicao_status VARCHAR(20) NOT NULL DEFAULT 'Nenhuma',
    horas_pendentes DECIMAL(6, 2),
    solicitado_por VARCHAR(150),
    solicitado_em TIMESTAMP,
    justificativa_edicao TEXT,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    custom01 DATE,
    custom02 VARCHAR(255),
    custom03 VARCHAR(255),
    custom04 DECIMAL(12, 2),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_apontamento_consultor FOREIGN KEY (id_consultor) REFERENCES tb_consultores (id),
    CONSTRAINT fk_apontamento_fornecedor FOREIGN KEY (id_fornecedor) REFERENCES tb_fornecedores (id)
);
DROP TRIGGER IF EXISTS trg_apontamentos_atualizado_em ON tb_apontamentos;
CREATE TRIGGER trg_apontamentos_atualizado_em BEFORE UPDATE ON tb_apontamentos
    FOR EACH ROW EXECUTE FUNCTION set_atualizado_em();

CREATE TABLE IF NOT EXISTS tb_uploads (
    id VARCHAR(20) PRIMARY KEY,
    empresa_id VARCHAR(20) NOT NULL,
    arquivo VARCHAR(255) NOT NULL,
    periodo VARCHAR(20) NOT NULL,
    data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    linhas INT NOT NULL DEFAULT 0,
    processadas INT NOT NULL DEFAULT 0,
    rejeitadas INT NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'Processando',
    erro_detalhe TEXT,
    CONSTRAINT fk_upload_empresa FOREIGN KEY (empresa_id) REFERENCES tb_empresas (id)
);

CREATE TABLE IF NOT EXISTS tb_audit (
    id VARCHAR(20) PRIMARY KEY,
    empresa_id VARCHAR(20) NOT NULL,
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario VARCHAR(150) NOT NULL,
    email_usuario VARCHAR(150) NOT NULL,
    modulo VARCHAR(100) NOT NULL,
    tipo_acao VARCHAR(30) NOT NULL,
    ip VARCHAR(45),
    nivel VARCHAR(30) NOT NULL,
    entidade VARCHAR(100),
    entidade_id VARCHAR(20),
    campo_alterado VARCHAR(100),
    valor_antes TEXT,
    valor_depois TEXT,
    justificativa TEXT,
    CONSTRAINT fk_audit_empresa FOREIGN KEY (empresa_id) REFERENCES tb_empresas (id)
);

CREATE TABLE IF NOT EXISTS tb_custom (
    id SERIAL PRIMARY KEY,
    empresa_id VARCHAR(20) NOT NULL,
    id_objeto VARCHAR(50) NOT NULL,
    nome_coluna VARCHAR(50) NOT NULL,
    nome VARCHAR(100) NOT NULL,
    tipo VARCHAR(20) NOT NULL DEFAULT 'padrao',
    visivel BOOLEAN NOT NULL DEFAULT TRUE,
    obrigatorio BOOLEAN NOT NULL DEFAULT FALSE,
    ordem INT NOT NULL DEFAULT 0,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_custom_empresa FOREIGN KEY (empresa_id) REFERENCES tb_empresas (id),
    CONSTRAINT uq_custom_campo UNIQUE (empresa_id, id_objeto, nome_coluna)
);
DROP TRIGGER IF EXISTS trg_custom_atualizado_em ON tb_custom;
CREATE TRIGGER trg_custom_atualizado_em BEFORE UPDATE ON tb_custom
    FOR EACH ROW EXECUTE FUNCTION set_atualizado_em();
