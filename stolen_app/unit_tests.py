import pandas as pd 
from pandas.testing import assert_frame_equal
from data_loading import load_full 

data_dir = '../unit_tests/reference_data/'

def test_map_data(): # indirectly tests load_full()
    for m in ['mar17', 'apr21', 'jul21', 'nov21', 'oct22', 'apr23']:
        df = load_full(m)

        dfbg = df[df.index < '320000000']
        by_ekatte = dfbg.groupby('ekatte').sum(numeric_only=True)
    #     by_ekatte    

        parties = by_ekatte.columns[:-1]# all parties + npn 

    #     parties = by_ekatte[parties].sum().sort_values(ascending = False).index # order by total votes at national level 

        final = by_ekatte[parties].divide( by_ekatte[parties].sum(axis = 1), axis = 'rows') # parties as proportion of total votes
        final['total'] = by_ekatte[parties].sum(axis = 1)  # total valid votes (parties + NPN) 
        final['eligible_voters'] = by_ekatte['eligible_voters'] # initial voter list 
        final['activity'] = final['total']/by_ekatte['eligible_voters']
        # final

        final.index.name = 'id' # update js to get rid of this rename 
        final.rename(columns = {'npn' : 'не подкрепям никого', 'activity' : 'активност'}, inplace = True) 

        ref = pd.read_csv(f'{data_dir}data_{m}_pct.csv', index_col = [0])

        assert_frame_equal(final, ref)
