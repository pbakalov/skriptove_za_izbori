import pandas as pd 
import plotly.graph_objects as go
import plotly.express as px
import geojson
import numpy as np 

from IPython.display import display 

from .data_loading import station_addresses

nuisance_cols = [
    'place',
    'region',
    'municipality',
    'municipality_name',
    'address',
    'eligible_voters',
    'admin_reg',
    'station',
    'ekatte',
    'region_name'
]

styles = [
    #table properties
    dict(selector=" ", 
         props=[("margin","0"),
                ("font-family",'"Helvetica", "Arial", sans-serif'),
                ("border-collapse", "collapse"),
                ("border","none"),
#                 ("border", "2px solid #ccf")
                   ]),

    #header color - optional
#     dict(selector="thead", 
#          props=[("background-color","#cc8484")
#                ]),
    
    dict(selector="caption", 
         props=[("font-size", "120%"), ("font-weight", "bold")]),

    #background shading
    dict(selector="tbody tr:nth-child(even)",
         props=[("background-color", "#fff")]),
    dict(selector="tbody tr:nth-child(odd)",
         props=[("background-color", "#eee")]),

    #cell spacing
    dict(selector="td", 
         props=[("padding", ".5em")]),

    #header cell properties
    dict(selector="th", 
         props=[("font-size", "100%"),
                ("text-align", "center")]),
]

def make_pretty(styler, caption):
    styler.set_caption(caption).set_table_styles(
        [dict(
            selector="caption", 
            props=[("font-size", "120%"), ("font-weight", "bold")]
        )]
    )
    styler.background_gradient(axis=1, vmin = -100, vmax = 100, subset = [x for x in styler.data if 'спад' in x], cmap="RdYlGn_r")
    styler.format(na_rep = '-', precision = 2)
    return styler

def plot_election_totals(data, top = None, title = ''):
    '''

    Sums data and plots a sorted barchart.

    Parameters
    ----------
    data : df 
        Votes per party and SID.
    top : int or None
        If not None will include the top parties only.
    title : str, default ''
        Optional plot title.
    '''

    totals = data.sum().sort_values(ascending = False)
    
    if top:
        totals = totals[totals.index[:top]]
    
    fig = px.bar(x = totals.index, y = totals, )
    
    fig.update_layout(
        xaxis_title = 'партия',
        yaxis_title = 'гласове',
        title = title,
    )
    
    return fig 
        
def single_party_df(party, april_results, july_results):
    '''
    Returns the results of party per ID + some additional columns:
    - спад, населено място 
    
    Parameters
    ----------
    party : str
        Should be in both april_results.columns and july_results.columns
    april_results : df
        Number of votes per party indexed by station ID or region ID.
    july_results : df 
        Number of votes per party indexed by station ID or region ID.
        
    Returns
    -------
    party_votes : df 
        columns: Votes 1, Votes 2, Drop pct, location
    '''
    if not (party in july_results):
        raise ValueError('party label not in', april_results.columns)
    if not (party in july_results):
        raise ValueError('party label not in', july_results.columns)

    ids = set(april_results.index) | set(july_results.index)
    
    data = pd.DataFrame(index = ids)
    
    data['населено място'] = july_results['place']
    data[f'{party} април'] = april_results[party]
    data[f'{party} юли'] = july_results[party]
    data['спад'] = (data[f'{party} април'] - data[f'{party} юли'])/data[f'{party} април']
    return data 


def party_drop(party, april_results, july_results, min_drop = 80, min_april_votes = 150):
    '''
    Filters results to only show stations where the pct. drop for party is above 
    the threshold ``min_drop`` and the number of votes in april was above ``min_april_votes``.
    
    Parameters
    ----------
    party : string
        A valid party label.
    april_results : df
        Number of votes per party indexed by station ID or region ID.
    july_results : df 
        Number of votes per party indexed by station ID or region ID.
    min_drop : int 
    
    Returns
    -------
    big_drop : df 
        Dataframe containing only stations where drop & number of votes exceeded 
        the specified criteria.
        
        
    '''
    
    data = single_party_df(party, april_results, july_results)
    
    #print (data[((data['спад']>min_drop) & (data[f'{party} април']>min_april_votes))].sum()[:2])
    return data[((data['спад']>min_drop) & (data[f'{party} април']>min_april_votes))]


def all_parties_drops( april_results, july_results):
    '''
    Returns the number of votes for each party party per Station ID in
    April and July + some additional columns:
    * drop (as proportion of april result)
    * location (sourced from July dataframe)
    
    Parameters
    ----------
    april_results : df
        Number of votes per party indexed by station ID or region ID.
    july_results : df 
        Number of votes per party indexed by station ID or region ID.
        
    Returns
    -------
    party_votes : df 
        columns: Votes 1, Votes 2, Drop pct, location
    '''

    parties_both = set(april_results.columns[:-7]) & set(july_results.columns) 
    ids = set(april_results.index) | set(july_results.index)
    
    order = april_results[list(parties_both)].sum().sort_values(ascending = False).index
    
    data = pd.DataFrame(index = [id for id in ids])
    data['населено място'] = july_results['place']

    for party in order:
        data[f'{party} април'] = april_results[party]
        data[f'{party} юли'] = july_results[party]
        data[f'спад {party}'] = (data[f'{party} април'] - data[f'{party} юли'])/data[f'{party} април']
    return data 

def compare_by_sid(
    results1, 
    results2, 
    label1 = 'април', 
    label2 = 'юли',
    include_drops = True,
    drop_abroad = True,
    include_totals =True,
):
    '''
    Returns a dataframe with the number of votes for each party per Station ID
    in both elections + some additional columns:
    * drop per party (as proportion of result1)
    * location (sourced from result2)
    * station address (sourced from Oct 2022)
    
    Only parties that are in both results1 and results2 are returned.
    
    Parameters
    ----------
    results1 : df
        Number of votes per party indexed by station ID
        The initial columns contain party results.
        The last seven columns are assumed to be:
        ['region', 'municipality', 'admin_reg', 'sid', 'region_name', 'place',
       'ekatte']
    results2 : df 
        Number of votes per party indexed by station ID
        The initial columns contain party results.
        The last seven columns are assumed to be:
        ['region', 'municipality', 'admin_reg', 'sid', 'region_name', 'place',
       'ekatte']
    label1 : str, default април
        A label that will be attached to party results from results1
    label2 : str, default юли
        A label that will be attached to party results from results2
    include_drops : bool, default True
        If ``True`` will include the relative drop of support for each party 
    drop_abroad : bool, default False
        If ``True`` will drop station IDs outside of the country (starting with '32')
        
    Returns
    -------
    party_votes : df 
        A dataframe indexed by Station ID.
        Columns: location, ekatte, region, address, party 1 votes 1, party 1 votes 2, party 1 drop pct, etc.
    '''

    last = 10

    parties1 = results1.columns[:-last]
    parties2 = results2.columns[:-last]
    parties_both = set(parties1) & set(parties2)
    ids = set(results1.index) | set(results2.index)
    
    if drop_abroad:
        ids = [x for x in ids if x[:2]!='32']
    
    addr1 = results1['address']
    addr2 = results2['address']
   
    # order descending by totals in results1
    order = results1[list(parties_both)].sum().sort_values(ascending = False).index
   
    # TODO this is not a proper merge; there will be NAs
    data = pd.DataFrame(index = [id for id in ids])
    data['регион'] = results2['region_name']
    data['община'] = results2['municipality_name']
    data['населено място'] = results2['place']
    data['екатте'] = results2['ekatte']

    data[f'адрес {label1}'] = results1['address']
    data[f'адрес {label2}'] = results2['address']

    #data['адрес'] = [x.replace(',', ';') for x in data['адрес'].fillna('не е наличен')]
    
    for party in order:
        data[f'{party} {label1}'] = results1[party]
        data[f'{party} {label2}'] = results2[party]
        if include_drops:
            data[f'{party} спад'] = (data[f'{party} {label1}'] - data[f'{party} {label2}'])/data[f'{party} {label1}']

    if include_totals:
        data[f'общо {label1}'] = results1[parties1].sum(axis = 1)
        data[f'общо {label2}'] = results2[parties2].sum(axis = 1)
        data['общо спад'] = (data[f'общо {label1}'] - data[f'общо {label2}'])/data[f'общо {label1}']
    return data 

def compare_by_ekatte(
    results1,
    results2, 
    label1='април',
    label2='юли',
    drop_abroad = True, 
    include_pct = False,
    include_totals = False,
):
    '''
    Returns a dataframe with the number of votes for each party per EKATTE code 
    in both elections + some additional columns:
    * drop per party (as proportion of result1)
    * location (sourced from result2)
    * 
    
    Only returns parties that participated in both elections.
    
    Parameters
    ----------
    results1 : df
        Number of votes per party indexed by station ID.
        The initial columns contain party results.
        The last seven columns are assumed to be:
        ['region', 'municipality', 'admin_reg', 'sid', 'region_name', 'place',
       'ekatte']
    results2 : df 
        Number of votes per party indexed by station ID.
        The initial columns contain party results.
        The last seven columns are assumed to be:
        ['region', 'municipality', 'admin_reg', 'sid', 'region_name', 'place',
       'ekatte']
    label1 : str, default април
        A label that will be attached to party results from results1
    label2 : str, default юли
        A label that will be attached to party results from results2
    drop_abroad : bool, default True
        If ``True`` will drop EKATTE codes outside of the country (6-digit EKATTE codes starting with '100').
    include_pct : bool, default False
        If ``True``, will include party pct. support.
    include_totals : bool, default False
        If ``True``, will include total votes in each election and total activity drop.
        
    Returns
    -------
    party_votes : df 
        A dataframe indexed by EKATTE code.
        Columns: region, location, party 1 votes 1, party 1 votes 2, party 1 drop pct, etc.
    '''

    parties1 = results1.columns[:-10]
    parties2 = results2.columns[:-10]
    parties_both = set(parties1) & set(parties2)
    print (parties_both) 

    if drop_abroad:
        results1 = results1[results1.index<='320000000'] 
        results2 = results2[results2.index<='320000000'] 


    regions = results1.groupby('ekatte').first()[['region_name','municipality_name', 'place']]
    results1 = results1.groupby('ekatte').sum(numeric_only = True)
    results2 = results2.groupby('ekatte').sum(numeric_only = True)
    ids = set(results1.index) | set(results2.index)
    
    if include_pct:
        pct1 = results1.divide(results1.sum(axis = 1), axis = 0)
        pct2 = results2.divide(results2.sum(axis = 1), axis = 0)
    
    
    order = results1[list(parties_both)].sum().sort_values(ascending = False).index
    
    data = pd.DataFrame(index = [x for x in ids])
    data.index.name = 'ЕКАТТЕ'
    data['регион'] = regions['region_name']
    data['община'] = regions['municipality_name']
    data['населено место'] = regions['place']
    
    for party in order:
        data[f'{party} {label1}'] = results1[party]
        data[f'{party} {label2}'] = results2[party]
        data[f'{party} спад'] = (data[f'{party} {label1}'] - data[f'{party} {label2}'])/data[f'{party} {label1}']
        if include_pct:
            data[f'{party} {label1} %'] = pct1[party]
            data[f'{party} {label2} %'] = pct2[party]
            
    # TODO: include others
    
    if include_totals:
        #print (results1.columns)
        #print (results2.columns)
        data[f'общо {label1}'] = results1[parties1].sum(axis = 1)
        data[f'общо {label2}'] = results2[parties2].sum(axis = 1)
        data['общо спад'] = (data[f'общо {label1}'] - data[f'общо {label2}'])/data[f'общо {label1}']
        
    
    return data 

def summary_plot(data, n): #TODO generalize to any two elections
    '''
    Produces an april-july bar chart, votes broken down by party.
    
    Parameters
    ----------
    data : series
        Index contains party labels + month (each party appears twice).
        E.g. 'ГЕРБ-СДС април', 'ГЕРБ-СДС юли', etc.
    n : int
        Number of stations
    
    Returns
    -------
    summary plot
    '''
    
    fig = go.Figure()
    
    april_ = data.loc[[x for x in data.index if 'април' in x]]
    april_.index = [x[:-6] for x in april_.index]
    april_.name = 'Април'

    july_ = data.loc[[x for x in data.index if 'юли' in x]]
    july_.index = [x[:-4] for x in july_.index]
    july_.name = 'Юли'

    for res in [april_, july_]:
        fig.add_trace(
            go.Bar(
                x = res.index,
                y = res,
                name = res.name,
                text = res.values
            )
        )
        
    fig.update_layout(
        title = f'Въведи филтри в таблицата долу, за да обновиш графиката. Брой секции: {n}',
        font = dict(size = 19)
    )
        
    return fig

def summary_table(data):
    ''' 
    Produces a summary table: April. vs. July votes for parties in data.

    Parameters
    ----------
    data : series
        Index contains party labels + month (each party appears twice).
        E.g. 'ГЕРБ-СДС април', 'ГЕРБ-СДС юли', etc.
    
    Returns
    summ : dataframe
    '''
    
    april_ = data.loc[[x for x in data.index if 'април' in x]]
    april_.index = [x[:-6] for x in april_.index]
    april_.name = 'Април'

    july_ = data.loc[[x for x in data.index if 'юли' in x]]
    july_.index = [x[:-4] for x in july_.index]
    july_.name = 'Юли'
    
    summ_ = pd.DataFrame(index =  april_.index)
    summ_['Април'] = april_.astype(int)
    summ_['Юли'] = july_.astype(int)
    return summ_


def single_ekatte_results(
    aa_by_sid, 
    jj_by_sid, 
    ekatte,
    parties_mvp = [
        'БСП result',
        'ВЪЗРАЖДАНЕ result',
        'ГЕРБ-СДС result',
        'ДБ result',
        'ДПС result',
        'ИТН result',
        'МУТРИ ВЪН! result'
    ]
):
    '''
    Returns april and july results for that single EKATTE code.
    
    Overall votes, votes by party.
    
    Parameters
    ----------
    aa_by_sid : df
        Votes by party + extra info (place names, EKATTE, etc.) for April, indexed by station ID.
    jj_by_sid : df
        Votes by party + extra info (place names, EKATTE, etc.) for July, indexed by station ID.
    ekatte : str 
        EKATTE code.
    parties_mvp : list of str
        A selection of parties to include.
    
    Returns 
    -------
    ekatte_df : dataframe

    '''

    # all station IDs in specified EKATTE in either april or july 
    index = list(set(aa_by_sid.loc[(aa_by_sid['ekatte'] == ekatte)].index) | set(jj_by_sid.loc[(jj_by_sid['ekatte'] == ekatte)].index))
    
    reg_sids = pd.DataFrame(index = index)

    reg_sids['населено место'] = aa_by_sid.loc[(aa_by_sid['ekatte'] == ekatte) ]['place']
    reg_sids['населено место юли'] = jj_by_sid.loc[(jj_by_sid['ekatte'] == ekatte) ]['place']
    
    reg_sids['гласове април'] = aa_by_sid.drop(columns = nuisance_cols).sum(axis=1).loc[reg_sids['населено место'].dropna().index] 
    reg_sids['гласове юли'] = jj_by_sid.drop(columns = nuisance_cols).sum(axis=1).loc[reg_sids['населено место юли'].dropna().index] 

    for party in parties_mvp:
        reg_sids[party.rstrip(' result') + ' април'] = aa_by_sid.loc[(aa_by_sid['ekatte'] == ekatte)][party.rstrip(' result')]
        reg_sids[party.rstrip(' result') + ' юли'] = jj_by_sid.loc[(jj_by_sid['ekatte'] == ekatte)][party.rstrip(' result')]
        
    reg_sids.loc['Общо'] = reg_sids.sum(numeric_only=True)
    #reg_sids['спад %'] = ['{:<5.2f}'.format(x) for x in (reg_sids['гласове април'] - reg_sids['гласове юли'])/reg_sids['гласове април']*100]
    reg_sids['спад %'] = (reg_sids['гласове април'] - reg_sids['гласове юли'])/reg_sids['гласове април']*100
        
    for party in parties_mvp:
        reg_sids[party.rstrip(' result') + ' спад %'] = (
            reg_sids[party.rstrip(' result') + ' април'] - reg_sids[party.rstrip(' result') + ' юли']
        )/reg_sids[party.rstrip(' result') + ' април']*100
        
    #order = ['населено место', 'населено место юли', 'гласове април', 'гласове юли', 'спад %']
    order = ['населено место', 'гласове април', 'гласове юли', 'спад %']
    for party in parties_mvp:
        order += [party.rstrip(' result') + ' април']
        order += [party.rstrip(' result') + ' юли']
        order += [party.rstrip(' result') + ' спад %']
        

    #return reg_sids[list(reg_sids.columns[:4]) + ['спад (%)'] + list(reg_sids.columns[4:-1])].sort_index()
    return reg_sids[order].sort_index()

def single_ekatte_plot(
    april, 
    july, 
    ekatte,
    parties_filter = [
        'БСП', 
        'ВЪЗРАЖДАНЕ', 
        'ГЕРБ-СДС', 
        'ДБ', 
        'ДПС', 
        'ИТН', 
        'МУТРИ ВЪН!'
    ],
    return_fig = False
):
    '''
    
    Parameters
    ----------
    april : dataframe 
        Number of votes by party and station, indexed by Station ID.
    july : dataframe 
        Number of votes by party and station, indexed by Station ID.
    ekatte : int
        EKATTE code
    parties_filter : list of str
        Parties to show.
    return_fig : bool, default False
        If true, will return the figure object.
    '''

    fig = go.Figure()
    
    aa = april.groupby('ekatte').sum(numeric_only = True)
    jj = july.groupby('ekatte').sum(numeric_only = True)

    s = aa.loc[ekatte][parties_filter].copy().sort_values(ascending=False)
    ss = jj.loc[ekatte][parties_filter].copy()

    #s.rename(rename_map, inplace=True)
    #ss.rename(rename_map, inplace = True)
    fig.add_trace(
        go.Bar(x = s.index, y = s, name = 'Април 2021', text=s.values)
    )


    fig.add_trace(
        go.Bar(x = ss.index, y = ss, name = 'Юли 2021', text=ss.values)
    )

    fig.update_layout(
        barmode = 'group',
        title= (
            '{}, МИР {}. Спад на активността: {:<5.2f} % '.format(
                #activity.loc[ekatte]['aj_drop_pct'], 
                april.loc[(april['ekatte'] == ekatte)]['place'].values[0],
                april.loc[(april['ekatte'] == ekatte)]['region_name'].values[0],
                (aa.loc[ekatte].sum() - jj.loc[ekatte].sum())/aa.loc[ekatte].sum()*100,
            )
        ),
        font=dict(
            size=27,
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            x=0.8,
            y=.8,
        ),
    )

    
    fig.update_layout(
        yaxis_title = 'Брой гласове',
        xaxis_title = 'Партия/коалиция',
        height = 650,
#         width = 1200
    )
    #fig.show()

    reg_sids = single_ekatte_results(april, july, ekatte, parties_mvp=s.index)
    
    reg_sids.replace([np.inf, -np.inf], np.nan, inplace = True)

    
    def make_pretty(styler):
        styler.set_caption("{}".format(april.loc[(april['ekatte'] == ekatte)]['place'].values[0])).set_table_styles(
            [dict(
                selector="caption", 
                props=[("font-size", "120%"), ("font-weight", "bold")]
            )]
        )
        styler.background_gradient(axis=1, vmin = -100, vmax = 100, subset = [x for x in reg_sids if 'спад' in x], cmap="RdYlGn_r")
        styler.format(na_rep = '-', precision = 0)
        return styler
   
    if return_fig:
        return reg_sids.style.pipe(make_pretty), fig
    else:
        fig.show()
        return reg_sids.style.pipe(make_pretty)

def sid_to_ekatte(results, station_id):
    '''
    Returns the EKATTE associated with the specified station ID
    
    Parameters
    ----------
    sid : string 
        A valid station ID. Should be in results.index
    results : dataframe
        Dataframe indexed by station ID with a column containing EKATTE data
        
    Returns
    -------
    ekatte : int
        The EKATTE code of the specified station ID
    '''
    return int(results.loc[station_id]['ekatte'])

def ekatte_map(
    data, 
    col,
    labels = {
        'region': 'населено место',
        'aj_drop_pct':'Промяна в активността (%)',
        'aj_drop_votes' : 'Промяна брой гласове ',
        'april' : 'април',
        'july' : 'юли'
    },
    range_color = (15, 80),
    title = None
):
    '''
    Produces an EKATTE map of data[col].
    
    Parameters
    ----------
    data : dataframe
        Contains a column named col to be plotted.
        Indexed by EKATTE (int).
    col : string
        Column of data to plot.
    labels : dict 
        Custom {col_label : display_label} to show on hover.
    range_color : tuple
        Controls the color scale.
    '''
    
    with open("../geojson/settlements.geojson", "r", encoding="utf-8") as f:
        settlements = geojson.load(f)
        
    print ('Брой населени места: ', len(data), col)
    for item in settlements['features']:
        item['id'] = item['properties']['ekatte'] 

    data = data.copy()
    data['ekatte'] = [str(x).zfill(5) for x in data.index]


#     fig = px.choropleth(
    fig = px.choropleth_mapbox(
        data,
        geojson=settlements, 
        locations='ekatte', 
        color=col,
        color_continuous_scale="Viridis",
        range_color=range_color,
        labels=labels, 
        hover_data = list(labels.keys()),
        featureidkey = 'properties.ekatte',
        # choropleth mapbox options
        mapbox_style = 'carto-positron',
        zoom=7, 
        center = {
            "lat": 42.75, 
            "lon": 25.6
        },
    )

    fig.update_layout(
        margin={"r":0, "t":0, "l":0,"b":0},
        #width = 1400,
        #height = 850,
        width = 1200,
        height = 750,
        title = title,
        title_y = 0.95,
        title_x = 0.1,
        font_size = 21
    )
    
    fig.update_layout(
        coloraxis_colorbar=dict(
            title="% подкрепа",
            #thicknessmode="pixels",
            #lenmode="pixels",
            #yanchor="top",y=1,
            #ticks="outside",
            #tickvals=[0,4,8,12],
            #ticktext=["Low", "Low Medium", "High Medium", "High"],
            #dtick=4
        )
    )
    
    return fig

def best_regs_by_party(results, party, top = 40):
    results.sort_values(by = 'БВ %', ascending = False).head(100)
    
    results.replace([np.inf, -np.inf], np.nan, inplace = True)
    
    def make_pretty(styler):
        styler.set_caption(f'Най-добрите {top} резултата на {party}')
        styler.background_gradient(axis=1, vmin = -100, vmax = 100, subset = [x for x in reg_sids if '%' in x], cmap="RdYlGn_r")
        styler.format(na_rep = '-', precision = 0)
        return styler
    
    return results.style.pipe(make_pretty)

def large_drop_loss(
    drops_by_ekatte, 
    min_drop = 0.5, 
    min_votes = 20, 
    parties = [
        'ГЕРБ-СДС',
        'БСП',
        'ДПС',
        'ДБ',
        'ИТН',
        'МУТРИ ВЪН!'
    ]
):
    '''
    Calculates the number of votes lost by a given party in all EKATTE with a drop exceeding ``min_drop`` 
    for said party. 
    
    Parameters
    ----------
    drops_by_ekatte : df 
        Indexed by EKATTE. Contains results by party and the drops per party.
        
    Returns
    -------
    large_drop_loss : df 
    '''
    
    caption = f'Резултати по партии в населени места със спад над {min_drop*100}% в подкрепата за съответната партия\n' + \
        f'през юли спрямо април 2021 и поне {min_votes} гласа за съответната партия през април 2021\n'

    print (caption)
    
    print (
        '{: <15} {: >15} {: >10} {: >10} {: >20}'.format('партия', 'гласове април', 'юли', 'разлика', 'брой населени места')
    )
    
    ldl = pd.DataFrame(
        index = [
            'гласове април', 'гласове юли', 'разлика', 'спад %', 'брой населени места'
        ]
    )

    for party in parties:
        settlements = drops_by_ekatte[
            (drops_by_ekatte[f'{party} април']>min_votes) & 
            (drops_by_ekatte[f'спад {party}']>min_drop)
        ]

        lost_votes = settlements.sum()[[f'{party} април', f'{party} юли']]

        print (
            '{: <15} {: >15d} {: >10d} {: >10d} {: >20d}'.format(
                party, 
                int(lost_votes[[f'{party} април', f'{party} юли'][0]]), 
                int(lost_votes[[f'{party} април', f'{party} юли'][1]]), 
                int(lost_votes[f'{party} април'] - lost_votes[f'{party} юли']),
                len(settlements)
            ) 
        )
        
        

        
        ldl[party] = [
#             party, 
            int(lost_votes[[f'{party} април', f'{party} юли'][0]]), 
            int(lost_votes[[f'{party} април', f'{party} юли'][1]]), 
            int(lost_votes[f'{party} април'] - lost_votes[f'{party} юли']),
            (lost_votes[f'{party} април'] - lost_votes[f'{party} юли'])/lost_votes[f'{party} април']*100,
            int(len(settlements))
        ]

    styles = [
        dict(
            selector="caption",
            props=[
                ("font-size", "150%"),
            ]
        )
    ]
    
    def make_pretty(styler):
        styler.set_caption(caption)
        styler.background_gradient(axis=1, vmin = 0, vmax = 53000, subset = [x for x in styler.data if 'разлика' in x], cmap="RdYlGn_r")
        styler.background_gradient(axis=1, vmin = 0, vmax = 449, subset = [x for x in styler.data if 'брой' in x], cmap="RdYlGn_r")
        styler.format(na_rep = '-', precision = 0)
        styler.format(na_rep = '-', precision = 2, subset = ['спад %'])
#         styler.bar(subset = ['разлика', 'брой населени места'])
        styler.set_table_styles(styles)
        return styler
        
    return ldl.transpose().sort_values('разлика', ascending = False).style.pipe(make_pretty)
        
def sid_selection_plot(
    april, 
    july, 
    sids,
    parties_filter = [
        'БСП', 
        'ГЕРБ-СДС', 
        'ДБ', 
        'ДПС', 
        'ИТН', 
        'МУТРИ ВЪН!',
    ],
    title = '',
    return_fig = False,
):
    '''
    
    Parameters
    ----------
    april : dataframe 
        Number of votes by party and station, indexed by Station ID.
    july : dataframe 
        Number of votes by party and station, indexed by Station ID.
    sids : list of str
        List of station IDs.
    parties_filter : list of str, optional 
        Party names to include.
    title : str, optional, default ''
        Will be displayed above the plot.
    return_fig : bool, default False
        If `True`, will return the figure object.
        
    '''

    fig = go.Figure()
    
    aa = april.drop(columns=nuisance_cols)[april.index.isin(sids)].sum(numeric_only=True)
    jj = july.drop(columns=nuisance_cols)[july.index.isin(sids)].sum(numeric_only=True)
    print ('activity drop:',(aa.sum() - jj.sum())/aa.sum()*100)

    s = aa[parties_filter].copy().sort_values(ascending=False)
    ss = jj[parties_filter].copy()

    fig.add_trace(
        go.Bar(x = s.index, y = s, name = 'Април 2021', text=s.values)
    )


    fig.add_trace(
        go.Bar(x = ss.index, y = ss, name = 'Юли 2021', text=ss.values)
    )

    fig.update_layout(
        barmode = 'group',
        title= (
            '{}. Брой секции: {}, \nСпад на активността: {:<5.2f} % '.format(
                title,
                len(sids),
                (aa.sum() - jj.sum())/aa.sum()*100,
            )
        ),
        font=dict(
            size=27,
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            x=0.8,
            y=.8,
        ),
    )

    
    fig.update_layout(
        yaxis_title = 'Брой гласове',
        xaxis_title = 'Партия/коалиция',
        height = 650,
#         width = 1200
    )

    reg_sids = sid_selection_results(
        april[april.index.isin(sids)], 
        july[july.index.isin(sids)], 
        sids, 
        parties_mvp=s.index
    )
    
    reg_sids.replace([np.inf, -np.inf], np.nan, inplace = True)
    reg_sids.index.name = 'секция'

    
    def make_pretty(styler):
        styler.background_gradient(axis=1, vmin = -100, vmax = 100, subset = [x for x in reg_sids if 'спад' in x], cmap="RdYlGn_r")
        styler.format(na_rep = '-', precision = 0)
        return styler
    
    #display(reg_sids.style.pipe(make_pretty))
    if return_fig:
        return reg_sids.style.pipe(make_pretty), fig
    else:
        fig.show()
        return reg_sids.style.pipe(make_pretty)

def sid_selection_results(
    aa_by_sid, 
    jj_by_sid, 
    sids,
    parties_mvp = [
        'БСП result',
        'ГЕРБ-СДС result',
        'ДБ result',
        'ДПС result',
        'ИТН result',
        'МУТРИ ВЪН! result'
    ]
):
    '''
    Returns april and july results for the selected station IDs.
    
    Overall votes, votes by party.
    
    Parameters
    ----------
    aa_by_sid : df
        Votes by party + extra info (place names, EKATTE, etc.) for April, indexed by station ID.
    jj_by_sid : df
        Votes by party + extra info (place names, EKATTE, etc.) for July, indexed by station ID.
    sids : liust of str 
        List of Station IDs.
    parties_mvp : list of str
        A selection of parties to include.
    
    Returns 
    -------
    ekatte_df : dataframe

    '''

    index = sids
    
    reg_sids = pd.DataFrame(index = index)

    reg_sids['населено место'] = aa_by_sid[aa_by_sid.index.isin(sids)]['place']
    reg_sids['населено место юли'] = jj_by_sid[jj_by_sid.index.isin(sids)]['place']
    
    reg_sids['гласове април'] = aa_by_sid.drop(columns = nuisance_cols).sum(axis=1)[aa_by_sid.index.isin(reg_sids.index)] 
    reg_sids['гласове юли'] = jj_by_sid.drop(columns = nuisance_cols).sum(axis=1)[jj_by_sid.index.isin(reg_sids.index)]
    
    for party in parties_mvp:
        reg_sids[party.rstrip(' result') + ' април'] = aa_by_sid[aa_by_sid.index.isin(sids)][party.rstrip(' result')]
        reg_sids[party.rstrip(' result') + ' юли'] = jj_by_sid[jj_by_sid.index.isin(sids)][party.rstrip(' result')]
    
    reg_sids.loc['Общо'] = reg_sids.sum(numeric_only=True)
    #reg_sids['спад %'] = ['{:<5.2f}'.format(x) for x in (reg_sids['гласове април'] - reg_sids['гласове юли'])/reg_sids['гласове април']*100]
    reg_sids['спад %'] = (reg_sids['гласове април'] - reg_sids['гласове юли'])/reg_sids['гласове април']*100
        
    for party in parties_mvp:
        reg_sids[party.rstrip(' result') + ' спад %'] = (
            reg_sids[party.rstrip(' result') + ' април'] - reg_sids[party.rstrip(' result') + ' юли']
        )/reg_sids[party.rstrip(' result') + ' април']*100
        
    #order = ['населено место', 'населено место юли', 'гласове април', 'гласове юли', 'спад %']
    order = ['населено место', 'гласове април', 'гласове юли', 'спад %']
    for party in parties_mvp:
        order += [party.rstrip(' result') + ' април']
        order += [party.rstrip(' result') + ' юли']
        order += [party.rstrip(' result') + ' спад %']
        

    return reg_sids[order].sort_index()
    
def ekatte_selection_totals(results_by_sid, ekatte_codes, parties_filter):
    '''
    Calculates party totals in regions specified.
    
    Parameters
    ----------
    results_by_sid : df
        DataFrame indexed by station ID.
    ekatte_codes : list
        A list of EKATTE codes.
    parties_filter : list
        List of party labels. Should be in results_by_sid.
        
    Returns
    -------
    s : series
        Totals for the parties in parties_filter and a separate total for all other parties.
        Sorted descending by the number of votes of parties in ``parties_filter``.
    '''
    selection = results_by_sid.groupby('ekatte').sum(numeric_only=True).loc[ekatte_codes].sum()
    s = selection[parties_filter].sort_values(ascending = False)
    other = selection[[x for x in selection.index if x not in parties_filter]]
    s['други'] = other.sum()
    return s
    
def comparison_barplot(series_list, labels = None, title=None, return_fig = False):
    '''
    Produces a comparison bar plot of series in series_list.
    
    Parameters
    ----------
    series_list : list of pd.series
    
    '''

    fig = go.Figure()
    
    if labels is None:
        labels = range(1, len(series_list)+1)
                    
    for i,s in enumerate(series_list):

        fig.add_trace(
            go.Bar(x = s.index, y = s, name = labels[i], text=s.values)
        )


    fig.update_layout(
        barmode = 'group',
        title= (f'{title}'),
        font=dict(
            size=27,
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            x=0.8,
            y=.8,
        ),
    )


    fig.update_layout(
        yaxis_title = 'Брой гласове',
        xaxis_title = 'Партия/коалиция',
        height = 650,
#         width = 1200
    )
    if return_fig:
        return fig
    
    fig.show()
    

def ekatte_selection_plot(
    results1,
    results2,
    ekatte_codes,
    label1 = 'Април 2021',
    label2 = 'Юли 2021',
    parties_filter = [
        'БСП', 
        'ГЕРБ-СДС', 
        'ДБ', 
        'ДПС', 
        'ИТН', 
        'МУТРИ ВЪН!',
    ],
    title = ''
):
    '''
    Produces a barplot of the aggregated results for the selected parties in the specified regions.
    
    TO DO: produce a summary table by EKATTE in addition to the plot.
    
    Parameters
    ----------
    results1 : df
        Results per party indexed by station ID.
    results2 : df
        Results per party indexed by station ID.
    ekatte_codes : list 
        List of valid EKATTE codes.
    label1 : str, default 'Април 2021'
        Optional label to appear in plots.
    label2 : str, default 'Юли 2021'
        Optional label to appear in plots.
        
    '''
    
    s1 = ekatte_selection_totals(results1, ekatte_codes, parties_filter)
    s2 = ekatte_selection_totals(results2, ekatte_codes, parties_filter)
        
#     добави:
#     * брой секции
#     * таблица по екатте
#     * таблица по секции за всяко екатте
#     * заглавие с брой населени места, брой секции, спад на активността 

    act_drop = (s1.sum() - s2.sum())/s1.sum()*100
    
    title = f'{title}. Брой населени места: {len(ekatte_codes)}. Спад на активността: {act_drop:.2f}%'
    
        
    comparison_barplot([s1,s2], labels=[label1, label2], title=title)

def ekatte_selection_comparison_table(
    results1,
    results2,
    ekatte_codes,
    label1 = 'април',
    label2 = 'юли',
    parties_mvp = [
        'БСП', 
        'ГЕРБ-СДС', 
        'ДБ', 
        'ДПС', 
        'ИТН', 
        'МУТРИ ВЪН!',
    ],
    sort_by = None,
    include_total = True,
    caption = ''
):
    
    '''
    Returns result by EKATTE and aggregate results (for all EKATTE codes) for the selected
    parties.
    '''
    
    compare_df = compare_by_ekatte(
        results1, 
        results2,
        label1 = label1,
        label2 = label2,
        include_totals=True
    )
        
    settlements = compare_df[compare_df.index.isin(ekatte_codes)]
    
    if parties_mvp is not None:
        order = ['регион', 'населено место']
        for party in parties_mvp:
            order.append(f'{party} {label1}')
            order.append(f'{party} {label2}')
            order.append(f'спад {party}')
        order+= [f'общо {label1}', f'общо {label2}', f'общо спад']
    else:
        order = settlements.columns

    table = settlements[order]
    
    if sort_by is not None:
        table = table.sort_values(sort_by, ascending = False)
        
    if include_total:
        totals = {}
        
        for col in order:
            if col in ['регион', 'населено место']:
                totals[col] = np.nan
            elif label1 in col or label2 in col and (not 'спад' in col):
                totals[col] = table[col].sum()
            elif 'спад' in col:
                if 'спад' in col[:4]:
                    p = col[5:]
                elif 'спад' in col[-4:]:
                    p = col[:-5]
                else:
                    raise ValueError('unexpected column', col)
                totals[col] = (totals[f'{p} {label1}'] - totals[f'{p} {label2}'])/totals[f'{p} {label1}']
            else:
                raise ValueError('unexpected column', col)
            
           
        table.loc['Общо'] = pd.Series(totals)
    
    table.replace([np.inf, -np.inf], np.nan, inplace = True)

    def make_pretty(styler, caption):
        styler.set_caption(caption)
        styler.background_gradient(axis=1, vmin = -1, vmax = 1, subset = [x for x in styler.data if 'спад' in x], cmap="RdYlGn_r")
        styler.format(na_rep = '-', precision = 2)
#         styler.background_gradient(axis=1, vmin = 100, vmax = 100, subset = [party], cmap="RdYlGn_r")
        return styler
    
    return table.style.pipe(make_pretty, caption = caption)

def large_drop_ekatte(
    results1,
    results2,
    party,
    label1 = 'април',
    label2 = 'юли',
    min_drop = 0.5,
    min_votes = 20,
    sort_by = None,
    parties_mvp = [
        'ГЕРБ-СДС',
        'БСП',
        'ДПС',
        'ДБ',
        'ИТН',
        'МУТРИ ВЪН!'
    ]
):
    '''
    Produces a styled table filtered to include only EKATTE where the drop in support for ``party`` 
    exceeded ``min_drop`` and where the number of votes cast for ``party`` in ``results1`` exceeds
    ``min_votes``.
    
    Parameters
    ----------
    results1 : df
        Number of votes per party indexed by station ID.
        The initial columns contain party results.
        The last seven columns are assumed to be:
        ['region', 'municipality', 'admin_reg', 'sid', 'region_name', 'place',
       'ekatte']
    results2 : df 
        Number of votes per party indexed by station ID.
        The initial columns contain party results.
        The last seven columns are assumed to be:
        ['region', 'municipality', 'admin_reg', 'sid', 'region_name', 'place',
       'ekatte']
    party : str 
        A party label. Should be in ``results1`` and ``results2``.
    label1 : str, default април
        A label that will be attached to party results from results1
    label2 : str, default юли
        A label that will be attached to party results from results2    
    '''
    
    compare_df = compare_by_ekatte(
        results1, 
        results2,
        label1 = label1,
        label2 = label2,
        include_totals=True
    )
        
    ekatte_codes = compare_df[(compare_df[f'{party} {label1}']>min_votes) & (compare_df[f'спад {party}']>min_drop)].index
    
    table = ekatte_selection_comparison_table(
        results1, 
        results2,
        ekatte_codes,
        label1 = label1,
        label2 = label2,
        parties_mvp = parties_mvp,
        sort_by = sort_by
    ).data
    
    for col in table:
        if 'спад' in col:
            table[col] = table[col]*100
            
    table.rename(columns = {col : f'{col} %' for col in table.columns if 'спад' in col}, inplace = True)
        
    caption = f'Населени места с над {min_votes} гласа за {party} през април 2021 и спад в подкрепата за {party} над {min_drop*100}% през юли 2021'
    def make_pretty(styler, caption = 'Тест'):
        styler.set_caption(caption).set_table_styles(
            [dict(
                selector="caption", 
                props=[("font-size", "120%"), ("font-weight", "bold")]
            )]
        )
        styler.background_gradient(axis=1, vmin = -100, vmax = 100, subset = [x for x in styler.data if 'спад' in x], cmap="RdYlGn_r")
        styler.format(na_rep = '-', precision = 2)
        return styler
    
    return table.style.pipe(make_pretty, caption = caption)

def sid_selection_multi_plot(
    results_list,
    sids,
    labels = None,
    parties_filter = [
        'БСП', 
        'ГЕРБ-СДС', 
        'ДБ', 
        'ДПС', 
        'ИТН', 
#         'МУТРИ ВЪН!',
        'ПП'
    ],
    include_others = False, 
    top = None,
    title = '',
    return_fig = True,
):
    '''
    Produces a barplot of the aggregated results for the selected parties in the specified regions.
        
    Parameters
    ----------
    results list : list of df
        Results per election. Each df contains number of votes per party indexed by station ID.
    sids : list 
        List of valid station IDs.
    labels : list of str, optional, default None
        Labels to associate with each election. If ``None`` will simply number results in results_list 
        1,2,3 ... N.
    title : str, default ''
        Optional plot title/table caption.
                
    '''    
    
    ss = []
    
    for res in results_list:
        ss.append(sid_selection_totals(res, sids, parties_filter, include_others = include_others, top = top))
        print (ss[-1])
        
    title = f'{title}. секции: {len(sids)}.'
    
    fig = comparison_barplot(ss, labels = labels, title=title, return_fig = return_fig)
    
    table = sid_selection_multi_table(results_list, labels, sids, ss[0].index)
   
    return table, fig 

def sid_selection_multi_table(results, labels, sids, parties_mvp):
    '''
    Collects results from multiple elections in a signle table.
    
    Parameters
    ----------
    results : list of df 
        Results data, indexed by station ID.
    labels : list of str 
        Labels to attach to each set of results in results.
    sids : list of str 
        Station IDs
    parties_mvp : list of str
        Party labels to focus on. The rest of the parties will be lumped together.
        
    Returns
    -------
    df 
    '''

    index = sids
    
    reg_sids = pd.DataFrame(index = index)
    reg_sids.index.name = 'секция'

#     reg_sids['населено место'] = station_addresses()['place']
    reg_sids['адрес'] = station_addresses()['address']
    
    for i,res in enumerate(results):
        reg_sids[f'гласове {labels[i]}'] = res.drop(columns = nuisance_cols)[res.index.isin(sids)].sum(axis=1) 
    
    for party in parties_mvp:
        for i, res in enumerate(results):
            if party in res:
                reg_sids[f'{party} {labels[i]}'] = res[res.index.isin(sids)][party]
            else:
                reg_sids[f'{party} {labels[i]}'] = [np.nan] * len(sids)
    
    reg_sids.loc['Общо'] = reg_sids.sum(numeric_only=True)
        
#     order = ['населено место', 'адрес']
    order = ['адрес']
    for label in labels:
        order += [f'гласове {label}']
    for party in parties_mvp:
        for label in labels:
            order += [f'{party} {label}']
        

    return reg_sids[order].sort_index()    

def sid_selection_totals(results_by_sid, sids, parties_filter = None, include_others = False, top = None):
    '''
    Calculates party totals in station IDs specified.
    
    Parameters
    ----------
    results_by_sid : df
        DataFrame indexed by station ID.
    sids : list of str
        Station IDs.
    parties_filter : list
        List of party labels. Should be in results_by_sid.
    include_others : bool, default True
        If ``True`` will include a total sum of parties outside of ``parties_filter``.
    top : int, default None
        Will return the top parties results (and possibly others)
        
    Returns
    -------
    s : series
        Totals for the parties in parties_filter and a separate total for all other parties.
        Sorted descending by the number of votes of parties in ``parties_filter``.
    '''
    
    selection = results_by_sid.drop(columns = 'ekatte')[results_by_sid.index.isin(sids)].sum(numeric_only=True)
    
    s = {}
    if parties_filter is None:
        parties_filter = [x for x in selection.index if x !='eligible_voters']
        
    for party in parties_filter:
        print (party)
        if party in selection:
            s[party] = selection[party]
        else:
            s[party] = np.nan
        
    s = pd.Series(s).sort_values(ascending = False)
    
    if top is not None:
        if not isinstance(top, int):
            raise ValueError('top should be int, not', type(top))
        s = s[:top]
    
    if include_others:
        other = selection[[x for x in selection.index if (x not in s.index and x!='eligible_voters')]]
        s['други'] = other.sum()
        
    return s

def compare_by_address(
    results1,
    results2, 
    label1='април',
    label2='юли',
    drop_abroad = True, 
    include_pct = False,
    include_totals = False,
):
    '''
    Returns a dataframe with the number of votes for each party per address 
    in both elections + some additional columns:
    * drop per party (as proportion of result1)
    * location (sourced from result2)
    
    Addresses sourced from October 22 data.
    
    Only returns parties that participated in both elections.
    
    Parameters
    ----------
    results1 : df
        Number of votes per party indexed by station ID.
        The initial columns contain party results.
        The last seven columns are assumed to be:
        ['region', 'municipality', 'admin_reg', 'sid', 'region_name', 'place',
       'ekatte']
    results2 : df 
        Number of votes per party indexed by station ID.
        The initial columns contain party results.
        The last seven columns are assumed to be:
        ['region', 'municipality', 'admin_reg', 'sid', 'region_name', 'place',
       'ekatte']
    label1 : str, default април
        A label that will be attached to party results from results1
    label2 : str, default юли
        A label that will be attached to party results from results2
    drop_abroad : bool, default True
        If ``True`` will drop EKATTE codes outside of the country (6-digit EKATTE codes starting with '100').
    include_pct : bool, default False
        If ``True``, will include party pct. support.
    include_totals : bool, default False
        If ``True``, will include total votes in each election and total activity drop.
        
    Returns
    -------
    party_votes : df 
        A dataframe indexed by EKATTE code.
        Columns: region, location, party 1 votes 1, party 1 votes 2, party 1 drop pct, etc.
    '''

    parties_both = set(results1.columns[:-7]) & set(results2.columns) 
    
    addr = station_addresses()
    
    results1 = results1.copy()
    results2 = results2.copy()
    
    results1['address'] = addr['address']
    results2['address'] = addr['address']
    
    if drop_abroad:
        results1 = results1.loc[[x for x in results1.index if x[:2] !='32']]
        results2 = results2.loc[[x for x in results2.index if x[:2] !='32']]
    
    regions = results1.groupby('address').first()[['region_name','place']]
    
    results1 = results1.groupby('address').sum(numeric_only = True).drop(columns = ['ekatte'])
    results2 = results2.groupby('address').sum(numeric_only = True).drop(columns = ['ekatte'])
    
    ids = set(results1.index) | set(results2.index)
    
    if include_pct:
        pct1 = results1.divide(results1.sum(axis = 1), axis = 0)
        pct2 = results2.divide(results2.sum(axis = 1), axis = 0)
    
    
    order = results1[list(parties_both)].sum().sort_values(ascending = False).index
    
    data = pd.DataFrame(index = [x for x in ids])
    data.index.name = 'адрес'
    data['регион'] = regions['region_name']
    data['населено место'] = regions['place']
    
    for party in order:
        data[f'{party} {label1}'] = results1[party]
        data[f'{party} {label2}'] = results2[party]
        data[f'спад {party}'] = (data[f'{party} {label1}'] - data[f'{party} {label2}'])/data[f'{party} {label1}']
        if include_pct:
            data[f'{party} {label1} %'] = pct1[party]
            data[f'{party} {label2} %'] = pct2[party]
    
    if include_totals:
        data[f'общо {label1}'] = results1.sum(axis = 1)
        data[f'общо {label2}'] = results2.sum(axis = 1)
        data['общо спад'] = (data[f'общо {label1}'] - data[f'общо {label2}'])/data[f'общо {label1}']
        
    
    return data 

def address_selection_comparison_table(
    results1,
    results2,
    addresses,
    label1 = 'април',
    label2 = 'юли',
    parties_mvp = [
        'БСП', 
        'ГЕРБ-СДС', 
        'ДБ', 
        'ДПС', 
        'ИТН', 
        'МУТРИ ВЪН!',
    ],
    sort_by = None,
    include_total = True,
    caption = ''
):
    
    '''
    Similar to ekatte selection plot, but returns result by address in addition to aggregate results.
    '''
    
    compare_df = compare_by_address(
        results1, 
        results2,
        label1 = label1,
        label2 = label2,
        include_totals=True
    )
        
    settlements = compare_df[compare_df.index.isin(addresses)]
    
    if parties_mvp is not None:
        order = ['регион', 'населено место']
        for party in parties_mvp:
            order.append(f'{party} {label1}')
            order.append(f'{party} {label2}')
            order.append(f'спад {party}')
        order+= [f'общо {label1}', f'общо {label2}', f'общо спад']
    else:
        order = settlements.columns

    table = settlements[order]
    
    if sort_by is not None:
        table = table.sort_values(sort_by, ascending = False)
        
    if include_total:
        totals = {}
        
        for col in order:
            if col in ['регион', 'населено место']:
                totals[col] = np.nan
            elif label1 in col or label2 in col and (not 'спад' in col):
                totals[col] = table[col].sum()
            elif 'спад' in col:
                if 'спад' in col[:4]:
                    p = col[5:]
                elif 'спад' in col[-4:]:
                    p = col[:-5]
                else:
                    raise ValueError('unexpected column', col)
                totals[col] = (totals[f'{p} {label1}'] - totals[f'{p} {label2}'])/totals[f'{p} {label1}']
            else:
                raise ValueError('unexpected column', col)
            
           
        table.loc['Общо'] = pd.Series(totals)
    
    table.replace([np.inf, -np.inf], np.nan, inplace = True)

    def make_pretty(styler, caption):
        styler.set_caption(caption)
        styler.background_gradient(axis=1, vmin = -1, vmax = 1, subset = [x for x in styler.data if 'спад' in x], cmap="RdYlGn_r")
        styler.format(na_rep = '-', precision = 2)
#         styler.background_gradient(axis=1, vmin = 100, vmax = 100, subset = [party], cmap="RdYlGn_r")
        return styler
    
    return table.style.pipe(make_pretty, caption = caption)


def large_drop_addresses(
    results1,
    results2,
    party,
    label1 = 'април',
    label2 = 'юли',
    min_drop = 0.5,
    min_votes = 20,
    sort_by = None,
    parties_mvp = [
        'ГЕРБ-СДС',
        'БСП',
        'ДПС',
        'ДБ',
        'ИТН',
        'МУТРИ ВЪН!'
    ]
):
    '''
    Produces a styled table filtered to include only polling locations where the drop in support for ``party`` 
    exceeded ``min_drop`` and where the number of votes cast for ``party`` in ``results1`` exceeds
    ``min_votes``.
    
    Parameters
    ----------
    results1 : df
        Number of votes per party indexed by station ID.
        The initial columns contain party results.
        The last seven columns are assumed to be:
        ['region', 'municipality', 'admin_reg', 'sid', 'region_name', 'place',
       'ekatte']
    results2 : df 
        Number of votes per party indexed by station ID.
        The initial columns contain party results.
        The last seven columns are assumed to be:
        ['region', 'municipality', 'admin_reg', 'sid', 'region_name', 'place',
       'ekatte']
    party : str 
        A party label. Should be in ``results1`` and ``results2``.
    label1 : str, default април
        A label that will be attached to party results from results1
    label2 : str, default юли
        A label that will be attached to party results from results2    
    '''
    
    compare_df = compare_by_address(
        results1, 
        results2,
        label1 = label1,
        label2 = label2,
        include_totals=True
    )
        
    ekatte_codes = compare_df[(compare_df[f'{party} {label1}']>min_votes) & (compare_df[f'спад {party}']>min_drop)].index
    
    table = address_selection_comparison_table(
        results1, 
        results2,
        ekatte_codes,
        label1 = label1,
        label2 = label2,
        parties_mvp = parties_mvp,
        sort_by = sort_by
    ).data
    
    for col in table:
        if 'спад' in col:
            table[col] = table[col]*100
            
    table.rename(columns = {col : f'{col} %' for col in table.columns if 'спад' in col}, inplace = True)
        
    caption = f'Населени места със спад над {min_drop*100}% за {party}'
    def make_pretty(styler, caption = 'Тест'):
        styler.set_caption(caption)
        styler.background_gradient(axis=1, vmin = -100, vmax = 100, subset = [x for x in styler.data if 'спад' in x], cmap="RdYlGn_r")
        styler.format(na_rep = '-', precision = 2)
        return styler
    
    return table.style.pipe(make_pretty, caption = caption)

def string_to_plots(
    res1, 
    res2, 
    s,
    parties_filter=[
        'БСП', 'ГЕРБ-СДС', 'ДБ', 'ДПС', 'ИТН', 'МУТРИ ВЪН!', 'РЕПУБЛИКАНЦИ ЗА БГ'
    ]
):    
    '''
    
    Produces a single plot + table for each address in s.
    
    Parameters
    ----------
    res1 : df
        Results by SID. Columns are party labels.
    res2 : df
        Results by SID. Columns are party labels.
    s: string
        Even lines include addresses, odd lines include space-separated SIDs.
    '''
    s = s.split('\n')
    for i in range(len(s))[::2]:
        name = s[i]
        sids = s[i+1].split()
        sid_selection_plot(
            res1, res2, sids, title = name, 
            parties_filter=parties_filter,
        )
        
        
def get_municipal_ekatte(res, mun_codes):
    
    '''
    res: df
        Results by SID with ekatte column.
    mun: list of str
        List of 4-digit municipal codes (xxyy, where xx is МИР, yy is община within said МИР) 
    '''
    mun_ekatte_codes = {}

    for m in mun_codes:
        codes = res.loc[[x for x in res.index if x[:4]==m]]['ekatte'].unique() 

        mun_ekatte_codes[m] = list(codes)
        
    return mun_ekatte_codes


def get_feudal_municipalities(mun_ekatte_codes, drops_by_ekatte, party, month, min_support = 0.6):
    '''
    
    Parameters
    ----------
    mun_ekatte_codes: dict
        Keys are municipalities (xxyy, xx = region, yy = municipality within reg);
        Values are EKATTE codes.
    drops_by_ekatte: df 
        Results by EKATTE
    party: str
        Party label
    month: str
        Month label, depends on drops_by_ekatte.
    min_support: 
        Municipalities 
        
    Returns
    -------
    list of municipal codes 
    '''

    feudal_mun = []

    for m in mun_ekatte_codes:
        codes = mun_ekatte_codes[m]

        # TO DO: figure out why these throw an error 
        if 17614 in codes or \
        49998 in codes or \
        67074 in codes or \
        18037 in codes or \
        49334 in codes:
            continue 

        totals = drops_by_ekatte.loc[codes].sum()[[f'{party} {month}', f'общо {month}']]
        if totals[0]/totals[1] > min_support:
            feudal_mun.append(m)
            
    return feudal_mun 


def group_by_ekatte(results, include_pct = True, include_totals = True, drop_abroad = True):
    '''
    Takes results by SID and returns results by EKATTE.
    
    
    Parameters
    ----------
    results: df
        Results by SID. Last 7 columns are:
        ['region', 'municipality', 'admin_reg', 'sid', 'region_name', 'place',
       'ekatte']
    drop_abroad: bool, default True
        Drop results abroad.
        
    Returns
    -------
    df 
        Results by EKATTE.
        
    '''
    # TODO: drop SID col from meta, add number of SIDs
    
    
    parties = results.columns[:-7]
    
    if results['ekatte'].isna().sum() > 0: # happens with scraped data from apr23
        print ("nan in ekatte column")
        results = results.copy()
        results['ekatte'] = results['ekatte'].fillna(-1).astype(int)
        
    res = results.groupby('ekatte').sum(numeric_only=True)
        
    if include_pct: 
        pct = res.divide(res.sum(axis = 1), axis = 0)
        for party in parties:
            res[f'{party} %'] = pct[party]*100
            
    if include_totals: 
        totals = res[parties].sum(axis = 1)
        res['Общо'] = totals
            
    meta = results[results.columns[-7:]].groupby('ekatte').first()
    for col in meta:
        res[col] = meta[col]

    if drop_abroad:
        bg_ekatte = [x for x in res.index if not (str(x)[:3] =='100' and len(str(x)) == 6)]
        return res[res.index.isin(bg_ekatte)]
    
    return res

def ekatte_to_sid(ekatte, results):
    '''
    Returns the SIDs in the selected EKATTE.
    
    Parameters
    ----------
    ekatte : int
    results: df
        Results by SID.
        
    Returns
    -------
    list of str 
        List of SIDs in selected EKATTE.
    '''
    
    if (results['ekatte'] == ekatte).sum() > 0:
        return [sid for sid in results[results['ekatte'] == ekatte].index]
    else:
        return []
    
def party_history_plot(
    results_list,
    party, 
    ekatte = None,
    sids = None,
    labels = None, # should match labels
    title = '',
):
    
    '''
    Shows election history over results_list for the selected party and EKATTE/SIDs.
    
    Parameters
    ----------
    results_list : list of df
        Election results.
    party : str
        Party label.
    ekatte : int, optional, default None 
        EKATTE code.
    sids : list of str
        List of station IDs.
    labels : list of str
        Labels to match results_lsit.
    title : str, default ''
        Optional plot title.
        
    Returns
    -------
    plotly figure
    '''
    
    if sids is not None and ekatte is not None:
        raise ValueError('either sids or ekatte should be specified, not both')
    
    ss = []
    
    for res in results_list:
        if ekatte is not None:
            sids = ekatte_to_sid(ekatte, res)
        ss.append(sid_selection_totals(res, sids, [party], include_others = True))     
        
#     title = f'{title}. Брой секции: {len(sids)}.'
#     fig = comparison_barplot(ss, labels = labels, title=title, return_fig = return_fig)
    
    history = pd.DataFrame(ss, index = labels)

    fig = px.bar(data_frame = history, barmode = 'group')
    
    
    fig.update_layout(
        barmode = 'group',
        title= (f'{title}'),
        font=dict(
            size=27,
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            x=0.8,
            y=.95,
            title = 'Партия',
            bgcolor = 'rgba(0,0,0,0)'
        ),
    )


    fig.update_layout(
        yaxis_title = 'Брой гласове',
        xaxis_title = 'Избори',
        #height = 650,
        #width = 1200
    )

    # TO DO: history table
#     table = sid_selection_multi_table(results_list, labels, sids, ss[0].index)
   
    return  fig 

def expand_ekatte(ekatte, places_df, include_ekatte = True): 
    '''
    Gets the region, municipality, and place name associated with
    ``ekatte``.
    
    Parameters
    ----------
    ekatte : int 
    places_df : df
        A dataframe with admin data. Columns:
        * област
        * община
        * населено место
        * ekatte

    Returns
    -------
    title : str
        A string containing region, municipality, place name and ekatte.
    '''
    if isinstance(ekatte, (int,float)):
        row = places_df[places_df['ekatte'] == ekatte]
        place = row["населено место"].values[0]
        mun = row["община"].values[0]
        reg = row["област"].values[0]
        if include_ekatte:
            title = f'{place}, общ. {mun}, обл. {reg} ({ekatte})'
        else:
            title = f'{place}, общ. {mun}, обл. {reg}'
    else:
        row = places_df[places_df['ekatte'].isin(ekatte)]
        title = f'избрани {len(set(ekatte))} населени места'
        
    return title

def ts_data(results, ekatte=None, sids = [], selectedParties=['ГЕРБ-СДС', 'ДПС', 'ГЕРБ']): 
    '''
    Creates a time-series df with basic election metrics for the selected ``ekatte`` for all
    elections in ``results``.

    Default columns:
    * total
    * invalid
    * eligible voters
    * n_stations

    Parameters
    ----------
    results : dict of df
        Each df in ``results`` contains election data. Last 10 columns are meta, the rest of
        the columns are parties (including npn and invalid).
    ekatte : int 
    sids : list of string
        Selected SIDs.
    selectedParties : list, optional, default []
        A list of party names to add in addition to the default columns.

    Returns
    -------
    df
        Indexed by the keys of ``results``.
    '''
    ts_data = {}

    for election in results:
        res = results[election].copy()
        res = add_total(res)

        if ekatte is not None:
            if isinstance(ekatte, (int,float)):
                filtered = res[res['ekatte'] == ekatte]
            else:
                filtered = res[res['ekatte'].isin(ekatte)].copy()
                filtered['place'] = '-'
                filtered['region_name'] = '-'
        elif len(sids)>0:
            #print ('filtering by sid', sids) 
            filtered = res[res.index.isin(sids)]
        else:
            raise ValueError('either ekatte or sids should be specified')
        ts_data[election] = {}
        ts_data[election]['total'] = filtered['total'].sum()
        ts_data[election]['eligible_voters'] = filtered['eligible_voters'].sum()
        ts_data[election]['invalid'] = filtered['invalid'].sum()
        ts_data[election]['n_stations'] = len(filtered)
        ts_data[election]['place'] = filtered['place'].to_list()[0] if len(filtered) else ''
        ts_data[election]['region_name'] = filtered['region_name'].to_list()[0] if len(filtered) else ''
        for party in selectedParties:
            if party in filtered:
                ts_data[election][party] = filtered[party].sum()
            else:
                ts_data[election][party] = 0

    ts_data = pd.DataFrame.from_dict(ts_data, orient = 'index')

    return ts_data

def add_total(result):
    '''
    Adds up all parties' results per row in a 'total' column.
    '''
    parties = result.columns[:-10]
    result = result.copy() 
    result['total'] = result[parties].sum(axis=1)
    
    return result 

def ts_plot(res, places_df, ekatte, selectedParties=['ГЕРБ-СДС', 'ДПС', 'ГЕРБ']):
    '''
    Plots basic election metrics over time for the selected ekatte.

    Parameters
    ----------
    res : dict of df
        Each df in ``results`` contains election data. Last 10 columns are meta, the rest of
        the columns are parties (including npn and invalid).
    places_df : df
        Dataframe with administrative data (region, municipality, place name, ekatte).
    ekatte : int 
    selectedParties : list, optional, default []
        A list of party names to add to the default columns.

    Returns
    
    '''

    df_ts = ts_data(res, ekatte, selectedParties)

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
    )
    
    fig.add_trace(
        go.Scatter(
            x = df_ts.index,
            y = df_ts['total'],
            name = 'Общо гласували',
        ),
        row = 1, col = 1,
    )

    fig.add_trace(
        go.Scatter(
            x = df_ts.index,
            y = df_ts['invalid'],
            name = 'Невалидни',
        ),
        row = 1, col = 1,
    )

    fig.add_trace(
        go.Scatter(
            x = df_ts.index,
            y = df_ts[selectedParties].sum(axis=1),
            name = '+'.join(selectedParties),
        ),
        row = 1, col = 1,
    )

    fig.add_trace(
        go.Scatter(
            x = df_ts.index,
            y = df_ts['eligible_voters'],
            name = 'Избиратели по списък',
        ),
        row = 2, col = 1,
    )

    fig.add_trace(
        go.Scatter(
            x = df_ts.index,
            y = df_ts['n_stations'],
            name = 'Брой секции',
        ),
        row = 3, col = 1,
    )

    fig.update_yaxes(title_text='Гласували', range=[0, max(df_ts['total'])*1.1],  row=1, col=1)
    fig.update_yaxes(title_text='Избиратели по списък', range=[0, max(df_ts['eligible_voters'])*1.1], row=2, col=1)
    fig.update_yaxes(title_text='Брой секции', range=[0, max(df_ts['n_stations'])*1.1], row=3, col=1)
    
    fig.update_layout(
        title = expand_ekatte(ekatte, places_df),
        height = 900,
    )

    return fig    

def ts_snapshot(
    res, 
    places_df, 
    ekatte=None,
    sids = [], 
    selectedParties=['ГЕРБ-СДС', 'ДПС', 'ГЕРБ'],
    sum_selected=False,
    title = None,
    include_eligible = False,
    include_invalid = False,
    include_total = False,
):
    '''
    Plots basic election metrics over time for the selected ekatte.
    All in one plot.

    Parameters
    ----------
    res : dict of df
        Each df in ``results`` contains election data. Last 10 columns are meta, the rest of
        the columns are parties (including npn and invalid).
    places_df : df
        Dataframe with administrative data (region, municipality, place name, ekatte).
    ekatte : int 
    sids: list of str
    selectedParties : list, optional, default []
        A list of party names to add to the default columns.

    Returns
    
    '''

    df_ts = ts_data(res, ekatte, sids, selectedParties)

    fig = go.Figure()
    
    used_cols = [p for p in selectedParties]
    
    if include_total:
        fig.add_trace(
            go.Scatter(
                x = df_ts.index,
                y = df_ts['total'],
                name = 'Общо гласували',
                mode = 'lines+markers+text',
                line = dict(width = 5),
                marker = dict(size = 15), 
                text = df_ts['total'],
                textposition = 'top center',
            )
        )
        used_cols.append('total')

    if include_invalid:
        fig.add_trace(
            go.Scatter(
                x = df_ts.index,
                y = df_ts['invalid'],
                name = 'Невалидни',
                mode = 'lines+markers+text',
                line = dict(width = 5),
                marker = dict(size = 15), 
                text = df_ts['invalid'],
                textposition = 'top center',
            )
        )
        used_cols.append('invalid')

    if include_eligible:
        fig.add_trace(
            go.Scatter(
                x = df_ts.index,
                y = df_ts['eligible_voters'],
                name = 'Избиратели по списък',
                mode = 'lines+markers+text',
                line = dict(width = 5),
                marker = dict(size = 15), 
                text = df_ts['eligible_voters'],
                textposition = 'top center',
            )
        )
        used_cols.append('eligible_voters')
    
    if not sum_selected:
        for p in selectedParties:
            fig.add_trace(
                go.Bar(
                    x = df_ts.index,
                    y = df_ts[p],
                    name = p,
                    text = df_ts[p],
                )
            )
    else:
        fig.add_trace(
            go.Scatter(
                x = df_ts.index,
                y = df_ts[selectedParties].sum(axis=1),
                mode = 'lines+markers+text',
                name = '+'.join(selectedParties),
                line = dict(width = 5),
                marker = dict(size = 15),
                text = df_ts[selectedParties].sum(axis=1),
                textposition = 'top center',
            )
        )
        
    # TODO possibly include n_stations 
    fig.update_yaxes(title_text='Гласували', range=[
        0, 
        max(
            df_ts[used_cols].max().max()*1.1,
            df_ts[selectedParties].sum(axis=1).max()*1.1
        )
    ])
    
    # TODO add SIDs as annotation 
    if title is None:
        try:
            title = expand_ekatte(ekatte, places_df) 
        except:
            ekatte = sid_to_ekatte(res[list(res.keys())[-1]], sids[0])
            title = expand_ekatte(ekatte, places_df) + f'. избрани {len(sids)} секции'
        
    fig.update_layout(
        title = title, # expand_ekatte(ekatte, places_df),
        height = 900,
        width = 1400,
        font = dict(size = 25),
        showlegend = True,
        barmode = 'stack',
    )

    return fig    
