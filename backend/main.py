import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
# Variável global para avisar as TVs que precisam atualizar
VERSAO_SISTEMA = 1
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mercado.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'chave_secreta_super_segura_123'

# Configuração para upload
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- MODELOS ---
class ConfiguracaoTela(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_setor = db.Column(db.String(50), default="Açougue")
    cor_fundo = db.Column(db.String(7), default="#121212")
    cor_texto = db.Column(db.String(7), default="#ffffff")
    cor_destaque = db.Column(db.String(7), default="#f1c40f")
    fonte_familia = db.Column(db.String(50), default="'Oswald', sans-serif")
    layout_tipo = db.Column(db.String(20), default="tabela_mista")
    imagem_fundo = db.Column(db.String(100))
    modo_exibicao = db.Column(db.String(20), default="tabela") 
    tempo_tabela = db.Column(db.Integer, default=15)  # Tempo de cada página da lista
    tempo_promo = db.Column(db.Integer, default=10)

class Promocao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_produto = db.Column(db.String(100))
    preco = db.Column(db.String(20))
    setor = db.Column(db.String(50))
    imagem = db.Column(db.String(100))
    ativo = db.Column(db.Boolean, default=True) # Ativa/Desativa manualmente
    dom = db.Column(db.Boolean, default=True) # Segunda...
    seg = db.Column(db.Boolean, default=True) # ...até domingo
    ter = db.Column(db.Boolean, default=True)
    qua = db.Column(db.Boolean, default=True)
    qui = db.Column(db.Boolean, default=True)
    sex = db.Column(db.Boolean, default=True)
    sab = db.Column(db.Boolean, default=True)

with app.app_context():
    db.create_all()
    if not ConfiguracaoTela.query.first():
        db.session.add(ConfiguracaoTela(nome_setor="Açougue"))
        db.session.commit()

# --- 1. ROTA: MENU PRINCIPAL (O HUB DE CARDS) ---
@app.route('/admin')
def menu_admin():
    return render_template('menu_admin.html')

# --- 2. ROTA: CONFIGURAÇÃO DE APARÊNCIA (CORES/FONTES) ---
@app.route('/admin/config/<setor>')
def admin_config(setor):
    # Busca a configuração específica do setor (ex: Açougue)
    config = ConfiguracaoTela.query.filter_by(nome_setor=setor).first()
    
    # Se não existir, cria uma configuração padrão para esse novo setor
    if not config:
        config = ConfiguracaoTela(nome_setor=setor)
        db.session.add(config)
        db.session.commit()
        
    return render_template('admin.html', config=config)

@app.route('/admin/salvar', methods=['POST'])
def salvar_config():
    # 1. Pega o nome do setor que estamos editando
    setor_atual = request.form.get('nome_setor')
    
    # 2. Busca a configuração no banco
    config = ConfiguracaoTela.query.filter_by(nome_setor=setor_atual).first()
    
    if config:
        # 3. Atualiza os campos
        config.modo_exibicao = request.form.get('modo_exibicao')
        config.cor_fundo = request.form.get('cor_fundo')
        config.cor_texto = request.form.get('cor_texto')
        config.cor_destaque = request.form.get('cor_destaque')
        config.fonte_familia = request.form.get('fonte_familia')
        config.modo_exibicao = request.form.get('modo_exibicao') # O novo rádio button
        
        # Lógica de upload da imagem de fundo
        if 'imagem_fundo' in request.files:
            file = request.files['imagem_fundo']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                config.imagem_fundo = filename
        
        db.session.commit()
    
    # --- ADICIONE ESTAS DUAS LINHAS AQUI ---
    global VERSAO_SISTEMA
    VERSAO_SISTEMA += 1
    
    # Isso faz ele voltar exatamente para a página do setor que você estava editando
    return redirect(url_for('admin_config', setor=setor_atual))

# --- 3. ROTAS: CADASTRO DE PROMOÇÕES (MANUAL) ---
@app.route('/cadastro-promo')
def pagina_cadastro_promo():
    promocoes = Promocao.query.order_by(Promocao.id.desc()).all()
    return render_template('cadastro_promo.html', promocoes=promocoes)

@app.route('/admin/promo/adicionar', methods=['POST'])
def add_promo():
    nome = request.form.get('nome')
    preco = request.form.get('preco')
    setor = request.form.get('setor')
    
    # --- NOVA LÓGICA DOS CHECKBOXES ---
    # Em HTML, se o checkbox for marcado, ele envia o valor 'on'. 
    # Se for desmarcado, ele envia None. O código abaixo converte isso para True ou False.
    seg = request.form.get('seg') is not None
    ter = request.form.get('ter') is not None
    qua = request.form.get('qua') is not None
    qui = request.form.get('qui') is not None
    sex = request.form.get('sex') is not None
    sab = request.form.get('sab') is not None
    dom = request.form.get('dom') is not None

    nome_imagem = None

    if 'foto_produto' in request.files:
        file = request.files['foto_produto']
        if file and file.filename != '' and allowed_file(file.filename):
            nome_imagem = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_imagem))

    # Agora passamos os dias da semana capturados para o banco de dados
    nova_p = Promocao(
        nome_produto=nome.upper(), 
        preco=preco, 
        setor=setor, 
        imagem=nome_imagem,
        seg=seg, ter=ter, qua=qua, qui=qui, sex=sex, sab=sab, dom=dom
    )
    
    db.session.add(nova_p)
    db.session.commit()
    
    global VERSAO_SISTEMA
    VERSAO_SISTEMA += 1
    
    return redirect(url_for('pagina_cadastro_promo'))

@app.route('/admin/promo/editar/<int:id>', methods=['POST'])
def editar_promo(id):
    # Busca o produto no banco de dados pelo ID
    promo = Promocao.query.get(id)
    
    if promo:
        # Atualiza os dados básicos
        promo.nome_produto = request.form.get('nome').upper()
        promo.preco = request.form.get('preco')
        promo.setor = request.form.get('setor')
        
        # Atualiza os dias da semana (mesma lógica do cadastro)
        promo.seg = request.form.get('seg') is not None
        promo.ter = request.form.get('ter') is not None
        promo.qua = request.form.get('qua') is not None
        promo.qui = request.form.get('qui') is not None
        promo.sex = request.form.get('sex') is not None
        promo.sab = request.form.get('sab') is not None
        promo.dom = request.form.get('dom') is not None

        # Lógica da imagem: Só altera se o usuário enviou um arquivo novo
        if 'foto_produto' in request.files:
            file = request.files['foto_produto']
            if file and file.filename != '' and allowed_file(file.filename):
                nome_imagem = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_imagem))
                promo.imagem = nome_imagem

        db.session.commit()
        
        global VERSAO_SISTEMA
        VERSAO_SISTEMA += 1
        
    return redirect(url_for('pagina_cadastro_promo'))

@app.route('/deletar-promo/<int:id>')
def deletar_promo(id):
    promo = Promocao.query.get(id)
    if promo:
        db.session.delete(promo)
        db.session.commit()
        
        global VERSAO_SISTEMA
        VERSAO_SISTEMA += 1
        
    return redirect(url_for('pagina_cadastro_promo'))

# --- 4. ROTAS: EXIBIÇÃO (TV) ---
@app.route('/tela')
def tela_atalho():
    return redirect(url_for('video_wall_por_setor', setor='Açougue'))

@app.route('/tela/<setor>')
def video_wall_por_setor(setor):
    config = ConfiguracaoTela.query.filter_by(nome_setor=setor).first()
    
    # --- TRAVA DE SEGURANÇA ADICIONADA ---
    # Se a configuração desse setor ainda não existe no banco, cria uma padrão na hora!
    if not config:
        config = ConfiguracaoTela(nome_setor=setor)
        db.session.add(config)
        db.session.commit()
    # -------------------------------------

    # 1. Buscamos as promoções no banco
    promocoes_objetos = Promocao.query.filter_by(setor=setor, ativo=True).all()
    
    # 2. TRANSFORMAMOS EM DICIONÁRIO
    promocoes_lista = []
    for p in promocoes_objetos:
            promocoes_lista.append({
                "id": p.id,
                "nome_produto": p.nome_produto,
                "preco": p.preco,
                "imagem": p.imagem,
                "ativo": p.ativo, 
                "seg": bool(p.seg), 
                "ter": bool(p.ter),
                "qua": bool(p.qua),
                "qui": bool(p.qui),
                "sex": bool(p.sex),
                "sab": bool(p.sab),
                "dom": bool(p.dom)
            })

    # Simulando itens do MGV (Agora enviando o "codigo" também)
    itens_mgv = [{"codigo": str(i).zfill(3), "nome": f"Produto {i}", "preco": f"{i},99"} for i in range(1, 61)]
    
    # --- NOVA LÓGICA DE ROTEAMENTO DE TEMPLATES ---
    if 'tabela' in config.modo_exibicao:
        # Carrega o HTML complexo com paginação
        
        global VERSAO_SISTEMA
        VERSAO_SISTEMA += 1
        
        return render_template('tela_tabela.html', 
                               config=config, 
                               promocoes=promocoes_lista, 
                               itens_mgv=itens_mgv)
    else:
        # Carrega o HTML leve apenas com Flexbox para as promoções
        
        
        return render_template('tela_promo.html', 
                               config=config, 
                               promocoes=promocoes_lista)
        
@app.route('/admin/aparencia')
def lista_setores_aparencia():
    setores = ['Açougue', 'Padaria', 'Hortifruti']
    return render_template('selecao_setor.html', setores=setores)

@app.route('/api/versao')
def api_versao():
    return {"versao": VERSAO_SISTEMA}

if __name__ == '__main__':
    app.run(debug=True, port=5000)