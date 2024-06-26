import pandas as pd 
import plotly.graph_objects as go
import plotly.express as px
import json 
import os

data_dir = os.path.join(os.path.dirname(__file__), '../data')

_known_elections = 'may13, oct14, mar17, apr21, jul21, nov21, oct22, or apr23'

def load_full(month):
    '''
    Loads votes data and station locations.
    
    Parameters
    ----------
    month : {'oct14', 'mar17', 'apr21', 'jul21', 'nov21', 'oct22', 'apr23'}
    
    Returns
    -------
    poll_data : dataframe
        Indexed by polling location ID.
    '''
    votes_data = load_votes_data(month)
    station_data = load_station_locations(month)
    #TODO use a single function for eligible voters, npn, and invalid (all from protocols.txt)
    eligible_voters = get_eligible_voters(month)
    npn = get_npn(month)
    invalid = get_invalid(month)
    return add_regional_codes(votes_data, station_data, eligible_voters, npn, invalid)

def load_votes_data(month):
    '''
    Loads votes data for either april or july.
    
    Parameters
    ----------
    month : {'mar17', 'apr21', 'jul21', 'nov21', 'oct22', 'apr23}
    
    Returns
    -------
    votes : dataframe
        Indexed by polling station ID. 
        Columns are party names + suffix indicating the month.
        
    '''
    
    from .rename_map import (
        may13_rename_map,
        oct14_rename_map,
        mar17_rename_map,
        apr21_rename_map,
        jul21_rename_map,
        nov21_rename_map,
        oct22_rename_map,
        apr23_rename_map,
    )
    
    if month == 'may13': 
        data_ = pd.read_csv(f'{data_dir}/pe2013_pe_votes_padded.csv', index_col = [0], dtype = {'sid': str})
        data_ = data_[['sid'] + [n for n in data_ if ('result' in n)]].groupby('sid').sum()
        data_.rename(columns = {x : x[:-7] for x in data_}, inplace = True)
        data_.rename(columns = may13_rename_map, inplace = True)
    
    elif month == 'oct14':
        data_ = pd.read_csv(f'{data_dir}/votes_pe2014_padded.csv', index_col = [0], dtype = {'sid': str})
        data_ = data_[['sid'] + [n for n in data_ if ('result' in n and 'invalid' not in n)]].groupby('sid').sum()
        data_.rename(columns = {x : x[:-7] for x in data_}, inplace = True)
        data_.rename(columns = oct14_rename_map, inplace = True)
    
    elif month == 'mar17':
        data_ = pd.read_csv(f'{data_dir}/votes_26.03.2017_padded.csv', index_col = [0], dtype = {'station no': str})
        data_ = data_[['station no'] + [n for n in data_ if ('result' in n and 'invalid' not in n)]].groupby('station no').sum()
        data_.rename(columns = {x : x[:-7] for x in data_}, inplace = True)
        data_.rename(columns = mar17_rename_map, inplace = True)
    
    elif month in ['april', 'apr21']:
        april = pd.read_csv(f'{data_dir}/votes_04.04.2021_padded.csv', index_col = [0], dtype = {'station no': str})
        april = april[['station no'] + [n for n in april if ('result' in n and 'paper' not in n and 'machine' not in n)]]
        data_ = april.groupby('station no').sum()
        data_.rename(columns = {x : x[:-7] for x in data_}, inplace = True)
        data_.rename(columns = apr21_rename_map, inplace = True)
    
    elif month in ['july', 'jul21']:
        july = pd.read_csv(f'{data_dir}/votes_11.07.2021_padded.csv', index_col = [0], dtype = {'station no': str})
        data_ = july[['station no'] + [n for n in july if 'result' in n]].groupby('station no').sum()
        data_.rename(columns = {x : x[:-7] for x in data_}, inplace = True)
        data_.rename(columns = jul21_rename_map, inplace = True)
    
    elif month == 'nov21':
        data = pd.read_csv(f'{data_dir}/votes_14.11.2021_padded.csv', index_col = [0], dtype = {'station no': str})
        data_ = data[['station no'] + [n for n in data if 'result' in n]].groupby('station no').sum()
        data_.rename(columns = {x : x[:-7] for x in data_}, inplace = True)
        data_.rename(columns = nov21_rename_map, inplace = True)
    
    elif month == 'oct22':
        data = pd.read_csv(f'{data_dir}/votes_02.10.2022_padded.csv', index_col = [0], dtype = {'station no': str})
        data_ = data[['station no'] + [n for n in data if 'result' in n]].groupby('station no').sum()
        data_.rename(columns = {x : x[:-7] for x in data_}, inplace = True)
        data_.rename(columns = oct22_rename_map, inplace = True)
    
    elif month == 'apr23':
        data_ = pd.read_csv(f'{data_dir}/votes_02.04.2023_padded.csv', index_col = [0], dtype = {'station no': str})
        data_ = data_[['station no'] + [n for n in data_ if ('result' in n and 'paper' not in n and 'machine' not in n)]]
        data_ = data_.groupby('station no').sum()
        data_.rename(columns = {x : x[:-7] for x in data_}, inplace = True)
        data_.rename(columns = apr23_rename_map, inplace = True)

    else:
        raise ValueError(f'Expected {_known_elections}, got', month)

    return data_

def load_station_locations(month):
    '''
    Loads polling station location data for either april or july.
    
    Parameters
    ----------
    month : {'mar17', 'apr21', 'jul21', 'nov21', 'oct22', 'apr23}
    
    Returns
    -------
    stations : dataframe
        Indexed by polling station ID. 
        Columns are place names, EKATTE, etc.
    '''
    
    names = ['station no', 'MIR', 'MIR name','EKATTE', 'place', 'mobile', 'ship', 'machine']
    usecols = [0, 1, 2, 3, 4]
    
    if month == 'may13':
        source_file = f'{data_dir}/pe2013_pe_sections.txt'
        names = ['station type flag', 'station no', 'MIR name', 'municipality', 'place', 'EKATTE']
        usecols = [1,2,4,5]
    elif month == 'oct14':
        source_file = f'{data_dir}/sections_pe2014.txt'
        names = ['station no', 'place', 'EKATTE', 'mobile', 'ship', 'machine']
        usecols = [0,1,2]
    elif month == 'mar17':
        source_file = f'{data_dir}/sections_26.03.2017.txt'
        names = names[:-1]
    elif month in ['april', 'apr21']:        
        source_file = f'{data_dir}/sections_04.04.2021.txt'
    elif month in ['july', 'jul21']:
        source_file = f'{data_dir}/sections_11.07.2021.txt'
    elif month=='nov21': 
        source_file = f'{data_dir}/sections_14.11.2021.txt'
    elif month=='oct22':
        source_file = f'{data_dir}/sections_02.10.2022_corr.txt' #fixed address of one station in USA
        names = ['station no', 'MIR', 'MIR name','EKATTE', 'place', 'address', 'mobile', 'ship', 'machine']
        usecols = [0, 1, 2, 3, 4, 5]
    elif month=='apr23':
        source_file = f'{data_dir}/sections_02.04.2023.txt' 
        names = ['station no', 'MIR', 'MIR name','EKATTE', 'place', 'address', 'mobile', 'ship', 'machine']
        usecols = [0, 1, 2, 3, 4, 5]
    else:
        raise ValueError(f'Expected {_known_elections}, got', month)
        
        
    stations = pd.read_csv(
        source_file, 
        usecols = usecols,
        dtype = {'station no': str},
        header = None, 
        names = names,
        delimiter = ';'
    ).set_index('station no')
    return stations
    
def get_eligible_voters(month):
    '''
    Parameters
    ----------
    month : {'oct14', 'mar17', 'apr21', 'jul21', 'nov21', 'oct22', 'apr23}
        The month for which to load data.
        
    Returns
    -------
    series
        Eligible voters by SID.
    '''
    
    # NOTE keeping column names to make it easier to reuse this later for other functiions.
    # otherwise could just use column numbers here

    if month == 'may13':        
        protocols_file = f'{data_dir}/pe2013_pe_protocols.txt'
    elif month == 'oct14':        
        protocols_file = f'{data_dir}/protocols_pe2014.txt'
    elif month == 'mar17':        
        protocols_file = f'{data_dir}/protocols_26.03.2017.txt'
    elif month in ['april', 'apr21']:        
        protocols_file = f'{data_dir}/protocols_04.04.2021.txt'
    elif month in ['july', 'jul21']:
        protocols_file = f'{data_dir}/protocols_11.07.2021.txt'
    elif month == 'nov21':
        protocols_file = f'{data_dir}/protocols_14.11.2021.txt'
    elif month =='oct22':
        protocols_file = f'{data_dir}/protocols_02.10.2022.txt'
    elif month =='apr23':
        protocols_file = f'{data_dir}/protocols_02.04.2023.txt'    
    else:
        raise ValueError(f'Expected {_known_elections}, got', month)

    names_all = ['form number', 'sid', 'rik', 'page numbers']
    index_col = 1
        
    if month == 'may13':
        index_col = 1
        col0 = 0 # station type flag
        col1 = 4 # elig voters (at home) 
        col2 = 2 # elig voters (abroad)
        protocols = pd.read_csv(
            protocols_file,
            sep = ';',
            header = None,
            #usecols = range(cols),
            #names = range(cols),
            dtype = {1 : str},
            index_col = [1],
        )
        
        data = protocols[col1].where(protocols[col0]!='Д', other=protocols[col2])
        data.index.name = 'sid'
        return data

    if month == 'oct14':
        names_all = ['sid', 'registered_candidate_lists']
        names = [
            'number of ballots', #3
            'eligible voters', #4 'брой избиратели в избирателният списък при предаването му на СИК'
            'added voters', #5 'дописани в изборният ден под черта'
            'signatures', #6 'брой гласували според подписите'
        ]
        index_col = 0
    elif month == 'mar17':
        names = [
            'number of ballots', #5
            'eligible voters', #6 'брой избиратели в избирателният списък при предаването му на СИК'
            'added voters', #7 'дописани в изборният ден под черта'
            'signatures', #8 'брой гласували според подписите'
        ]
    elif month in ['april', 'apr21']:        
        names = [
            'number of ballots', #5 брой на получените бюлетини 
            'eligible voters', #6 'брой избиратели в избирателният списък при предаването му на СИК, включително вписаните в изборния ден'
            'signatures', #7 'брой гласували според подписите'
        ]
    elif month in ['july', 'jul21']:
        names = [
            'number of ballots', #5
            'eligible voters', #6 'брой избиратели в избирателният списък при предаването му на СИК'
            'added voters', #7 'дописани в изборният ден под черта'
            'signatures', #8 'брой гласували според подписите'
        ]        
    elif month in ['nov21', 'oct22', 'apr23']:
        names = [
            'machine number', #5 NA
            'reason flag', #6 NA
            'number of ballots', #7
            'eligible voters', #8 'брой избиратели в избирателният списък при предаването му на СИК'
            'added voters', #9 'дописани в изборният ден под черта'
            'signatures', #10 'брой гласували според подписите'
        ]
    else:
        raise ValueError(f'Expected {_known_elections}, got', month)
        
    names = names_all + names
    
    protocols = pd.read_csv(
        protocols_file,
        sep = ';',
        usecols = range(len(names)), 
        names = names, 
        dtype = {'sid' : str},
        index_col = [index_col],
    )
    
    return protocols['eligible voters'].groupby('sid').sum() # by sid 

def get_npn(month):
    '''
    Parameters
    ----------
    month : {'mar17', 'apr21', 'jul21', 'nov21', 'oct22', 'apr23}
        The month for which to load data.
        
    Returns
    -------
    series
        "Не подкрепям никого" votes by SID.
    '''
   
    index_col = 1 

    if month == 'may13':        
        protocols_file = f'{data_dir}/pe2013_pe_protocols.txt'
        col = 19
        index_col = 1
    elif month == 'oct14':        
        protocols_file = f'{data_dir}/protocols_pe2014.txt'
        col = 19
        index_col = 0
    elif month == 'mar17':        
        protocols_file = f'{data_dir}/protocols_26.03.2017.txt'
        col = 19
    elif month in ['april', 'apr21']:        
        protocols_file = f'{data_dir}/protocols_04.04.2021.txt'
        col = 21
    elif month in ['july', 'jul21']:
        protocols_file = f'{data_dir}/protocols_11.07.2021.txt'
        col = 17
    elif month == 'nov21':
        protocols_file = f'{data_dir}/protocols_14.11.2021.txt'
        col = 19
    elif month =='oct22':
        protocols_file = f'{data_dir}/protocols_02.10.2022.txt'
        col = 19
    elif month =='apr23':
        protocols_file = f'{data_dir}/protocols_02.04.2023.txt'    
        col = 25
    else:
        raise ValueError(f'Expected {_known_elections}, got', month)
        
    protocols = pd.read_csv(
        protocols_file,
        sep = ';',
        usecols = range(col), 
        names = range(col), 
        dtype = {index_col : str},
        index_col = [index_col],
    )
    
    protocols.index.name = 'sid'
    
    if month in ['may13', 'oct14']:
        return 0*protocols[col-1].groupby('sid').sum() # or np.nan? 
    elif month =='apr23':
        form_col_map = { # columns where total NPN votes are (values), depending on form number (keys)
            24 : 23,
            26 : 25,
            28 : 23,
            30 : 25,
        }
        
        npn = pd.Series(index = protocols.index, dtype = int)
        for fn in form_col_map:
            npn[protocols[0]==fn] = protocols[protocols[0]==fn][form_col_map[fn]-1]
            
        return npn.groupby('sid').sum()
    else:
        return protocols[col-1].groupby('sid').sum() # by sid 
    
def add_regional_codes(results, stations, elig_voters, npn, invalid):
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
    if not results.index.equals(elig_voters.index):
        raise ValueError ('results and elig_voters index don\'t match')
    if not results.index.equals(npn.index):
        raise ValueError ('results and npn index don\'t match')
        
    results = results.copy()
    
    results['npn'] = npn
    results['invalid'] = invalid
    results['region'] = [sid[:2] for sid in results.index]
    results['municipality'] = [sid[2:4] for sid in results.index]
    results['municipality_name'] = [sid_to_mun(sid) for sid in results.index]
    results['admin_reg'] = [sid[4:6] for sid in results.index]
    results['station'] = [sid[6:] for sid in results.index]
    if 'MIR name' in stations:
        results['region_name'] = stations['MIR name']
    else: # oct14 patch
        results['region_name'] = ['-']*len(results)
    results['place'] = stations['place'].copy()
    results['ekatte'] = stations['EKATTE'].copy()
    if 'address' in stations:
        results['address'] = stations['address'].copy()
    else:
        results['address'] = ['-']*len(results.index) 

    results['eligible_voters'] = elig_voters

    return results

def sid_to_mun(sid):
    '''
    Returns the municipality in which the polling station is located.
    
    Parameters
    ----------
    sid : string 
        Station ID. Only first four digits are used (XXYYxxxxx).
        XX = MIR
        YY = municipality

    Returns
    -------
    municipality name : str
    '''

    with open(f'{data_dir}/xxyy_to_municipality_map.json', 'r') as f:
        sid_to_mun = json.loads(f.read())

    return sid_to_mun[sid[:4]] if sid[:2] < '32' else 'чужбина'

def station_addresses():
    '''
    Polling station addresses from October 2022 (first time they appeared).
    '''
    addr = pd.read_csv(
        f'{data_dir}/sections_02.10.2022_corr.txt', 
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

def get_protocols(month, by_sid = True, extra = True):
    '''
    Parameters
    ----------
    month : {oct22}
        The month for which to load data.
        For now only October 22.
    by_sid : bool, default True
        If ``True`` will sum the data by SID.
    extra : bool, defaul True
        If ``True`` and ``by_sid`` is also ``True``, will return some extra data (address, station location)
        
    Returns
    -------
    protocols: df
        Protocols data.
        Rows correspond to individual protocols/station IDs.
    '''
    
    if month == 'oct22':
        protocols = pd.read_csv(
            '../2022-10ns/np/protocols_02.10.2022.txt', 
            sep = ';', 
            usecols = range(19),
            names = [
                'form number', 
                'sid', 
                'rik', 
                'page numbers', 
                'machine number', 
                'reason flag', 
                'number of ballots', 
                'eligible voters', 
                'added voters', 
                'signatures', 

                'unused ballots', 
                'destroyed ballots', 
                'total cast', # values in this column seem to be totally off, should be the sum of the next two lines; actually the column order seems to be messed up   
                'paper ballots', 
                'machine votes',
                'invalid paper ballots', 
                'valid votes total', # according to readme: 'valid paper ballots',
                'valid votes for parties', 
                'valid votes blank'
            ],
            dtype = {'sid': str}
        )
    
    if by_sid:
        protocols = protocols.groupby('sid').sum(numeric_only = True).drop(columns = ['form number', 'rik', 'reason flag'])

        if extra:
            addr = station_addresses()
            protocols['address'] = addr['address']
            month_data = load_full(month)
            protocols['place'] = month_data['place']
            protocols['ekatte'] = month_data['ekatte']

    return protocols

def get_invalid(month):
    '''
    Parameters
    ----------
    month : {mar17, apr12, jul21, nov21, oct22, apr23}
        The month for which to load data.
        
    Returns
    -------
    series
        "Недействителни" votes by SID.
    '''

    index_col = 1

    if month == 'may13':
        protocols_file = f'{data_dir}/pe2013_pe_protocols.txt'
        col0 = 0 # station type flag
        col1 = 32 # domestic
        col2 = 14  # abroad 
        
        protocols = pd.read_csv(
            protocols_file,
            sep = ';',
            header = None,
            dtype = {1 : str},
            index_col = [1],
        )
        data = protocols[col1].where(protocols[col0]!='Д', other=protocols[col2])
        data.index.name = 'sid'
        return data
    if month == 'oct14':        
        protocols_file = f'{data_dir}/protocols_pe2014.txt'
        col = 17
        index_col = 0
    elif month == 'mar17':        
        protocols_file = f'{data_dir}/protocols_26.03.2017.txt'
        col = 16
    elif month in ['april', 'apr21']:
        protocols_file = f'{data_dir}/protocols_04.04.2021.txt'
        col = 12
    elif month in ['july', 'jul21']:
        protocols_file = f'{data_dir}/protocols_11.07.2021.txt'
        col = 14
    elif month == 'nov21':
        protocols_file = f'{data_dir}/protocols_14.11.2021.txt'
        col = 16
    elif month =='oct22':
        protocols_file = f'{data_dir}/protocols_02.10.2022.txt'
        col = 16
    elif month =='apr23':
        protocols_file = f'{data_dir}/protocols_02.04.2023.txt'
        col = 16
    else:
        raise ValueError(f'Expected {_known_elections}, got', month)

    protocols = pd.read_csv(
        protocols_file,
        sep = ';',
        usecols = range(col), 
        names = range(col), 
        dtype = {index_col : str},
        index_col = [index_col],
    )
    
    protocols.index.name = 'sid'
    
    return protocols[col-1].groupby('sid').sum() # by sid     

def place_data():
    '''
    Gets region, municipality, place name, ekatte data according to NSI.

    Returns
    -------
    df
        A dataframe with admin data. Columns:
        * област
        * община
        * населено место
        * ekatte
    '''
    data = pd.read_csv(f'{data_dir}/place_data.csv')
    return data 

