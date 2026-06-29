"""Popula o banco com dados de demonstração: 5 empresas-cliente, cada uma com seu
próprio universo de fornecedores, usuários, consultores e apontamentos, além da
empresa EWMS (dona da plataforma) com o SuperUsuario.

Rode com: python -m scripts.seed (a partir da raiz do ewms-backend, com o venv ativo)
"""
import random
from datetime import date, timedelta
from decimal import Decimal

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import Apontamento, Consultor, Empresa, Fornecedor, Usuario
from app.services.periodo_utils import calcular_semana

random.seed(42)

PROJETOS = [
    ("PRJ-001", "Modernização ERP"),
    ("PRJ-002", "Suporte Operacional"),
    ("PRJ-003", "Expansão Digital"),
    ("PRJ-004", "Migração para Cloud"),
]

NOMES = [
    "João Pereira", "Maria Oliveira", "Carlos Souza", "Ana Beatriz", "Pedro Henrique",
    "Juliana Costa", "Rafael Almeida", "Beatriz Lima", "Thiago Santos", "Camila Rocha",
    "Lucas Martins", "Fernanda Dias", "Bruno Carvalho", "Larissa Nunes", "Gustavo Ribeiro",
]


def cpf_fake(seq: int) -> str:
    base = f"{seq:09d}"
    return f"{base[0:3]}.{base[3:6]}.{base[6:9]}-{seq % 100:02d}"


def cnpj_fake(seq: int) -> str:
    base = f"{seq:08d}"
    return f"{base[0:2]}.{base[2:5]}.{base[5:8]}/0001-{seq % 100:02d}"


EMPRESAS_DATA = [
    {
        "id": "EMP-001", "nome": "Cliente Demo S.A.",
        "admin_email": "admin@ewms.com", "admin_senha": "admin123", "admin_nome": "Administrador Demo",
        "lider_email": "lider@ewms.com", "lider_senha": "lider123", "lider_nome": "Adriana Bastos",
        "fornecedores": [
            {"razao_social": "Tech Solutions LTDA", "segmento": "TI", "cidade": "São Paulo", "uf": "SP",
             "fornecedor_email": "fornecedor@ewms.com", "fornecedor_senha": "fornecedor123",
             "fornecedor_nome": "Maria Silva",
             "consultores": [{"nome": "João Pereira", "email": "usuario@ewms.com", "senha": "usuario123"}]},
        ],
    },
    {
        "id": "EMP-002", "nome": "Banco Horizonte S.A.",
        "admin_email": "admin@horizonte.com", "admin_senha": "admin123", "admin_nome": "Patrícia Mendes",
        "lider_email": "lider@horizonte.com", "lider_senha": "lider123", "lider_nome": "Eduardo Tavares",
        "fornecedores": [
            {"razao_social": "DataCore Consultoria", "segmento": "TI", "cidade": "Rio de Janeiro", "uf": "RJ",
             "fornecedor_email": "fornecedor@datacore.com", "fornecedor_senha": "fornecedor123",
             "fornecedor_nome": "Renato Vieira",
             "consultores": [
                 {"nome": "Maria Oliveira", "email": "maria.oliveira@datacore.com", "senha": "usuario123"},
                 {"nome": "Carlos Souza", "email": "carlos.souza@datacore.com", "senha": "usuario123"},
             ]},
            {"razao_social": "SecureBank Tecnologia", "segmento": "Segurança", "cidade": "Niterói", "uf": "RJ",
             "fornecedor_email": "fornecedor@securebank.com", "fornecedor_senha": "fornecedor123",
             "fornecedor_nome": "Vanessa Cardoso",
             "consultores": [{"nome": "Ana Beatriz", "email": "ana.beatriz@securebank.com", "senha": "usuario123"}]},
        ],
    },
    {
        "id": "EMP-003", "nome": "Varejo Estrela LTDA",
        "admin_email": "admin@estrela.com", "admin_senha": "admin123", "admin_nome": "Marcos Paulo",
        "lider_email": "lider@estrela.com", "lider_senha": "lider123", "lider_nome": "Simone Castro",
        "fornecedores": [
            {"razao_social": "LogiTI Serviços", "segmento": "Infraestrutura", "cidade": "Curitiba", "uf": "PR",
             "fornecedor_email": "fornecedor@logiti.com", "fornecedor_senha": "fornecedor123",
             "fornecedor_nome": "Felipe Andrade",
             "consultores": [
                 {"nome": "Pedro Henrique", "email": "pedro.henrique@logiti.com", "senha": "usuario123"},
                 {"nome": "Juliana Costa", "email": "juliana.costa@logiti.com", "senha": "usuario123"},
             ]},
        ],
    },
    {
        "id": "EMP-004", "nome": "Indústria Atlas LTDA",
        "admin_email": "admin@atlas.com", "admin_senha": "admin123", "admin_nome": "Roberto Fernandes",
        "lider_email": "lider@atlas.com", "lider_senha": "lider123", "lider_nome": "Cláudia Pires",
        "fornecedores": [
            {"razao_social": "Atlas Engenharia de Software", "segmento": "Software", "cidade": "Belo Horizonte", "uf": "MG",
             "fornecedor_email": "fornecedor@atlassoft.com", "fornecedor_senha": "fornecedor123",
             "fornecedor_nome": "Henrique Souza",
             "consultores": [
                 {"nome": "Rafael Almeida", "email": "rafael.almeida@atlassoft.com", "senha": "usuario123"},
                 {"nome": "Beatriz Lima", "email": "beatriz.lima@atlassoft.com", "senha": "usuario123"},
                 {"nome": "Thiago Santos", "email": "thiago.santos@atlassoft.com", "senha": "usuario123"},
             ]},
        ],
    },
    {
        "id": "EMP-005", "nome": "Saúde Vitalis S.A.",
        "admin_email": "admin@vitalis.com", "admin_senha": "admin123", "admin_nome": "Fabiana Rezende",
        "lider_email": "lider@vitalis.com", "lider_senha": "lider123", "lider_nome": "André Luiz",
        "fornecedores": [
            {"razao_social": "MedTech Soluções", "segmento": "Saúde Digital", "cidade": "Porto Alegre", "uf": "RS",
             "fornecedor_email": "fornecedor@medtech.com", "fornecedor_senha": "fornecedor123",
             "fornecedor_nome": "Camila Rocha",
             "consultores": [{"nome": "Lucas Martins", "email": "lucas.martins@medtech.com", "senha": "usuario123"}]},
            {"razao_social": "Vitalis Suporte TI", "segmento": "Suporte", "cidade": "Caxias do Sul", "uf": "RS",
             "fornecedor_email": "fornecedor@vitalisti.com", "fornecedor_senha": "fornecedor123",
             "fornecedor_nome": "Fernanda Dias",
             "consultores": [{"nome": "Bruno Carvalho", "email": "bruno.carvalho@vitalisti.com", "senha": "usuario123"}]},
        ],
    },
]

STATUS_CICLO = ["Aprovado", "Aprovado", "Em Análise", "Recusado"]


def run():
    db = SessionLocal()
    try:
        if db.query(Empresa).count() > 0:
            print("Banco já populado, nada a fazer.")
            return

        empresa_ewms = Empresa(id="EMP-EWMS", nome="EWMS Sistemas", status="Ativo")
        db.add(empresa_ewms)
        db.commit()

        super_usuario = Usuario(
            nome="Super Usuário EWMS", email="super@ewms.com", senha_hash=hash_password("super123"),
            perfil="SuperUsuario", status="Ativo", empresa_id=empresa_ewms.id,
        )
        db.add(super_usuario)
        db.commit()

        cpf_seq = 1
        cnpj_seq = 1
        consultor_seq = 1
        fornecedor_seq = 1
        apontamento_seq = 1

        for empresa_info in EMPRESAS_DATA:
            empresa = Empresa(id=empresa_info["id"], nome=empresa_info["nome"], status="Ativo")
            db.add(empresa)
            db.commit()

            admin = Usuario(
                nome=empresa_info["admin_nome"], email=empresa_info["admin_email"],
                senha_hash=hash_password(empresa_info["admin_senha"]), perfil="Administrador",
                status="Ativo", empresa_id=empresa.id,
            )
            lideranca = Usuario(
                nome=empresa_info["lider_nome"], email=empresa_info["lider_email"],
                senha_hash=hash_password(empresa_info["lider_senha"]), perfil="Liderança",
                status="Ativo", empresa_id=empresa.id,
            )
            db.add_all([admin, lideranca])
            db.commit()

            for fornecedor_info in empresa_info["fornecedores"]:
                fornecedor = Fornecedor(
                    id=f"FOR-{fornecedor_seq:03d}", empresa_id=empresa.id,
                    razao_social=fornecedor_info["razao_social"],
                    nome_fantasia=fornecedor_info["razao_social"].split(" ")[0],
                    cnpj=cnpj_fake(cnpj_seq), segmento=fornecedor_info["segmento"],
                    cidade=fornecedor_info["cidade"], uf=fornecedor_info["uf"], status="Ativo",
                    contato=fornecedor_info["fornecedor_nome"], telefone="(11) 99999-0000",
                    email=fornecedor_info["fornecedor_email"],
                )
                db.add(fornecedor)
                db.commit()
                cnpj_seq += 1
                fornecedor_seq += 1

                fornecedor_user = Usuario(
                    nome=fornecedor_info["fornecedor_nome"], email=fornecedor_info["fornecedor_email"],
                    senha_hash=hash_password(fornecedor_info["fornecedor_senha"]), perfil="Fornecedor",
                    status="Ativo", empresa_id=empresa.id, id_fornecedor=fornecedor.id,
                )
                db.add(fornecedor_user)
                db.commit()

                for idx, consultor_info in enumerate(fornecedor_info["consultores"]):
                    terceiro_user = Usuario(
                        nome=consultor_info["nome"], email=consultor_info["email"],
                        senha_hash=hash_password(consultor_info["senha"]), perfil="Usuário",
                        status="Ativo", empresa_id=empresa.id, cpf=cpf_fake(cpf_seq),
                    )
                    db.add(terceiro_user)
                    db.commit()
                    cpf_seq += 1

                    valor_hora = Decimal(random.choice(["75.00", "85.00", "95.00", "110.00", "120.00"]))
                    horas_previstas = Decimal(random.choice(["30.00", "40.00", "44.00"]))
                    consultor = Consultor(
                        id=f"CON-{consultor_seq:03d}", usuario_id=terceiro_user.id,
                        cargo=random.choice(["Desenvolvedor", "Analista", "Especialista", "Consultor Sênior"]),
                        departamento=random.choice(["TI", "Infraestrutura", "Projetos", "Operações"]),
                        valor_hora=valor_hora, horas_previstas_semana=horas_previstas,
                        id_fornecedor=fornecedor.id, lideranca_id=lideranca.id, status="Ativo",
                        data_inicio=date(2025, random.randint(1, 12), 1),
                    )
                    db.add(consultor)
                    db.commit()
                    consultor_seq += 1

                    # apontamentos das últimas semanas, com status variados, p/ alimentar os gráficos
                    hoje = date(2026, 6, 27)
                    for semana_idx in range(6):
                        data_reporte = hoje - timedelta(weeks=semana_idx)
                        id_projeto, nome_projeto = random.choice(PROJETOS)
                        horas = horas_previstas + Decimal(random.choice(["-4", "0", "0", "4", "8"]))
                        if horas < 0:
                            horas = Decimal("0")
                        status_apontamento = STATUS_CICLO[(semana_idx + idx) % len(STATUS_CICLO)]
                        apontamento = Apontamento(
                            id=f"APO-{apontamento_seq:03d}", id_consultor=consultor.id,
                            id_fornecedor=fornecedor.id, id_projeto=id_projeto, nome_projeto=nome_projeto,
                            data_reporte=data_reporte, semana=calcular_semana(data_reporte),
                            horas_trabalhadas=horas, valor_hora=valor_hora,
                            valor_total=(horas * valor_hora).quantize(Decimal("0.01")),
                            status=status_apontamento,
                            justificativa="Horas fora do esperado para o período." if status_apontamento == "Recusado" else None,
                        )
                        db.add(apontamento)
                        apontamento_seq += 1
            db.commit()

        print("Seed concluído. Empresas e credenciais de teste:")
        print(" - EWMS Sistemas: super@ewms.com / super123 (SuperUsuario, vê todas as empresas)")
        for empresa_info in EMPRESAS_DATA:
            print(f" - {empresa_info['nome']}:")
            print(f"     Administrador: {empresa_info['admin_email']} / {empresa_info['admin_senha']}")
            print(f"     Liderança:     {empresa_info['lider_email']} / {empresa_info['lider_senha']}")
            for fornecedor_info in empresa_info["fornecedores"]:
                print(f"     Fornecedor:    {fornecedor_info['fornecedor_email']} / {fornecedor_info['fornecedor_senha']} ({fornecedor_info['razao_social']})")
                for c in fornecedor_info["consultores"]:
                    print(f"       Usuário/Terceiro: {c['email']} / {c['senha']} ({c['nome']})")
    finally:
        db.close()


if __name__ == "__main__":
    run()
