from pathlib import Path
from datetime import date
from zoneinfo import ZoneInfo
from datetime import datetime
from copy import deepcopy
import base64
import hashlib
import hmac
import html
import io
import json
import time
import uuid
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
from PIL import Image, ImageOps
from financeiro import ROOT, DATA, KINDS, MONTHS, load, save, payment, rows, totals, due, scheduled, brl, input_brl, parse_brl, month_add, month_label, validate, Conflict
from visual import STYLE, CAROUSEL

st.set_page_config(page_title='Nosso Universo · Lucas & Julia',page_icon='♡',layout='wide')
st.markdown(STYLE,unsafe_allow_html=True)
st.markdown('<style>[data-testid="stMetricValue"]{font-size:25px}.stButton button{min-height:38px}.block-container{padding-top:1.5rem}.hero{min-height:240px;padding:30px}.hero h1{font-size:40px}.photo,.photo-empty{height:240px} .stTabs{margin-top:15px}</style>',unsafe_allow_html=True)

# Optional local login; external exposure is refused until credentials are set.
users={}
if (ROOT/'.streamlit/secrets.toml').exists():
    try: users=dict(st.secrets.get('usuarios',{}))
    except Exception:st.error('Não foi possível ler a configuração de acesso.');st.stop()
address=st.get_option('server.address')
if address not in ('127.0.0.1','localhost','::1') and not users:
    st.error('Acesso pela rede bloqueado. Configure os usuários antes de mudar o endereço do servidor. Veja LEIA-ME.md.');st.stop()
if users and not st.session_state.get('authenticated'):
    st.title('♡ Nosso Universo')
    st.caption('Um espaço só de vocês. Entre para continuar.')
    with st.form('login'):
        username=st.selectbox('Pessoa',list(users))
        password=st.text_input('Senha',type='password')
        if st.form_submit_button('Entrar',type='primary'):
            if time.time()<st.session_state.get('blocked_until',0):st.error('Aguarde um minuto antes de tentar novamente.')
            else:
                try:
                    salt,digest=users[username].split('$');check=hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),600000).hex()
                    ok=hmac.compare_digest(check,digest)
                except Exception:ok=False
                if ok:st.session_state.authenticated=username;st.rerun()
                else:
                    st.session_state.attempts=st.session_state.get('attempts',0)+1
                    if st.session_state.attempts>=5:st.session_state.blocked_until=time.time()+60;st.session_state.attempts=0
                    st.error('Senha incorreta.')
    st.stop()
try:s,version=load()
except Exception:st.error('Não foi possível abrir o banco. Preserve a pasta dados e tente novamente.');st.stop()
try:today=datetime.now(ZoneInfo('America/Sao_Paulo')).date()
except Exception:today=date.today()
current=today.strftime('%Y-%m')
if 'selected_month' not in st.session_state:st.session_state.selected_month=current

def commit(candidate,message):
    try:save(candidate,version);st.session_state.notice=message;st.rerun()
    except (ValueError,Conflict,KeyError,TypeError) as e:st.error(str(e))
    except Exception:st.error('Não foi possível salvar. Os dados não foram confirmados; tente novamente.')

def mark(a,m,paid):
    try:payment(a['id'],m,paid,st.session_state.get('authenticated',st.session_state.get('actor','Lucas')));st.session_state.notice='Conta concluída. O valor a pagar diminuiu.' if paid else 'Pagamento desfeito. A conta voltou às pendências.';st.rerun()
    except Exception as e:st.error(str(e))

def month_fields(prefix,value):
    y,m=map(int,value.split('-'));c1,c2=st.columns(2)
    mm=c1.selectbox('Mês',list(range(1,13)),index=m-1,format_func=lambda n:MONTHS[n-1].capitalize(),key=prefix+'_month')
    yy=c2.number_input('Ano',min_value=2020,max_value=2099,value=y,step=1,key=prefix+'_year')
    return f'{yy:04}-{mm:02}'

with st.sidebar:
    st.markdown('### ♡ Nosso espaço')
    st.caption('Lucas & Julia · um plano, dois corações')
    if users:
        st.caption('Conectado como '+st.session_state.authenticated)
        if st.button('Sair'):st.session_state.clear();st.rerun()
    else:st.selectbox('Quem está registrando?', ['Lucas','Julia'],key='actor')
    st.caption('Dados deste Streamlit ficam separados do site online anterior.')
    if st.button('Atualizar dados',use_container_width=True):st.rerun()
    with st.expander('Rendas do casal'):
        with st.form('incomes'):
            rl=st.text_input('Renda Lucas (R$)',input_brl(s['incomes']['Lucas']))
            rj=st.text_input('Renda Julia (R$)',input_brl(s['incomes']['Julia']))
            if st.form_submit_button('Salvar rendas'):
                try:
                    n=deepcopy(s);n['incomes']={'Lucas':parse_brl(rl),'Julia':parse_brl(rj)};commit(n,'Rendas atualizadas.')
                except ValueError as e:st.error(str(e))
        st.caption('Rendas mantidas da versão anterior. Alterar atualiza a projeção inteira; não é um histórico de salários.')
    with st.expander('Nossa foto'):
        photo=st.file_uploader('JPG ou PNG',type=['jpg','jpeg','png'])
        if photo and st.button('Salvar foto'):
            try:
                if photo.size>5_000_000:raise ValueError('Escolha uma foto de até 5 MB.')
                im=ImageOps.exif_transpose(Image.open(photo));im.thumbnail((1400,1400));DATA.mkdir(exist_ok=True,parents=True)
                im.convert('RGB').save(DATA/'foto.jpg',quality=88);st.rerun()
            except Exception:st.error('Não foi possível salvar. Use JPG ou PNG de até 5 MB.')
        if (DATA/'foto.jpg').exists() and st.button('Remover foto'):(DATA/'foto.jpg').unlink();st.rerun()
    st.download_button('↓ Backup dos dados',json.dumps(s,ensure_ascii=False,indent=2),'nosso-universo-backup.json','application/json',use_container_width=True)
    with st.expander('Restaurar backup'):
        st.caption('Aceita o backup do site novo e desta versão Streamlit. Não aceita o JSON do primeiro protótipo.')
        f=st.file_uploader('Backup JSON',type=['json'])
        confirm=st.checkbox('Substituir contas, metas e pagamentos atuais')
        if st.button('Restaurar',disabled=not(f and confirm)):
            try:
                if f.size>5_000_000:raise ValueError('Arquivo muito grande.')
                candidate=validate(json.loads(f.getvalue()));commit(candidate,'Backup restaurado.')
            except Exception as e:st.error('Backup não restaurado: '+str(e))
    st.caption('O banco é salvo na pasta dados. Backup JSON não inclui a foto. Não exclua essa pasta ao atualizar o app.')

st.markdown('<div class="brand">nosso universo ♡<span>FINANÇAS A DOIS · LUCAS & JULIA</span></div>',unsafe_allow_html=True)
a,b=st.columns([2.2,1],gap='large')
with a:st.markdown('<div class="hero"><div class="eyebrow">Dois corações. Um mesmo plano.</div><h1>Nosso futuro começa<br><em>nas escolhas de hoje.</em></h1><p>Cada conta resolvida abre espaço para uma conquista nossa.</p><div class="pill">LUCAS + JULIA &nbsp; ∞ &nbsp; NO MESMO TIME</div></div>',unsafe_allow_html=True)
with b:
    if (DATA/'foto.jpg').exists():
        encoded=base64.b64encode((DATA/'foto.jpg').read_bytes()).decode();st.markdown(f'<img class="photo" alt="Foto do casal" src="data:image/jpeg;base64,{encoded}">',unsafe_allow_html=True)
    else:st.markdown('<div class="photo-empty"><b>♡ Nosso lugar favorito.</b><span>Adicione a foto de vocês no menu lateral.</span></div>',unsafe_allow_html=True)
if st.session_state.get('notice'):st.success(st.session_state.pop('notice'))
prev,mc,nxt,pc=st.columns([.55,3,.55,2])
with prev:
    if st.button('←',help='Mês anterior'):st.session_state.selected_month=month_add(st.session_state.selected_month,-1);st.rerun()
with nxt:
    if st.button('→',help='Próximo mês'):st.session_state.selected_month=month_add(st.session_state.selected_month,1);st.rerun()
months=[month_add('2025-01',i) for i in range(60)]
if st.session_state.selected_month not in months:months.append(st.session_state.selected_month);months.sort()
with mc:
    chosen=st.selectbox('Mês de referência',months,index=months.index(st.session_state.selected_month),format_func=month_label)
    if chosen!=st.session_state.selected_month:st.session_state.selected_month=chosen;st.rerun()
m=st.session_state.selected_month
with pc:person=st.selectbox('Visão', ['Nós dois','Lucas','Julia'])
t=totals(s,m,person)
cs=st.columns(4)
for c,label,value in zip(cs,['Renda mensal','Falta pagar','Já pagamos','Saldo após todas as contas'],[t['income'],t['pending'],t['paid'],t['balance']]):c.metric(label,brl(value))
msg=f"Precisamos ajustar {brl(-t['balance'])} para equilibrar {month_label(m).lower()}." if t['balance']<0 else f"O planejamento deixa {brl(t['balance'])} para outras escolhas."
st.markdown(f'<div class="note">{msg}<br>Previsto no mês: <b>{brl(t["planned"])}</b>. Concluir reduz “Falta pagar”. O saldo previsto não aumenta: o dinheiro já foi utilizado.</div>',unsafe_allow_html=True)
month_tab,future_tab,accounts_tab,dream_tab=st.tabs(['Contas do mês','Próximos meses','Todas as contas','Nossos sonhos'])
with month_tab:
    st.subheader('Uma conta a menos. Um respiro a mais.')
    rr=rows(s,m,person);pending=[r for r in rr if not r['payment']];paid=[r for r in rr if r['payment']]
    status=st.radio('Situação',[f'A pagar ({len(pending)})',f'Pagas ({len(paid)})'],horizontal=True)
    shown=pending if status.startswith('A pagar') else paid
    if m<s['baseline']:st.warning('Período anterior ao início do controle. Pagamentos não foram confirmados: revise antes de considerar atraso.')
    if not shown:st.info('Nenhuma conta nesta lista. As concluídas ficam em Pagas.')
    for r in shown:
        a=r['account'];c1,c2,c3,c4=st.columns([4,2,2,1.5])
        with c1:
            st.markdown('**'+html.escape(a['name'])+'**')
            number=(int(m[:4])-int(a['start'][:4]))*12+int(m[5:])-int(a['start'][5:])+1
            st.caption(f"{a['person']} · {KINDS[a['kind']]}"+(f" · {number}/{a['quantity']}" if a['kind']=='installment' else ''))
        with c2:
            st.write(r['due'].strftime('%d/%m/%Y') if r['due'] else 'Dia a definir')
            if r['payment']:st.caption('Concluída · '+r['payment']['by'])
            elif r['due'] and r['due']<today and m>=s['baseline']:st.caption('Vencida')
        c3.write(brl(r['cents']))
        if c4.button('↶ Desfazer' if r['payment'] else '✓ Concluir',key='pay_'+r['key'],use_container_width=True):mark(a,m,not bool(r['payment']))
    with st.expander('Gastos opcionais — incluir somente se usar'):
        for a in s['accounts']:
            if a['kind']!='optional' or not scheduled(a,m):continue
            key=a['id']+'@'+m;active=key in s['optionalMonths'];c1,c2=st.columns([4,2])
            c1.write(f"{a['name']} · {a['person']} · {brl(a['cents'])}")
            if c2.button('Retirar do mês' if active else 'Incluir no mês',key='optional_'+key,disabled=key in s['payments']):
                n=deepcopy(s);n['optionalMonths']=[k for k in n['optionalMonths'] if k!=key] if active else n['optionalMonths']+[key];commit(n,'Gasto opcional atualizado.')
    st.divider()
    for col,p in zip(st.columns(2),['Lucas','Julia']):
        pt=totals(s,m,p)
        with col:
            st.markdown('### '+p+' ♡');st.write('Falta pagar: **'+brl(pt['pending'])+'**');st.caption('Concluído: '+brl(pt['paid']))
            st.progress(pt['paid']/pt['planned'] if pt['planned'] else 0)
with future_tab:
    st.subheader('Mais leve a cada capítulo.')
    fut=[(month_add(m,i),totals(s,month_add(m,i),person)) for i in range(12)]
    fig=go.Figure()
    for label,field,color in [('Falta pagar','pending','#87536a'),('Já pago','paid','#789c88')]:
        fig.add_bar(name=label,x=[month_label(mm) for mm,_ in fut],y=[x[field] for _,x in fut],customdata=[brl(x[field]) for _,x in fut],marker_color=color,hovertemplate='%{x}<br>%{customdata}<extra>%{fullData.name}</extra>')
    ticks=[max(x['planned'] for _,x in fut)*i/4 for i in range(5)]
    fig.update_layout(barmode='stack',height=340,paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',margin=dict(l=0,r=0,t=25,b=0),font_color='#826f71',yaxis=dict(tickvals=ticks,ticktext=[brl(round(x)) for x in ticks],gridcolor='#e8ded9'),legend=dict(orientation='h',y=1.15))
    st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})
    st.dataframe(pd.DataFrame([{'Mês':month_label(mm),'Previsto':brl(x['planned']),'Pago':brl(x['paid']),'Falta pagar':brl(x['pending']),'Saldo previsto':brl(x['balance'])} for mm,x in fut]),hide_index=True,use_container_width=True)
    st.caption('Fixas repetem todo mês; parcelas encerram no término. Renda constante. Opcionais só entram nos meses selecionados. Dívidas sem acordo ficam separadas.')
with accounts_tab:
    st.subheader('Tudo na mesa, sem julgamentos.')
    st.caption('Quantidades são o total original do contrato. Início calculado pela data final. Pagamentos anteriores não foram presumidos.')
    visible=[a for a in s['accounts'] if person=='Nós dois' or a['person']==person]
    st.dataframe(pd.DataFrame([{'Conta':a['name'],'Pessoa':a['person'],'Tipo':KINDS[a['kind']],'Valor':brl(a['cents']),'Parcelas':str(a['quantity']) if a['kind']=='installment' else '—','Início':month_label(a['start']),'Término':month_label(a['end']) if a['end'] else '—','Situação':'Arquivada' if a['archived'] else 'Ativa'} for a in visible]),hide_index=True,use_container_width=True)
    st.metric('Dívidas a negociar — fora do orçamento',brl(sum(a['cents'] for a in s['accounts'] if a['kind']=='debt' and not a['archived'])))
    options=['new']+[a['id'] for a in s['accounts']]
    names={a['id']:f"{a['name']} · {a['person']} · {brl(a['cents'])}" for a in s['accounts']}
    selected=st.selectbox('Adicionar ou editar',options,format_func=lambda x:'＋ Nova conta' if x=='new' else names[x])
    account=next((a for a in s['accounts'] if a['id']==selected),dict(id='new',name='',person='Lucas',kind='installment',cents=0,day=None,start=m,end=m,quantity=1,enabled=True,archived=False))
    with st.form('account_'+selected):
        name=st.text_input('Nome da conta',account['name'],max_chars=100)
        c1,c2=st.columns(2);owner=c1.selectbox('Responsável',['Lucas','Julia'],index=['Lucas','Julia'].index(account['person']))
        kind=c2.selectbox('Tipo',list(KINDS),index=list(KINDS).index(account['kind']),format_func=KINDS.get)
        c1,c2=st.columns(2);value=c1.text_input('Valor (R$)',input_brl(account['cents']));day=c2.text_input('Dia de vencimento (em branco se desconhecido)',str(account['day'] or ''))
        qty=st.number_input('Total original de parcelas (usado apenas no tipo Parcela)',min_value=1,max_value=600,value=account['quantity'],step=1)
        st.caption('Para parcelas, selecione o mês da última parcela. Para os demais tipos, selecione o primeiro mês.')
        endpoint=month_fields('period_'+selected,account['end'] or account['start'])
        archived=st.checkbox('Arquivar — retirar pendências e projeções; preservar pagamentos',value=account['archived'])
        if st.form_submit_button('Salvar conta',type='primary'):
            try:
                a=dict(id=uuid.uuid4().hex if selected=='new' else selected,name=name.strip(),person=owner,kind=kind,cents=parse_brl(value),day=int(day) if day.strip() else None,start=month_add(endpoint,-qty+1) if kind=='installment' else endpoint,end=endpoint if kind=='installment' else '',quantity=int(qty) if kind=='installment' else 1,enabled=True,archived=archived)
                n=deepcopy(s)
                if selected=='new':n['accounts'].append(a)
                else:n['accounts']=[a if x['id']==selected else x for x in n['accounts']]
                commit(n,'Conta salva. Projeções atualizadas.')
            except (ValueError,TypeError) as e:st.error(str(e))
    with st.expander('Conferir parcelas anteriores a setembro/2026'):
        st.caption('Não sabemos quais já foram pagas. Escolha um mês no topo para registrar os pagamentos. Não são somadas automaticamente como dívidas atuais.')
        for a in s['accounts']:
            if a['kind']=='installment' and a['start']<s['baseline']:
                st.write(f"{a['name']} · {a['person']}: início em {month_label(a['start'])}, {a['quantity']} parcelas originais.")
with dream_tab:
    st.subheader('Dinheiro com um porquê.')
    for g in s['goals']:
        st.markdown('### '+html.escape(g['name']))
        st.progress(min(g['saved']/g['target'],1) if g['target'] else 0)
        st.caption(brl(g['saved'])+' de '+brl(g['target']) if g['target'] else 'Definam o valor deste sonho.')
    with st.expander('Editar nossos sonhos'):
        with st.form('goals'):
            new=[]
            for g in s['goals']:
                title=st.text_input('Sonho',g['name'],key='gn_'+g['id'])
                c1,c2=st.columns(2);target=c1.text_input('Meta (R$)',input_brl(g['target']),key='gt_'+g['id']);saved=c2.text_input('Já guardamos (R$)',input_brl(g['saved']),key='gs_'+g['id']);new.append((g['id'],title,target,saved))
            if st.form_submit_button('Salvar sonhos'):
                try:n=deepcopy(s);n['goals']=[{'id':i,'name':title,'target':parse_brl(target),'saved':parse_brl(saved)} for i,title,target,saved in new];commit(n,'Sonhos atualizados.')
                except ValueError as e:st.error(str(e))
    st.caption('Atualização manual. Valores guardados não são descontados automaticamente da renda.')
st.markdown('<div class="section-number">EM TODOS OS UNIVERSOS</div>',unsafe_allow_html=True)
components.html(CAROUSEL,height=350)
st.markdown('<footer>FEITO DE PLANOS, CORAGEM E NÓS DOIS. ♡</footer>',unsafe_allow_html=True)
