#!/usr/bin/env python3

from pprint import pprint
from collections import namedtuple

TypeAtLocation = namedtuple('InstanceTypeAtRegion', ['os', 'region', 'type'])
Price = namedtuple('Price', ['Name', 'UpFront', 'Hourly', 'Years'])


location_to_name = {
    'Asia Pacific (Seoul)': 'ap-northeast-2 ',
    'Asia Pacific (Singapore)': 'ap-southeast-1',
    'Asia Pacific (Sydney)': 'ap-southeast-2',
    'Asia Pacific (Tokyo)': 'ap-northeast-1',
    'AWS GovCloud (US)': 'us-gov-west-1',
    'EU (Frankfurt)': 'eu-central-1 ',
    'EU (Ireland)': 'eu-west-1',
    'US East (N. Virginia)': 'us-east-1',
    'US West (N. California)': 'us-west-1',
    'US West (Oregon)': 'us-west-2',
    'South America (Sao Paulo)': 'sa-east-1',
}


def servers_from_doc(doc):
    servers = {
        k: v
        for k, v in doc['products'].items()
        if 'productFamily' in v and v['productFamily'] == 'Compute Instance'
    }

    return servers

def unique_attributes(servers, attribute):
    return set([v['attributes'][attribute]
                for k, v in servers.items()])


def Price_from_term(term):
    name = term['termAttributes'].get('PurchaseOption', 'On Demand')
    years = int(term['termAttributes'].get('LeaseContractLength', '1yr')[0:-2])
    up_front = 0
    hourly = 0

    for k, dimension in term['priceDimensions'].items():
        if dimension['unit'] == 'Quantity':
            up_front = dimension['pricePerUnit']['USD']
        elif dimension['unit'] == 'Hrs':
            hourly = dimension['pricePerUnit']['USD']

    return Price(name, float(up_front), float(hourly), int(years))


def TypeAtLocation_from_product(product):
    attrs = product['attributes']
    location = location_to_name[attrs['location']]

    return TypeAtLocation(attrs['operatingSystem'], location,
                          attrs['instanceType'])


def pricing_data(data):
    assert(data['formatVersion'] == 'v1.0')
    assert(data['offerCode'] == 'AmazonEC2')

    del data['formatVersion']
    del data['offerCode']



    results = {}

    results['meta'] ={
        'disclaimer': data['disclaimer'],
        'version': data['version'],
        'date': data['publicationDate']
    }
    del data['disclaimer']
    del data['version']
    del data['publicationDate']

    servers = servers_from_doc(data)

    results['dimensions'] =  {
        'operating_systems': unique_attributes(servers, 'operatingSystem'),
        'instance_types': unique_attributes(servers, 'instanceType'),
        'regions': [region for name, region in location_to_name.items()]
    }

    results['prices'] = {}
    for _, server in servers.items():
        instance_location = TypeAtLocation_from_product(server)

        prices = []

        sku = server['sku']
        on_demand = [v for k, v in data['terms']['OnDemand'][sku].items()]
        reservations = [v for k, v in data['terms']['Reserved'].get(sku, {}).items()]

        terms = on_demand + reservations
        for term in terms:
            p = Price_from_term(term)
            if p.Hourly > 0 or p.UpFront > 0:
                prices.append(p)

        if len(prices) > 0:
            results['prices'][instance_location] = {
                'server': server,
                'prices': prices,
                'instance_location': instance_location
            }

    return results
