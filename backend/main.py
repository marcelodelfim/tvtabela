import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
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
    tempo_exibicao = db.Column(db.Integer, default=30) # segundos para alternar (opcional futuro)

class Promocao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_produto = db.Column(db.String(100))
    preco = db.Column(db.String(20))
    setor = db.Column(db.String(50))
    imagem = db.Column(db.String(100))

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
    
    # 4. O PONTO DO ERRO: Agora passamos o setor no url_for
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
    nome_imagem = None

    if 'foto_produto' in request.files:
        file = request.files['foto_produto']
        if file and file.filename != '' and allowed_file(file.filename):
            nome_imagem = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_imagem))

    nova_p = Promocao(nome_produto=nome.upper(), preco=preco, setor=setor, imagem=nome_imagem)
    db.session.add(nova_p)
    db.session.commit()
    return redirect(url_for('pagina_cadastro_promo'))

@app.route('/deletar-promo/<int:id>')
def deletar_promo(id):
    promo = Promocao.query.get(id)
    if promo:
        db.session.delete(promo)
        db.session.commit()
    return redirect(url_for('pagina_cadastro_promo'))

# --- 4. ROTAS: EXIBIÇÃO (TV) ---
@app.route('/tela')
def tela_atalho():
    return redirect(url_for('video_wall_por_setor', setor='Açougue'))

@app.route('/tela/<setor>')
def video_wall_por_setor(setor):
    config = ConfiguracaoTela.query.filter_by(nome_setor=setor).first()
    if not config: config = ConfiguracaoTela.query.first()
    promocoes = Promocao.query.filter_by(setor=setor).all()
    
    # Simulação MGV (será substituído pelo TXT)
    itens_mgv = [{"nome": "ALCATRA KG", "preco": "39,90"}, {"nome": "PICANHA KG", "preco": "69,90"}]
    return render_template('tela_exibicao.html', config=config, promocoes=promocoes, itens_mgv=itens_mgv)

@app.route('/admin/aparencia')
def lista_setores_aparencia():
    setores = ['Açougue', 'Padaria', 'Hortifruti']
    return render_template('selecao_setor.html', setores=setores)

if __name__ == '__main__':
    app.run(debug=True, port=5000)