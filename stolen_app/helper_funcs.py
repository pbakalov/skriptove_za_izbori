import pandas as pd 
import plotly.graph_objects as go
import plotly.express as px
import geojson
import numpy as np 

def load_votes_data(month):
    '''
    Loads votes data for either april or july.
    
    Parameters
    ----------
    month : {'april', 'july', 'oct22'}
    
    Returns
    -------
    votes : dataframe
        Indexed by polling station ID. 
        Columns are party names + suffix indicating the month.
        
    '''
    if month == 'april':
        april = pd.read_csv('votes_04.04.2021_padded.csv', index_col = [0], dtype = {'station no': str})
        april = april[['station no'] + [n for n in april if ('result' in n and 'paper' not in n and 'machine' not in n)]]
        april_ = april.groupby('station no').sum()
        april_.rename(columns = {x : x[:-7] for x in april_}, inplace = True)
        return april_
    
    elif month == 'july':
        july = pd.read_csv('votes_11.07.2021_padded.csv', index_col = [0], dtype = {'station no': str})
        july_ = july[['station no'] + [n for n in july if 'result' in n]].groupby('station no').sum()
        july_.rename(columns = {x : x[:-7] for x in july_}, inplace = True)
        return july_
    
    elif month == 'oct22':
        data = pd.read_csv('votes_02.10.2022_padded.csv', index_col = [0], dtype = {'station no': str})
        data_ = data[['station no'] + [n for n in data if 'result' in n]].groupby('station no').sum()
        data_.rename(columns = {x : x[:-7] for x in data_}, inplace = True)
        return data_
        
    else:
        raise ValueError('expected july, april, or oct22, got', month)

def load_station_locations(month):
    '''
    Loads polling station location data for either april or july.
    
    Parameters
    ----------
    month : {'april', 'july', 'oct22'}
    
    Returns
    -------
    stations : dataframe
        Indexed by polling station ID. 
        Columns are place names, EKATTE, etc.
    '''
    
    names = ['station no', 'MIR', 'MIR name','EKATTE', 'place', 'mobile', 'ship', 'machine']
    usecols = [0, 1, 2, 3, 4]
    
    if month == 'april':
        source_file = 'sections_04.04.2021.txt'
    elif month=='july': 
        source_file = 'sections_11.07.2021.txt'
    elif month=='oct22':
        source_file = 'sections_02.10.2022.txt'
        names = ['station no', 'MIR', 'MIR name','EKATTE', 'place', 'address', 'mobile', 'ship', 'machine']
        usecols = [0, 1, 2, 3, 4, 5]
    else:
        raise ValueError('expected july, april, or oct22, got', month)
        
        
    stations = pd.read_csv(
        source_file, 
        usecols = usecols,
        dtype = {'station no': str},
        header = None, 
        names = names,
        delimiter = ';'
    ).set_index('station no')
    return stations
    
    #elif month=='july': 
    #    j_stations = pd.read_csv(
    #        'sections_11.07.2021.txt', 
    #        usecols = [0, 1, 2, 3, 4],
    #        dtype = {'station no': str},
    #        header = None, 
    #        names = ['station no', 'MIR', 'MIR name','EKATTE', 'place', 'mobile', 'ship', 'machine'],  
    #        delimiter = ';'
    #    ).set_index('station no')
    #    return j_stations
        


def add_regional_codes(results, stations):
    '''
    Adds region, municipality, and administrative region codes to a results dataframe
    by splitting the station ID into its constituent parts:
    region code (2 digits), municipality (2), administrative region (2), station (3)
    
    Parameters
    ----------
    results : dataframe
        results.index are station IDs
        results.columns are party labels
        data in each column indicates the number of votes in each polling station
    stations : dataframe 
        indexed by SID, contains location data (placenames)
    '''
    
    if not results.index.equals(stations.index):
        raise ValueError ('results and stations index don\'t match')
        
    results = results.copy()
    
    results['region'] = [sid[:2] for sid in results.index]
    results['municipality'] = [sid[2:4] for sid in results.index]
    results['admin_reg'] = [sid[4:6] for sid in results.index]
    results['sid'] = [sid[6:] for sid in results.index]
    results['region_name'] = stations['MIR name']
    results['place'] = stations['place'].copy()
    results['ekatte'] = stations['EKATTE'].copy()
    return results

def load_full(month):
    '''
    Loads votes data and station locations.
    
    Parameters
    ----------
    month : {'april', 'july', 'oct22'}
    
    Returns
    -------
    poll_data : dataframe
        Indexed by polling location ID.
    '''
    votes_data = load_votes_data(month)
    station_data = load_station_locations(month)
    return add_regional_codes(votes_data, station_data)


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
    drop_abroad = False
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
    drop_abroad : bool, default True
        If ``True`` will drop station IDs outside of the country (starting with '32')
        
    Returns
    -------
    party_votes : df 
        A dataframe indexed by Station ID.
        Columns: location, ekatte, region, address, party 1 votes 1, party 1 votes 2, party 1 drop pct, etc.
    '''

    parties_both = set(results1.columns[:-7]) & set(results2.columns) 
    ids = set(results1.index) | set(results2.index)
    
    if drop_abroad:
        ids = [x for x in ids if x[:2]!='32']
    
    addr = station_addresses()
   
    # order descending by totals in results1
    order = results1[list(parties_both)].sum().sort_values(ascending = False).index
    
    data = pd.DataFrame(index = [id for id in ids])
    data['населено място'] = results2['place']
    data['екатте'] = results2['ekatte']
    data['регион'] = results2['region_name']
    data['адрес'] = addr['address']
    
    for party in order:
        data[f'{party} {label1}'] = results1[party]
        data[f'{party} {label2}'] = results2[party]
        data[f'спад {party}'] = (data[f'{party} {label1}'] - data[f'{party} {label2}'])/data[f'{party} {label1}']
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

    parties_both = set(results1.columns[:-7]) & set(results2.columns) 
    regions = results1.groupby('ekatte').first()[['region_name','place']]
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
        
    if drop_abroad:
        bg_ekatte1 = [x for x in results1.index if not (str(x)[:3] =='100' and len(str(x)) == 6)]
        bg_ekatte2 = [x for x in results2.index if not (str(x)[:3] =='100' and len(str(x)) == 6)]
        both_bg = list(set(bg_ekatte2) & set(bg_ekatte1))
        return data[data.index.isin(both_bg)]
    
    return data 

def summary_plot(data, n):
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
        
    fig.update_layout(title = f'Ако въведеш филтри в таблицата долу, графиката ще се обнови. Брой секции: {n}')
        
    return fig

def summary_table(data):
    ''' 
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
    nuisance_cols = ['place', 'region', 'municipality', 'admin_reg', 'sid', 'ekatte', 'region_name']

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
        styler.set_caption("{}".format(april.loc[(april['ekatte'] == ekatte)]['place'].values[0]))
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
    return results.loc[station_id]['ekatte']
    

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
        
    
    #ns = []
    for item in settlements['features']:
    #         print (item['type'], item['properties'])
        item['id'] = item['properties']['ekatte'] 
#         ns.append(item)
            
    #ns_geo = settlements.copy()
    
    #ns_geo['features'] = ns
    #len(ns_geo['features'])
        
    data['ekatte'] = [str(x).zfill(5) for x in data.index]


    fig = px.choropleth(
    #     activity[activity.index.isin(active_filter)],
        data,
        geojson=settlements, 
        locations='ekatte', 
        color=col,
        color_continuous_scale="Viridis",
        range_color=range_color,
        labels=labels, 
        hover_data = list(labels.keys()), #['region', 'aj_drop_votes', 'april', 'july'],
        scope="europe",
        fitbounds = 'locations',
        featureidkey = 'properties.ekatte'
    )

    fig.update_geos(
    #     fitbounds="locations", 
    #     resolution=50,
        visible=False, #hide plotly background
    #     showframe=True, #what? 
    #     projection={"type": "mercator"},
    )


    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        width = 1400,
        height = 1200,
        title = title,
    )

    fig.show()
    
    
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
    print (
        f'Резултати по партии в населени места със спад над {min_drop*100}% в подкрепата за съответната партия\n' +
        f'през юли спрямо април 2021 и поне {min_votes} гласа за съответната партия през април 2021\n'
    )
    
    print (
        '{: <15} {: >15} {: >10} {: >10} {: >20}'.format('партия', 'гласове април', 'юли', 'разлика', 'брой населени места')
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
    title = ''
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
        
    '''

    fig = go.Figure()
    
    aa = april.drop(columns=['ekatte'])[april.index.isin(sids)].sum(numeric_only=True)
    jj = july.drop(columns=['ekatte'])[july.index.isin(sids)].sum(numeric_only=True)
    print ((aa.sum() - jj.sum())/aa.sum()*100)

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
    fig.show()

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
    nuisance_cols = ['place', 'region', 'municipality', 'admin_reg', 'sid', 'ekatte', 'region_name']

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
    
def station_addresses():
    '''
    Polling station addresses from October 2022 (first time they appeared).
    '''
    addr = pd.read_csv(
        './sections_02.10.2022_corr.txt', 
        sep = ';', 
        header=None,
        names = [
            'sid', 
            'region',
            'region_name',
            'ekatte',
            'place',
            'address',
            'mobile',
            'ship',
            'number of machines',
        ],
        dtype = {'sid': str}
    ).set_index('sid')
    return addr
