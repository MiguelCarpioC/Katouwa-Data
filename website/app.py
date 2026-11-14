'''KATOUWA evidence-first hackathon showcase — every tab works offline.

If NASA cannot be fetched, all charts derived from generated data are explicitly
labelled as SYNTHETIC DEMO. The historical information is separately attributed.
'''
from __future__ import annotations
from pathlib import Path
import json, math, subprocess, sys
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from analysis import validate, annual_aggregate, trend
from living_signal import create_sonification_wav, frequency_hz

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='KATOUWA | Two Skies, One Territory', page_icon='🌿', layout='wide')
st.markdown('''<style>
.stApp {background:#091c24;color:#f0f3ec}
[data-testid="stSidebar"] {background:#13242c}
h1,h2,h3 {color:#f1f4ed!important}
.k-hero {padding:24px 28px;background:linear-gradient(110deg,#163f38 0%,#183644 48%,#111d30 100%);border:1px solid #416157;border-radius:16px;margin-bottom:16px}
.k-small {font-size:11px;font-weight:750;color:#a6d5bb;letter-spacing:2px}
.k-title {font-size:41px;font-weight:800;line-height:1.15;color:#f4f6ef;margin:8px 0}
.k-sub {font-size:17px;color:#c8dcd2}
.k-note {background:#1c3037;border-left:4px solid #bca86e;padding:12px 16px;border-radius:6px;margin:10px 0}
[data-testid="stMetric"] {background:#193139;border:1px solid #3a5d58;border-radius:12px;padding:12px}
</style>''',unsafe_allow_html=True)

def photo(filename,caption):
    path=ROOT/'assets'/filename
    if path.exists(): st.image(str(path),use_container_width=True,caption=caption)

def subtitle(t):
    st.markdown(f'#### {t}')

config=json.loads((ROOT/'config'/'sites.json').read_text(encoding='utf-8'))
points=pd.DataFrame([{'point':p['id'],'lat':p['latitude'],'lon':p['longitude']} for p in config['sites']])

manifest_path=ROOT/'reports'/'run_manifest.json'
try: manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
except Exception: manifest={'status':'UNKNOWN'}
real_file=ROOT/'data'/'processed'/'real_nasa_observations.csv'
verified_available=real_file.exists() and manifest.get('status') in ('SUCCESS','SUCCESS_WITH_WARNINGS') and bool(manifest.get('sources_trace'))

st.sidebar.markdown('## 🌿 KATOUWA')
st.sidebar.caption('Earth System Trend Detective · Scientific evidence + community context')
options=['Guided showcase (illustrative data)']
if verified_available: options.insert(0,'NASA retrieved & quality-filtered')
options.append('Upload sourced CSV')
mode=st.sidebar.radio('Data shown in charts', options, index=0)
if mode=='NASA retrieved & quality-filtered':
    data=pd.read_csv(real_file); data_label='REAL NASA API / see provenance manifest'; is_demo=False
elif mode=='Upload sourced CSV':
    u=st.sidebar.file_uploader('Upload CSV: date, site, variable, value',type=['csv'])
    if u:
        try:
            data=validate(pd.read_csv(u)); data_label='USER UPLOAD — provenance not verified';is_demo=False
        except Exception as exc:
            st.sidebar.error(str(exc));data=pd.read_csv(ROOT/'data'/'demo_TWO_POINTS_SYNTHETIC.csv');data_label='SYNTHETIC DEMO';is_demo=True
    else:
        data=pd.read_csv(ROOT/'data'/'demo_TWO_POINTS_SYNTHETIC.csv'); data_label='SYNTHETIC DEMO until CSV is uploaded';is_demo=True
else:
    data=pd.read_csv(ROOT/'data'/'demo_TWO_POINTS_SYNTHETIC.csv'); data_label='SYNTHETIC DEMO — NOT NASA OBSERVATIONS'; is_demo=True
try: data=validate(data)
except Exception as exc:
    st.error(f'The selected dataset could not be parsed: {exc}')
    st.stop()
if 'is_qa_valid' in data:
    good=data['is_qa_valid'].astype(str).str.lower().isin(('true','1'))
    data=data.loc[good].copy()

st.sidebar.markdown('---')
st.sidebar.write('**Data integrity**')
if is_demo:
    st.sidebar.error('All trend graphs are illustrative. No verified NASA observations are loaded.')
else:
    st.sidebar.success('Using the explicitly selected data source. Review provenance before making conclusions.')
st.sidebar.markdown('---')
st.sidebar.write('**NASA data connection**')
st.sidebar.caption(f'Last attempt: {manifest.get("status", "UNKNOWN")}')
with st.sidebar.expander('Retrieve NASA (optional; limited timeout)'):
    st.caption('Try one location and one year first. May be unavailable during the event. The research and demo tabs remain usable offline.')
    if st.button('Quick 2024 P1 retrieval',key='quick'):
        cmd=[sys.executable,str(ROOT/'run_agents.py'),'--source','modis','--site','MANGROVE_POINT_1','--start','2024','--end','2024']
        try:
            with st.spinner('Downloading from NASA ORNL (can take several minutes; stops after 15 minutes)…'):
                r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=900)
            latest=json.loads(manifest_path.read_text(encoding='utf-8'))
            if r.returncode==0 and latest.get('failures'):
                st.warning('Partial NASA data retrieved; some requests failed. Click again to resume, or refresh to use what was downloaded.')
            elif r.returncode==0:
                st.success('Retrieved data. Refresh this webpage to select it.')
            else:
                st.warning('NASA unavailable. Showcase remains ready.')
            with st.expander('Technical diagnostics'): st.code((r.stderr+'\n'+r.stdout)[-2800:]); st.json(latest.get('failures',[]))
        except subprocess.TimeoutExpired:
            st.warning('NASA request reached the 15-minute limit; no values fabricated. Downloaded pieces are cached: click again to resume.')

st.markdown('''<div class="k-hero"><div class="k-small">NASA SPACE APPS 2026 • EARTH SYSTEM TREND DETECTIVE</div><div class="k-title">KATOUWA · TWO SKIES</div><div class="k-sub">The satellite observes from above. The territory knows from within.</div></div>''',unsafe_allow_html=True)
if is_demo:
    st.warning('🚧 SCIENCE PREVIEW: the NDVI/EVI charts and Living Signal use INVENTED, illustrative values. They are NOT NASA measurements or proof of mangrove change. Historical research and supplied photographs are separate, attributed evidence.')
else:
    st.info('Data source: '+data_label+'. Always inspect source and quality before interpreting.')

t1,t2,t3,t4,t5=st.tabs(['01 · The place','02 · Earth trends','03 · Two skies','04 · Living signal','05 · Evidence & action'])

with t1:
    a,b=st.columns([1.2,1])
    with a:
        st.markdown('### Santa Rosa de Agua, Lake Maracaibo')
        st.write('A community whose stilt-house landscape and coastal ecology motivate an investigation into mangrove change. KATOUWA connects Earth-observation measurements with historically documented community perspectives.')
        m1,m2,m3=st.columns(3)
        m1.metric('Historical survey', '50', help='2007 thesis abstract: 50 persons/homes studied; not a current population count')
        m2.metric('Candidate locations','2',help='User-selected map points; not mapped mangrove boundaries')
        m3.metric('NASA observations', 'Available' if verified_available else 'Not yet',help='Based on latest verified pipeline manifest')
        st.markdown('**The four scientific questions**: What changed? Where? How much? Is the trend statistically meaningful?')
        st.caption('Source for historical survey: Lissett Spelorzi, URU, 2007, thesis abstract. Other information: team project dossier. Photos: supplied team materials; date/location and reuse permissions to verify.')
    with b:
        photo('water_community.jpg','Supplied photograph of stilt houses and water (exact date/location not independently verified)')
    st.markdown('### Two selected observation points')
    left,right=st.columns([1,1])
    with left:
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=points.lon,y=points.lat,mode='markers+text',text=['P1','P2'],textposition='top center',marker=dict(size=20,color=['#6fd4ba','#e5b76a']),showlegend=False))
        fig.update_layout(title='Relative geographic positions (not satellite imagery)',xaxis_title='Longitude, °W (negative)',yaxis_title='Latitude, °N',height=310,template='plotly_dark',paper_bgcolor='#0e242c',plot_bgcolor='#0e242c',margin=dict(l=15,r=15,t=55,b=15))
        st.plotly_chart(fig,use_container_width=True)
    with right:
        st.dataframe(points,hide_index=True,use_container_width=True)
        st.info('These locations were selected as candidate mangrove points. MODIS 250 m pixels may mix water, soil, buildings and vegetation, so NDVI is not a direct estimate of mangrove-cover loss.')

with t2:
    st.markdown('### Earth System Trend Detective')
    st.caption('Plots below are sourced from the selected data mode: '+data_label)
    c1,c2=st.columns(2)
    with c1: variable=st.selectbox('What variable?',sorted(data.variable.unique()),key='var2')
    with c2: selected_sites=st.multiselect('Which locations?',sorted(data.site.unique()),default=sorted(data.site.unique()),key='sites2')
    df=data.loc[(data.variable==variable)&(data.site.isin(selected_sites))].copy()
    if df.empty: st.warning('No records for this combination.')
    else:
        fig=go.Figure()
        palette=['#75e5c2','#eab56c','#a1b3ff']
        for idx,(sid,g) in enumerate(df.groupby('site')):
            fig.add_trace(go.Scatter(x=g.date,y=g.value,mode='lines+markers',name=sid.replace('MANGROVE_POINT_','P'),line=dict(width=2,color=palette[idx%3]),marker=dict(size=4)))
        fig.update_layout(title=f'{variable} observations · {"ILLUSTRATIVE" if is_demo else "source shown above"}',height=370,xaxis_title='Date',yaxis_title=variable,template='plotly_dark',paper_bgcolor='#0e242c',plot_bgcolor='#0e242c',legend=dict(orientation='h',y=1.12),margin=dict(l=25,r=25,t=60,b=35))
        st.plotly_chart(fig,use_container_width=True)
        st.markdown('#### Annual comparison & statistical method')
        out=[]
        for sid,g in df.groupby('site'):
            ag=annual_aggregate(g)
            ag=ag.loc[ag['count']>=10]
            x=trend(ag) if len(ag)>=6 else {'valid':False,'reason':'Fewer than six eligible years'}
            out.append({'Location':sid.replace('MANGROVE_POINT_','P'),'Years':len(ag),'Theil–Sen slope/year':round(x['slope'],5) if x.get('valid') else None,'Kendall p (exploratory)':round(x['p'],4) if x.get('valid') else None, 'Evidence': 'SYNTHETIC DEMO — NO SCIENTIFIC CONCLUSION' if is_demo else 'Review QA and pixel-mixing limitations'})
        st.dataframe(pd.DataFrame(out),hide_index=True,use_container_width=True)
        st.caption('Annual medians with at least 10 QA-accepted observations per year; exploratory Theil–Sen and Kendall trend test. Serial correlation and seasonal trends require further analysis.')
        if is_demo: st.error('Illustrative trajectories and computed p-values are not findings about Venezuela. Do not quote them in the pitch as NASA results.')
        st.download_button('Export current view (with source labels)',df.to_csv(index=False).encode(),file_name='KATOUWA_preview_OR_source.csv',mime='text/csv')

with t3:
    st.markdown('### Two skies: two independent kinds of evidence')
    a,b=st.columns(2)
    with a:
        photo('mangrove_roots.jpg','Supplied image: mangrove aerial-root structure; exact site/date unverified')
        st.markdown('#### From above · NASA Earth observations')
        st.write('Spectral vegetation indices, time series, temporal comparisons, quality flags, and explicit uncertainty. No satellite can directly read a fishing account or cultural memory.')
    with b:
        photo('water_community.jpg','Supplied image of a waterside community; provenance to be confirmed')
        st.markdown('#### From within · community and research')
        st.write('A 2007 field study surveyed approximately 50 people/households in Capitán Chico. The abstract reports that participants understood mangroves’ livelihood value and identified insufficient institutional support.')
    st.markdown('### Community observations / annotated evidence')
    st.info('2007 documented survey → baseline research context. Contemporary field observations, dated interviews and audio require consent and verification before integrating them as community records.')
    history=pd.read_csv(ROOT/'data'/'historical_claims.csv')
    st.dataframe(history[['period','event','finding','verification_status']],use_container_width=True,hide_index=True)
    st.caption('Citation: Spelorzi (2007), *Destrucción del Mangle y la Percepción de los Habitantes de Santa Rosa Sobre la Incidencia en su Calidad de Vida*, Universidad Rafael Urdaneta.')

with t4:
    st.markdown('### The Living Signal · data translated into geometry')
    st.write('The circle below is a **mathematical visualization of the selected index**, not a sensor, a physical Chladni experiment, or an independent ecological-health diagnosis.')
    c1,c2,c3=st.columns([1,1,1])
    with c1: chosen=st.selectbox('Location',sorted(data.site.unique()),key='sigsite')
    with c2: index=st.selectbox('Index',sorted(data.variable.unique()),key='sigindex')
    signal_df=data[(data.site==chosen)&(data.variable==index)].sort_values('date')
    if signal_df.empty: st.warning('No selected signal available')
    else:
        with c3: position=st.slider('Time step',0,len(signal_df)-1,len(signal_df)-1,key='sigtime')
        signal=signal_df.iloc[position]
        v=float(signal.value)
        angle=np.linspace(0,2*np.pi,361)
        # Fixed deterministic *artistic mapping*, no implied physical frequency.
        normalized=float(np.clip((v+1)/2,0,1)) if index in ('NDVI','EVI') else float(1/(1+np.exp(-v/15)))
        radius=1.05+0.20*normalized+0.055*np.cos(7*angle+normalized*2*np.pi)+0.028*np.sin(13*angle+normalized*3)
        signalfig=go.Figure(go.Scatter(x=radius*np.cos(angle),y=radius*np.sin(angle),mode='lines',line=dict(color='#7ee8c8',width=4),fill='toself',fillcolor='rgba(54,155,139,.15)',name='Signal'))
        for rr in [.7,1.0,1.25]:signalfig.add_shape(type='circle',xref='x',yref='y',x0=-rr,y0=-rr,x1=rr,y1=rr,line=dict(color='rgba(159,185,176,.22)',width=1))
        signalfig.update_layout(height=420,template='plotly_dark',paper_bgcolor='#0e242c',plot_bgcolor='#0e242c',xaxis=dict(visible=False,scaleanchor='y',range=[-1.42,1.42]),yaxis=dict(visible=False,range=[-1.42,1.42]),margin=dict(l=15,r=15,t=20,b=10),showlegend=False)
        a,b=st.columns([1.45,1])
        with a: st.plotly_chart(signalfig,use_container_width=True)
        with b:
            st.metric(f'{index} at selected date',f'{v:.3f}')
            st.write(f'**Date:** {signal.date.date()}')
            st.write(f'**Location:** {chosen}')
            st.write('**Geometry mapping:** radius = 1.05 + 0.20 × normalized signal + periodic decorative harmonics. The periodic terms are for legibility, not a measured sound frequency.')
            st.caption('Value and geometry: '+data_label)
            if is_demo: st.warning('SYNTHETIC · This animation-ready concept uses fabricated numbers, not environmental truth.')
        st.markdown('#### Hear the same numerical signal (optional)')
        st.caption('This audio is a computer-generated translation of numerical values. It is NOT a field recording, Indigenous music, or an environmental microphone.')
        try:
            wav = create_sonification_wav(signal_df['value'].tail(42).values)
            st.audio(wav, format='audio/wav')
            st.caption('Deterministic formula for NDVI/EVI: frequency = 220 + 440 × clip((index + 1) / 2, 0, 1) Hz. The notes follow the observation order; duration is compressed for demonstration.')
        except Exception as sound_exc:
            st.info('Sound preview unavailable: ' + str(sound_exc))
        st.markdown('#### Read the underlying series alongside the artistic translation')
        mini=go.Figure(go.Scatter(x=signal_df.date,y=signal_df.value,mode='lines',line=dict(color='#e7b36a',width=2)))
        mini.add_vline(x=signal.date.timestamp()*1000,line_color='#6fd4ba',line_dash='dash')
        mini.update_layout(height=200,template='plotly_dark',paper_bgcolor='#0e242c',plot_bgcolor='#0e242c',margin=dict(l=0,r=0,t=15,b=15))
        st.plotly_chart(mini,use_container_width=True)

with t5:
    st.markdown('### Evidence audit & action pathway')
    a,b,c=st.columns(3)
    a.metric('Satellite pipeline',manifest.get('status','UNKNOWN'))
    b.metric('Research source','2007')
    c.metric('Restoration proposal','CONCEPT')
    st.markdown('#### Evidence ladder')
    st.markdown('''
1. **[DOCUMENTED]** A 2007 thesis conducted a survey in Capitán Chico, providing historical community context — not current ecological measurements.
2. **[OBSERVATION PENDING]** NASA NDVI/EVI measurements require a successful retrieval or a sourced upload; no real ecological trend may be claimed until then.
3. **[PHOTO SOURCE UNVERIFIED]** Team-supplied images can illustrate the environment; image metadata, capture location and public-use consent must be checked.
4. **[CONCEPT]** Ñeruna biomimetic floating islands are proposed experimental structures, not a deployed remediation system.
''')
    st.markdown('#### From evidence to local action')
    c1,c2,c3=st.columns(3)
    c1.info('**01 · Detect**\n\nMonitor environmental indices and report data quality.')
    c2.info('**02 · Ground-truth**\n\nInvite community-led field checks and informed consent.')
    c3.info('**03 · Prototype**\n\nTest in situ sensors and biomimetic concepts before scaling.')
    st.markdown('#### Last NASA collection diagnostics')
    with st.expander('Raw machine-readable manifest'):
        st.json(manifest)
    st.markdown('#### References')
    st.markdown('- [NASA ORNL DAAC MODIS subsetting API](https://modis.ornl.gov/data/modis_webservice.html)')
    st.markdown('- [NASA POWER meteorological service](https://power.larc.nasa.gov/docs/services/api/temporal/monthly/)')
    st.markdown('- Spelorzi, L. (2007). *Destrucción del Mangle y la Percepción de los Habitantes de Santa Rosa Sobre la Incidencia en su Calidad de Vida*. Universidad Rafael Urdaneta (user-provided thesis).')
    st.markdown('- User-provided KATOUWA technical dossier and field-image archive. Attribution and permissions pending review.')
