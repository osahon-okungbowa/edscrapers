import json
import sys
import os
import re
import urllib.parse
import functools
import pathlib
import edscrapers
import pandas as pd
import requests

from json.decoder import JSONDecodeError

from  edscrapers.transformers.base.helpers import traverse_output
from edscrapers.cli import logger

class Statistics():

    METRICS_OUTPUT_PATH = os.path.join(os.getenv('ED_OUTPUT_PATH'), 'tools', 'stats')
    METRICS_OUTPUT_XLSX = os.path.join(os.getenv('ED_OUTPUT_PATH'), 'tools', 'stats', 'metrics.xlsx')


    def __init__(self, delete_all_stats=False):

        if delete_all_stats is True:
            if os.path.exists(self.METRICS_OUTPUT_XLSX): # check if excel sheet exist
                os.remove(self.METRICS_OUTPUT_XLSX) # remove the excel sheet

        if os.path.exists(os.getenv('ED_OUTPUT_PATH') +\
            '/transformers/deduplicate/deduplicated_all.lst'):
            self.deduplicated_list_path = os.getenv('ED_OUTPUT_PATH') +\
            '/transformers/deduplicate/deduplicated_all.lst'
        else:
            self.deduplicated_list_path = None

        self.resource_count_per_page = []
        self.resource_count_per_domain = []
        self.page_count_per_domain = []

    def generate_statistics(self):
        logger.debug("Creating statistics...")
        scraper_outputs_df = self._generate_scraper_outputs_df(use_dump=False)
        self.resource_count_per_page = self.list_resource_count_per_page(scraper_outputs_df)
        self.resource_count_per_domain = self.list_resource_count_per_domain(scraper_outputs_df)
        self.page_count_per_domain = self.list_page_count_per_domain(scraper_outputs_df)
        self.datasets_per_scraper = self.list_datasets_per_scraper()

        print(
            f"Total number of raw datasets: \n {self.datasets_per_scraper}\n",
            f"\n---\n\n",
            f"Total number of pages: {self.page_count_per_domain['page count'].sum()}\n",
            f"\n---\n\n",
            f"Total number of resources: {self.resource_count_per_domain['resource count'].sum()}\n",
            f"\n---\n\n",
            f"Total number of pages by domain: \n{self.page_count_per_domain}\n",
            f"\n---\n\n",
            f"Total number of resources by domain: \n{self.resource_count_per_domain}\n",
            f"\n---\n\n",
        )

    def _add_to_spreadsheet(self, sheet_name, result):
        # write the result (dataframe) to an excel sheet
        if os.path.exists(self.METRICS_OUTPUT_XLSX): # check if excel sheet exist
            writer_mode = 'a' # set write mode to append
        else:
            writer_mode = 'w' # set write mode to write
        with pd.ExcelWriter(self.METRICS_OUTPUT_XLSX, engine="openpyxl",
                            mode=writer_mode) as writer:
            result.to_excel(writer,
                            sheet_name=sheet_name,
                            index=False,
                            engine='openpyxl')
        pass

    def to_json(self, stats_dict):
        """Create a JSON output from the provided stats dictionary
        """
        pass

    def to_xlsx(self):
        pass

    def to_ascii(self, stats_dict):
        """Create an ASCII output from the provided stats dictionary
        """
        pass

    # TODO: Imported from the Summary module, needs refactoring to fit in
    def _generate_scraper_outputs_df(self, use_dump=False):

        def abs_url(url, source_url):
            if url.startswith(('../', './', '/')) or not urllib.parse.urlparse(url).scheme:
                full_url = urllib.parse.urljoin(source_url, url)
                return full_url
            else:
                return url

        if self.deduplicated_list_path is None:
            files = traverse_output()
        else:
            try:
                with open(self.deduplicated_list_path, 'r') as fp:
                    files = [pathlib.Path(line.rstrip()) for line in fp]
            except:
                files = traverse_output()

        df_dump = str(pathlib.Path(os.path.join(os.getenv('ED_OUTPUT_PATH'), 'out_df.csv')))
        if use_dump:
            df = pd.read_csv(df_dump)
        else:
            dfs = []
            for fp in files:
                # TODO refactor these rules or the files structure
                if 'data.json' in str(fp):
                    continue

                with open(fp, 'r') as json_file:
                    try:
                        j = json.load(json_file)
                        j = [{
                            'url': abs_url(r['url'], r['source_url']),
                            'source_url': r['source_url'],
                            'scraper': fp.parent.name
                        } for r in j['resources'] if r['source_url'].find('/print/') == -1]
                        dfs.append(pd.read_json(json.dumps(j)))
                    except:
                        logger.warning(f'Could not parse file {json_file} as JSON!')
            df = pd.concat(dfs, ignore_index=True)
            df.to_csv(df_dump, index=False)

        return df

    def list_datasets_per_scraper(self, ordered=True):
        """Generate page count per domain

        PARAMETERS
        - ordered: whether the resulting DataFrame or
        Excel sheet result be sorted/ordered. If True, order by 'page count'
        """

        filenames = []
        try:
            with open(self.deduplicated_list_path, 'r') as fp:
                filenames = fp.readlines()
        except:
            logger.warning('Warning! Cannot read deduplication results. Please run deduplicate transformer first')
            filenames = traverse_output()

        scraper_counts = {}
        for filename in filenames:
            scraper_name = str(filename).rstrip().split('/')[-2]
            scraper_counts[scraper_name] = (scraper_counts.get(scraper_name, 0) + 1)

        df = pd.DataFrame(columns=['scraper', 'dataset count'])
        df['scraper'] = list(scraper_counts.keys())
        df['dataset count'] = list(scraper_counts.values())

        if ordered:
            df.sort_values(by='dataset count', axis='index',
                                    ascending=False, inplace=True,
                                    ignore_index=True)

        self._add_to_spreadsheet(sheet_name='DATASET COUNT PER SCRAPER',
                                    result=df)
        return df
    

    def list_page_count_per_domain(self, scraper_outputs_df, ordered=True):
        """Generate page count per domain

        PARAMETERS
        - scraper_outputs_df: dataframe containing scraper outputs,
           generated with the method with the same name
        - ordered: whether the resulting DataFrame or
        Excel sheet result be sorted/ordered. If True, order by 'page count'
        """

        # create a dataframe with duplicate source_urls removed
        df = scraper_outputs_df.\
            drop_duplicates(subset='source_url', inplace=False)

        # create subset of the datopian dataframe (subset will house domain info)
        df_subset = pd.DataFrame(columns=['domain'])
        # create the domain column from the source_url info available
        df_subset['domain'] = df.\
            apply(lambda row: urllib.parse.\
                    urlparse(row['source_url']).hostname.\
                        replace('www2.', 'www.').replace('www.', ''), axis=1)
        # to get the number of pages visited from each domain, perform groupby
        grouped = df_subset.groupby(['domain'])
        # recreate the datopian dataframe subset to store aggreated domain info
        df_subset = pd.DataFrame(columns=['domain'])
        # get the keys/names for grouped domains
        df_subset['domain'] = list(grouped.indices.keys())
        # get the size of each group
        # i.e. the number of times each domain appeared in the non-grouped dataframe
        # this value represents the number of pages visited
        df_subset['page count'] = list(grouped.size().values)

        # if 'ordered' is True, sorted the df by 'page count' in descending order
        if ordered:
            df_subset.sort_values(by='page count', axis='index',
                                    ascending=False, inplace=True,
                                    ignore_index=True)

        self._add_to_spreadsheet(sheet_name='PAGE COUNT PER DOMAIN',
                                    result=df_subset)
        return df_subset


    def list_resource_count_per_domain(self, scraper_outputs_df, ordered=True):
        """Generate resource count per domain

        PARAMETERS
        - scraper_outputs_df: dataframe containing scraper outputs,
           generated with the method with the same name
        - ordered: whether the resulting DataFrame or
        Excel sheet result be sorted/ordered. If True, order by 'resource per domain'
        """

        # create a dataframe with duplicate url and source_urls removed
        df_deduplicated_df = scraper_outputs_df.\
            drop_duplicates(subset=['url', 'source_url'], inplace=False)

        # create subset of the df dataframe (subset will house domain info)
        df_subset = pd.DataFrame(columns=['domain'])
        # create the domain column from the source_url info available
        df_subset['domain'] = df_deduplicated_df.\
            apply(lambda row: urllib.parse.\
                    urlparse(row['source_url']).hostname.\
                        replace('www2.', 'www.').replace('www.', ''), axis=1)
        # to get the number of pages visited from each domain, perform groupby
        grouped = df_subset.groupby(['domain'])
        # recreate the datopian dataframe subset to store aggreated domain info
        df_subset = pd.DataFrame(columns=['domain'])
        # get the keys/names for grouped domains
        df_subset['domain'] = list(grouped.indices.keys())
        # get the size of each group
        # i.e. the number of times each domain appeared in the non-grouped dataframe
        # this value represents the number of resources visited
        df_subset['resource count'] = list(grouped.size().values)

        if ordered:
            df_subset.sort_values(by='resource count', axis='index',
                                        ascending=False, inplace=True,
                                        ignore_index=True)

        self._add_to_spreadsheet(sheet_name='RESOURCE COUNT PER DOMAIN',
                                    result=df_subset)
        return df_subset

    def list_resource_count_per_page(self, scraper_outputs_df, ordered=True,):
        """Determine resources produced/generated from each page

        PARAMETERS
        - scraper_outputs_df: dataframe containing scraper outputs,
           generated with the method with the same name
        - ordered: whether the resulting DataFrame or
        Excel sheet result be sorted/ordered. If True, order by 'resource per page'
        """

        # create a dataframe with duplicate url and source_urls removed
        deduplicated_df = scraper_outputs_df.drop_duplicates(subset=['url', 'source_url'],
                                             inplace=False)
        # create subset of the dataframe (subset will house domain info)
        df_subset = pd.DataFrame(columns=['domain'])
        # create the domain column from the source_url info available
        df_subset['domain'] = deduplicated_df.apply(lambda row: urllib.parse.\
                                       urlparse(row['source_url']).hostname.\
                                       replace('www2.', 'www.').replace('www.', ''), axis=1)

        # get the 'source_url' renamed as 'page'
        df_subset['page'] = deduplicated_df['source_url']
        # to get the number of resources retrieved from each page, perform groupby
        grouped = df_subset.groupby(['domain', 'page'])
        # create dataframe to store aggreated resource info
        result = pd.DataFrame(columns=['domain', 'page'])
        result['domain'] = [domain for domain, page in grouped.indices.keys()]
        result['page'] = [page for domain, page in grouped.indices.keys()]
        # get the size of each group
        # this value represents the number of resources gotten per page
        result['resource per page'] = list(grouped.size().values)

        # if 'ordered' is True, sorted the df by 'resource count' in descending order
        if ordered:
            result.sort_values(by='resource per page',
                                  axis='index',
                                  ascending=False,
                                  inplace=True,
                                  ignore_index=True)

        self._add_to_spreadsheet(sheet_name='RESOURCE COUNT PER PAGE',
                                 result=result)

        return result
