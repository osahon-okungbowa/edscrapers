""" module creates the dashboard '/insights' page """

# -*- coding: utf-8 -*-
import os

import dash
import textwrap
import dash_table
import pandas as pd
import dash_daq as daq
import plotly.graph_objects as go
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc


from edscrapers.tools.stats.stats import Statistics
from edscrapers.tools.dashboard.ckan_api import CkanApi
from edscrapers.tools.dashboard.utils import buttonsToRemove
from edscrapers.tools.dashboard.pages.tooltips import (INSIGHTS_TOTALS_INITIAL_TOOLTIP,
                                                INSIGHTS_TOTALS_SCRAPED_TOOLTIP,
                                                INSIGHTS_TOTALS_INGESTED_TOOLTIP,
                                                INSIGHTS_DATASETS_BY_DOMAIN_TOOOLTIP,
                                                INSIGHTS_DATASETS_BY_OFFICE_TOOOLTIP,
                                                INSIGHTS_RESOURCES_BY_DOMAIN_TOOOLTIP,
                                                INSIGHTS_RESOURCES_BY_OFFICE_TOOOLTIP)
from edscrapers.tools.dashboard.pages.components import header, led_display

class InsightsPage():

    # path to Excel sheet used for creating stas dataframes
    PATH_TO_EXCEL_SHEET = os.path.join(os.getenv('ED_OUTPUT_PATH'), 'tools', 'stats', 'metrics.xlsx')

    def __init__(self):
        self.ckan_api = CkanApi()

    def _get_df_from_excel_sheet(self, sheet_name):
        """ private helper function used to read excel sheets and
            create dataframes from the specified sheet"""

        return pd.read_excel(self.PATH_TO_EXCEL_SHEET, sheet_name, engine='openpyxl')

    def dataset_by_domain_portal_df(self):
        data = self.ckan_api.datasets_by_domain()

        domains = []
        counts = []

        for name, count in data:
            domains.append(name)
            counts.append(count)

        df = pd.DataFrame(columns=['domain','page count'])
        df['domain'] = domains
        df['page count'] = counts

        df.sort_values(by='page count', axis='index',
                                    ascending=False, inplace=True,
                                    ignore_index=True)

        return df

    def resource_by_domain_portal_df(self):
        data = self.ckan_api.resources_by_domain()

        domains = []
        counts = []

        for name, count in data:
            domains.append(name)
            counts.append(count)

        df = pd.DataFrame(columns=['domain','resource count'])
        df['domain'] = domains
        df['resource count'] = counts

        df.sort_values(by='resource count', axis='index',
                                    ascending=False, inplace=True,
                                    ignore_index=True)

        return df

    def dataset_by_domain_table(self):
        """ function used to create the Table component which displays
        the number of pages/datasets obtained from each domain """

        df = self.dataset_by_domain_portal_df()

        # add a total of page count at the end of the df
        total_page_count = df['page count'].sum()

        df_total = pd.DataFrame([['Total', total_page_count]],
                            columns=['domain','page count'])
        df = df.append(df_total, ignore_index=True)


        # create the DataTable
        return dash_table.DataTable(
                id='dataset_by_domain_table',
                #columns=[{"name": i, "id": i} \
                #    if i != "page count" else \
                #        {"name": "Dataset Count", "id": i} \
                #            for i in df.columns],
                columns=[{"id": "domain", "name": "Domain"},
                        {"id": "page count", "name": "Dataset Count"}],
                data=df.to_dict('records'),
                sort_action='native',
                style_cell={'textAlign': 'left',
                            'whiteSpace': 'normal'},
                            #fixed_rows={ 'headers': True, 'data': 0 },
                            #virtualization=True,
                style_cell_conditional=[
                            {'if': {'column_id': 'domain'},
                            'width': '70%',
                            'textAlign': 'right'},
                            {'if': {'column_id': 'page count'},
                            'width': '30%'},
                            #{'if': {'row_index': 'odd'},
                            #'backgroundColor': 'rgb(248, 248, 248)'}
                            ],
                style_table={
                            'maxHeight': '300px',
                            'maxWidth': '100%',
                            'overflowY': 'auto',
                            'overflowX': 'hidden',
                            'margin': 0,
                            'padding': 0,
                            },
                style_header={
                            'backgroundColor': 'rgb(230, 230, 230)',
                            'fontWeight': 'bold',
                            'textAlign': 'center',
                            }
        )


    def dataset_by_domain_bar(self):
        """ function creates a bar chart which displays the
        number of pages/datasets per domain """

        df = self.dataset_by_domain_portal_df()
        # create the bar chart using the created dataframe
        return dcc.Graph(
            id='dataset_by_domain_graph',
            figure={
                'data': [
                            {'x': df['domain'], 'y': df['page count'], 'type': 'bar'}
                        ],
                'layout': {
                    #'title': 'Datasets by Domain'
                }
            },
            config={
                'modeBarButtonsToRemove': buttonsToRemove
            }
        )


    def resources_by_domain_table(self):
        """ function is used to create DataTable containing
        the number of resources/domains """

        working_df1 = self.resource_by_domain_portal_df()

        # sort values
        working_df1.sort_values(by='resource count', axis='index',
                                    ascending=False, inplace=True,
                                    ignore_index=True)

        # add a total of resource count at the end of the df
        total_resource_count = working_df1['resource count'].sum()

        df_total = pd.DataFrame([['Total', total_resource_count]],
                            columns=['domain','resource count'])
        working_df1 = working_df1.append(df_total, ignore_index=True)

        # return the created DataTable
        return dash_table.DataTable(
                    id='resource_by_domain_table',
                    #columns=[{"name": i, "id": i} for i in working_df1.columns],
                    columns=[{"id": "domain", "name": "Domain"},
                            {"id": "resource count", "name": "Resource Count"}],
                    data=working_df1.to_dict('records'),
                    sort_action='native',
                    style_cell={'textAlign': 'left',
                        'whiteSpace': 'normal'},
                    #fixed_rows={ 'headers': True, 'data': 0 },
                    #virtualization=True,
                    style_cell_conditional=[
                        {'if': {'column_id': 'domain'},
                        'width': '70%', 'textAlign': 'right'},
                        {'if': {'column_id': 'resource count'},
                        'width': '30%'},
                        #{'if': {'row_index': 'odd'},
                        #'backgroundColor': 'rgb(248, 248, 248)'}
                        ]
                        ,
                    style_table={
                        'maxHeight': '300px',
                        'maxWidth': '100%',
                        'overflowY': 'scroll',
                        'overflowX': 'hidden',
                        'margin': 0,
                        'padding': 0
                    },
                    style_header={
                        'backgroundColor': 'rgb(230, 230, 230)',
                        'fontWeight': 'bold',
                        'textAlign': 'center',
                    }
        )

    def total_domains_count_stats(self):
        df = self._get_df_from_excel_sheet('RESOURCE COUNT PER DOMAIN')
        return df['domain'].count()
    
    def total_page_count_stats(self):
        df = self._get_df_from_excel_sheet('PAGE COUNT PER DOMAIN')
        return df['page count'].sum()
    
    def total_resource_count_stats(self):
        df = self._get_df_from_excel_sheet('RESOURCE COUNT PER DOMAIN')
        return df['resource count'].sum()
    
    def total_datasets_count_stats(self):
        df = self._get_df_from_excel_sheet('DATASET COUNT PER SCRAPER')
        return df['dataset count'].sum()

    def resources_by_publisher_portal_df(self):

        data = self.ckan_api.resources_by_publisher()

        publishers = []
        counts = []
        for name, count in data:
            publishers.append(name)
            counts.append(count)

        df = pd.DataFrame(columns=['publisher','resource count'])
        df['publisher'] = publishers
        df['resource count'] = counts

        df.sort_values(by='resource count', axis='index',
                                    ascending=False, inplace=True,
                                    ignore_index=True)

        return df


    def resources_by_domain_pie(self):
        """" function is used to created a pie chart showing
        the number of resources gotten per domain """

        df = self.resource_by_domain_portal_df()

        wrapped_domain_names = []
        for domain in df['domain']:
            wrapped_domain_names.append(str('<br>'.join(textwrap.wrap(domain, width=20))))
        df['domain'] = wrapped_domain_names

        pie_figure = go.Figure(data=[go.Pie(labels=df['domain'],
                                            values=df['resource count'],
                                            title={
                                                #'text': 'Resources By Domain',
                                                'font': {'size': 16},
                                                'position': 'bottom right'})])
        pie_figure.update_traces(textposition='inside', textinfo='value+label')

        # return the pie chart
        return dcc.Graph(id='resources_by_domain_pie',
                         figure=pie_figure,
                         config={
                            'modeBarButtonsToRemove': buttonsToRemove
                         }
                        )

    def resources_by_publisher_table(self):

        df = self.resources_by_publisher_portal_df()

         # add a total of resource count at the end of the df
        total_resource_count = df['resource count'].sum()

        df_total = pd.DataFrame([['Total', total_resource_count]],
                            columns=['publisher','resource count'])
        df = df.append(df_total, ignore_index=True)

        # return the created DataTable
        return dash_table.DataTable(
            id='resource_by_publisher_table',
            columns=[{"id": "publisher", "name": "Publisher"},
                     {"id": "resource count", "name": "Resource Count"}],
            data=df.to_dict('records'),
            sort_action='native',
            style_cell={'textAlign': 'left',
                'whiteSpace': 'normal'},
            style_cell_conditional=[
                {'if': {'column_id': 'publisher'},
                'width': '70%', 'textAlign': 'right'},
                {'if': {'column_id': 'resource count'},
                'width': '30%'},
                #{'if': {'row_index': 'odd'},
                #'backgroundColor': 'rgb(248, 248, 248)'}
                ],
            style_table={
                        'maxHeight': '300px',
                        'maxWidth': '100%',
                        'overflowY': 'scroll',
                        'overflowX': 'hidden',
                        'margin': 0,
                        'padding': 0
            },
            style_header={
                        'backgroundColor': 'rgb(230, 230, 230)',
                        'fontWeight': 'bold',
                        'textAlign': 'center',
            }
        )

    def resources_by_publisher_pie(self):

        df = self.resources_by_publisher_portal_df()

        wrapped_publisher_names = []
        for publisher in df['publisher']:
            wrapped_publisher_names.append(str('<br>'.join(textwrap.wrap(publisher, width=20))))
        df['publisher'] = wrapped_publisher_names

        pie_figure = go.Figure(data=[go.Pie(labels=df['publisher'],
                                            values=df['resource count'],
                                            title={
                                                #'text': 'Resources By Domain',
                                                'font': {'size': 16},
                                                'position': 'bottom right'})])
        pie_figure.update_traces(textposition='inside', textinfo='value+label')

        # return the pie chart
        return dcc.Graph(id='resources_by_publisher_pie',
                         figure=pie_figure,
                         config={
                            'modeBarButtonsToRemove': buttonsToRemove
                         }
                        )

    def dataset_by_office_portal_data(self):
        rows = []
        total = 0

        datasets_by_publisher = self.ckan_api.datasets_by_publisher()
        for name, count in datasets_by_publisher:
            rows.append({'s' : name, 'datopian': count})
            total += count

        rows.sort(key = lambda item: item['datopian'], reverse=True)

        rows.append({'s' : 'Total', 'datopian': total})
        return rows

    def get_datasets_bars_portal_data(self):

        data_list = list()
        datasets_by_publisher = self.ckan_api.datasets_by_publisher()
        for name, count in datasets_by_publisher:
            legend_str = '<br>'.join(textwrap.wrap(name, width=20))
            data_list.append({
                'x': ['Datasets'], 'y': [count],
                'type': 'bar', 'name': legend_str
            })

        data_list.sort(key=lambda item: item['y'][0], reverse=True)
        return data_list

def generate_split_layout():
    """" function generates the layout for this page """

    p = InsightsPage()

    return html.Div(children=[

    # Totals Based on Original Scraper
    header('Initial Estimate', 'total-initial', INSIGHTS_TOTALS_INITIAL_TOOLTIP),
    html.Hr(),

    # LED displays
    led_display(32985,
        "Datasets"),
    led_display(52709,
        "Resources"),
    led_display(52745,
        "Pages"),
    led_display(26,
        "Domains"),

    # Totals Based on Original Scraper
    html.Br(),
    html.Br(),
    html.Br(),
    html.Br(),
    header('Based On Scraper', 'total-scraper', INSIGHTS_TOTALS_SCRAPED_TOOLTIP),
    html.Hr(),

    # LED displays
    led_display(p.total_datasets_count_stats(), "Datasets"),
    led_display(p.total_resource_count_stats(), "Resources"),
    led_display(p.total_page_count_stats(), "Pages"),
    led_display(p.total_domains_count_stats(), "Domains"),

    # Totals Based on Original Scraper
    html.Br(),
    html.Br(),
    html.Br(),
    html.Br(),
    header('Ingested Into Data Portal', 'total-ingested', INSIGHTS_TOTALS_INGESTED_TOOLTIP),
    html.Hr(),

    # LED displays
    led_display(p.ckan_api.total_scraped_datasets(),
        "Datasets"),
    led_display(p.ckan_api.total_scraped_resources(),
        "Resources"),
    led_display(p.ckan_api.total_scraped_pages(),
        "Pages"),
    led_display(p.ckan_api.total_scraped_domains(),
        "Domains"),


    # Datasets By Publisher
    html.Br(),
    html.Br(),
    html.Br(),
    html.Br(),
    header('Datasets Ingested Into The Portal By Publisher',
            'datasets-office', INSIGHTS_DATASETS_BY_OFFICE_TOOOLTIP),
    html.Hr(),

    html.Div([
        dash_table.DataTable(
            columns=[{'name': 'Publisher', 'id': 's'},
                    {'name': 'Count', 'id': 'datopian'}],
            #data=p.dataset_by_office_data(),
            data=p.dataset_by_office_portal_data(),
            sort_action='native',
            style_cell={'textAlign': 'left'},
            style_cell_conditional=[
                {'if': {'column_id': 's'},
                'width': '70%', 'textAlign': 'right'},
                {'if': {'column_id': 'datopian'},
                'width': '30%'}],
            style_table={
                'maxHeight': '300px',
                'overflowY': 'scroll',
                'overflowX': 'hidden',
            },
            style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold',
                    'textAlign': 'center',
                    }

        ),
    ], style={
            'width': '50%',
            'display': 'inline-block',
            'vertical-align': 'middle'}
    ),

    html.Div([
        dcc.Graph(
            figure={
                'data': p.get_datasets_bars_portal_data(),
                'layout': {
                    #'title': 'Datasets by Office'
                    #'showlegend': False
                    #'legend': {'x': 1.02},
                }
            },
            config={
                'modeBarButtonsToRemove': buttonsToRemove
            }
            ),
        ],
        style={
            'width': '50%',
            'display': 'inline-block',
            'vertical-align': 'middle'
            }
    ),

    # Resources by Publisher
    html.Br(),
    html.Br(),
    html.Br(),
    html.Br(),
    header('Resources Ingested Into The Portal By Publisher',
            'resources-office',INSIGHTS_RESOURCES_BY_OFFICE_TOOOLTIP),
    html.Hr(),

    html.Div([
        p.resources_by_publisher_table()
    ],
    style={
        'width': '50%',
        'display': 'inline-block',
        'vertical-align': 'middle',
        'overflow-x': 'auto',
        'margin-bottom': '50px',}
    ),

    html.Div([
        p.resources_by_publisher_pie(),
    ], style={
        'width': '50%',
        'display': 'inline-block',
        'vertical-align': 'middle'}
    ),


    # Datasets By Domain
    html.Br(),
    html.Br(),
    html.Br(),
    html.Br(),
    header('Datasets Ingested Into The Portal By Domain',
            'datasets-domain',INSIGHTS_DATASETS_BY_DOMAIN_TOOOLTIP),
    html.Hr(),

    html.Div([
        p.dataset_by_domain_table()
    ],
    style={
        'width': '50%',
        'display': 'inline-block',
        'vertical-align': 'middle',
        'overflow-x': 'auto',
        'margin-bottom': '50px',}
    ),

    html.Div([
        p.dataset_by_domain_bar()],
        style={
            'width': '50%',
            'display': 'inline-block',
            'vertical-align': 'middle',
            'margin-bottom': '50px',
        }
    ),

    # Resources by Domain
    html.Br(),
    html.Br(),
    html.Br(),
    html.Br(),
    header('Resources Ingested Into The Portal By Domain',
            'resources-domain',INSIGHTS_RESOURCES_BY_DOMAIN_TOOOLTIP),
    html.Hr(),

    html.Div([
        p.resources_by_domain_table()
    ], style={
        'width': '50%',
        'display': 'inline-block',
        'vertical-align': 'middle'}
    ),

    html.Div([
        p.resources_by_domain_pie(),
    ], style={
        'width': '50%',
        'display': 'inline-block',
        'vertical-align': 'middle'}
    ),


])

external_stylesheets = [dbc.themes.BOOTSTRAP, 'https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = generate_split_layout

if __name__ == '__main__':
    app.run_server(debug=False, dev_tools_hot_reload=True, host='0.0.0.0')
