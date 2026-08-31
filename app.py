import os, json, re
from datetime import datetime
import pandas as pd
import requests
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title='Skylark BI Agent', page_icon='📊', layout='wide')

MONDAY_URL='https://api.monday.com/v2'

@st.cache_data(ttl=300)
def monday_query(query, variables=None):
    token=os.getenv('MONDAY_API_TOKEN','').strip()
    if not token: raise RuntimeError('MONDAY_API_TOKEN is not configured.')
    r=requests.post(MONDAY_URL, json={'query':query,'variables':variables or {}}, headers={'Authorization':token,'Content-Type':'application/json'}, timeout=30)
    r.raise_for_status(); data=r.json()
    if data.get('errors'): raise RuntimeError('; '.join(x.get('message','Monday API error') for x in data['errors']))
    return data['data']

def get_boards():
    ids=[]
    for key in ('MONDAY_DEALS_BOARD_ID','MONDAY_WORK_ORDERS_BOARD_ID'):
        if os.getenv(key): ids.append(int(os.getenv(key)))
    if not ids: raise RuntimeError('Configure MONDAY_DEALS_BOARD_ID and MONDAY_WORK_ORDERS_BOARD_ID.')
    q='query($ids:[ID!]){boards(ids:$ids){id name columns{id title type} items_page(limit:500){items{id name column_values{id text value type}}}}}'
    return monday_query(q, {'ids':ids})['boards']

def board_to_df(board):
    cols={c['id']:c['title'] for c in board['columns']}
    rows=[]
    for item in board['items_page']['items']:
        row={'_item_name':item['name']}
        for cv in item['column_values']:
            row[cols.get(cv['id'],cv['id'])]=cv.get('text') or ''
        rows.append(row)
    return pd.DataFrame(rows)

def clean_df(df):
    x=df.copy()
    x.columns=[re.sub(r'\s+',' ',str(c)).strip() for c in x.columns]
    for c in x.columns:
        if x[c].dtype=='object': x[c]=x[c].fillna('').astype(str).str.strip()
    return x

def compact_data(deals, work):
    # Keep prompt size bounded while preserving useful business fields.
    def pick(df, words):
        return [c for c in df.columns if any(w in c.lower() for w in words)]
    dcols=pick(deals,['deal','owner','client','status','date','prob','value','stage','sector','product'])[:14]
    wcols=pick(work,['deal','customer','execution','date','sector','work','amount','billed','collect','receiv','invoice','status','quantity'])[:22]
    return deals[dcols].head(500).to_dict('records'), work[wcols].head(500).to_dict('records')

def answer(question, deals, work):
    key=os.getenv('OPENAI_API_KEY','').strip()
    if not key: raise RuntimeError('OPENAI_API_KEY is not configured.')
    client=OpenAI(api_key=key)
    d,w=compact_data(deals,work)
    system='''You are Skylark Drones founder-level business intelligence agent. Answer using only the supplied Monday.com data. Be concise but insightful. Calculate when useful. State assumptions and data-quality caveats. If the question is ambiguous, ask one focused clarification. Never invent missing values. For money, use INR formatting. For pipeline, distinguish open deals from closed/completed outcomes and use closure probability only when present. Cross-reference Deals and Work Orders when useful.'''
    payload=json.dumps({'deals':d,'work_orders':w}, default=str)
    resp=client.responses.create(model=os.getenv('OPENAI_MODEL','gpt-4.1-mini'), input=[{'role':'system','content':system},{'role':'user','content':f'Question: {question}\n\nMonday.com data snapshot:\n{payload}'}])
    return resp.output_text

st.title('📊 Skylark Drones — Monday.com BI Agent')
st.caption('Read-only prototype • dynamically reads Deals and Work Orders from Monday.com')

try:
    boards=get_boards()
    deals=clean_df(board_to_df(next(b for b in boards if b['id']==str(os.getenv('MONDAY_DEALS_BOARD_ID')))))
    work=clean_df(board_to_df(next(b for b in boards if b['id']==str(os.getenv('MONDAY_WORK_ORDERS_BOARD_ID')))))
    c1,c2,c3=st.columns(3)
    c1.metric('Deals records',len(deals)); c2.metric('Work orders',len(work)); c3.metric('Boards connected',len(boards))
    with st.expander('Data quality / preview'):
        st.write('Blank values are retained and communicated to the agent. Column names are normalized for analysis.')
        st.dataframe(deals.head(10), use_container_width=True)
        st.dataframe(work.head(10), use_container_width=True)
except Exception as e:
    st.error(f'Connection/setup issue: {e}')
    st.info('Set MONDAY_API_TOKEN, MONDAY_DEALS_BOARD_ID, MONDAY_WORK_ORDERS_BOARD_ID and OPENAI_API_KEY in the deployment secrets, then reload.')
    st.stop()

if 'messages' not in st.session_state: st.session_state.messages=[]
for m in st.session_state.messages:
    with st.chat_message(m['role']): st.markdown(m['content'])

q=st.chat_input('Ask a founder-level question… e.g. “How is our pipeline looking by sector?”')
if q:
    st.session_state.messages.append({'role':'user','content':q})
    with st.chat_message('user'): st.markdown(q)
    with st.chat_message('assistant'):
        with st.spinner('Analyzing Monday.com data…'):
            try: a=answer(q,deals,work)
            except Exception as e: a=f'Unable to answer safely: {e}'
        st.markdown(a)
    st.session_state.messages.append({'role':'assistant','content':a})
