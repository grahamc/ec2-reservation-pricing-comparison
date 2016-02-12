#!/usr/bin/env python3

from pprint import pprint
from parse import pricing_data, TypeAtLocation
import json
import os


with open('price.json') as pj:
    price_doc = json.loads(pj.read())

data = pricing_data(price_doc)

def build_table(data, os):
    table = {
        'limited_os': os,
        'regions': data['dimensions']['regions'],
        'rows': [],
    }

    for inst_type in data['dimensions']['instance_types']:
        row = {
            'type': inst_type,
            'columns': []
        }
        for region in data['dimensions']['regions']:
            typeloc = TypeAtLocation(os, region, inst_type)
            row['columns'].append(data['prices'].get(typeloc))
        table['rows'].append(row)

    return table

def filename_instance_location(instance_location):
    return "./{}-{}-{}.html".format(
        instance_location.os,
        instance_location.region,
        instance_location.type
    )

def name_price(price):
    if price.Name == 'On Demand':
        return price.Name
    return '{name} ({years} years)'.format(
        name=price.Name,
        years=price.Years
    )

def render_table(table):
    html = """
    <h1>EC2 Payment Plan Comparisons, OS: {os}</h1>

    <table class="table table-striped table-hover" id="os-{os}">
    <tr>
    <td></td>
    """.format(os=table['limited_os']) + "\n".join(["<th>{}</th>".format(region)
                     for region in table['regions']]) + """
    </tr>

    """

    for row in table['rows']:
        html += "<tr><th>{inst}</th>".format(inst=row['type'])

        for column in row['columns']:
            if column is None:
                html += "<td>&nbsp;</td>"
            else:
                html += '<td><a href="{url}">{inst} / {region} / {os}</a></td>'.format(
                    url=filename_instance_location(column['instance_location']),
                    inst=column['instance_location'].type,
                    region=column['instance_location'].region,
                    os=table['limited_os']
                )
        html += "</tr>"
    html += "</table>"

    return html

def build_3yr_monthly_costs(price, years=3):
    spent = 0
    datapoints = []

    for year in range(0, years):
        if year % price.Years == 0:
            spent += price.UpFront


        for month in range(0, 12):
            spent += price.Hourly * 24 * 30
            datapoints.append(spent)

    return { 'price': price, 'datapoints': datapoints }

def build_graph(prices):
    return [build_3yr_monthly_costs(plan) for plan in prices['prices']]


def footer():
    return """
    <footer>
    By <a target='_blank' href='http://grahamc.com/'>Graham Christensen</a> with
    source on <a target='_blank' href='https://github.com/grahamc/ec2-reservation-pricing-comparison'>GitHub</a>.
    </footer>
    <script>
    (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
    (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
    m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
    })(window,document,'script','//www.google-analytics.com/analytics.js','ga');

    ga('create', 'UA-34283093-1', 'auto');
    ga('send', 'pageview');

    </script>
    """

def render_graph(instloc, graph_data):
    title = 'Cumulative Cost of {type} in {region} on EC2 with OS {os}'.format(
        type=instloc.type,
        region=instloc.region,
        os=instloc.os
    )

    graph = {
        'title': title,
        'tooltip': { 'shared': True },
        'title': {
            'text': title
        },
        'xAxis': { 'title': { 'text': 'months' }, 'categories': list(range(1, 36)) },
        'yAxis': { 'title': { 'text': 'USD' }, 'min': 0 },
        'series': [],
    }

    for gen in graph_data:
        graph['series'].append({
            'name': name_price(gen['price']),
            'data': gen['datapoints']
        })

    html = """
    <title>{title}</title>
    <script type="text/javascript" src="https://code.jquery.com/jquery-1.9.1.js"></script>
    <script src="http://code.highcharts.com/highcharts.js"></script>
    <script src="http://code.highcharts.com/modules/exporting.js"></script>
    <script>
    $(function () {{
        $('#container-{id}').highcharts({json});
    }});
    </script>

    <div id="container-{id}" style="height: 100%; width: 100%;"></div>
    {footer}
    """.format(
        id='main-graph',
        title=title,
        json=json.dumps(graph),
        footer=footer()
    )

    return html


for instloc, prices  in data['prices'].items():
    url = filename_instance_location(instloc)
    with open(os.path.join("./out/", url), 'w') as fp:
        fp.write(render_graph(instloc, build_graph(prices)))


table_html = """
    <link href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.2/css/bootstrap.min.css" rel="stylesheet">
    <title>EC2 Payment Plan Comparisons</title>
    """

for os in data['dimensions']['operating_systems']:
    table_html += render_table(build_table(data, os))

table_html += footer()
with open('out/index.html', 'w') as fp:
    fp.write(table_html)
