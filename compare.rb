#!/usr/bin/env ruby

require 'json'

def raw_data
  json = File.read('./price.fmt.json')
  JSON.parse(json)
end

data = {}

raw_data['config']['regions'].each do |region|
  region['instanceTypes'].each do |type|
    rates = {}
    type['terms'].each do |term|
      rates['ondemand'] = {
        years: 0,
        upfront: 0,
        perhr: term['onDemandHourly'].first['prices']['USD'].to_f,
        savings: 0,
      }


      term['purchaseOptions'].each do |opt|
        values = {}
        opt['valueColumns'].each do |col|
          values[col['name']] = col['prices']['USD'].to_f
        end

        key = opt['purchaseOption'] + '-' + term['term']
        rates[key] = {
          years: term['term'][-1].to_i,
          upfront: values['upfront'],
          perhr: values['monthlyStar'] / 30 / 24,
          savings: opt['savingsOverOD'],
        }
      end
    end
    data[type['type']] ||= {}
    data[type['type']][region['region']] = rates
  end
end

graphs = {}
categories = (1..36).to_a
data.each do |type, regions|
  regions.each do |region, costs|
    local_graphs = {
      title:  [type, region].join('-'),
      graph: {
        tooltip: { shared: true },
        title: { text: "Cumulative Cost of #{type} in #{region} on EC2" },
        xAxis: { title: { text: 'months' }, categories: categories },
        yAxis: { title: { text: 'USD' }, min: 0 },
        series: [],
      }
    }
    costs.each do |reservation, pricing|
      datapoints = []

      spent = 0
      3.times do |year|
        puts pricing.inspect
        if pricing[:years] > 0
          if year % pricing[:years] == 0
            spent += pricing[:upfront]
          end
        end
        12.times do |i|
          spent += pricing[:perhr] * 24 * 30
          datapoints << spent.round(3)
        end
      end

      local_graphs[:graph][:series] << {
        name:  reservation,
        data: datapoints
      }
    end
    graphs[region] ||= {}
    graphs[region][type] = local_graphs
  end
end



def score_type(type)
  desc = type.match(/^(?<category>[a-z]+)(?<revision>\d+)\.(?<multiplier>\d+)?(?<subtype>.*)$/)
  categories = ['t', 'm', 'c', 'g', 'r', 'i', 'hs']
  subtypes = ['micro', 'small', 'medium', 'large', 'xlarge']

  score = 0
  score += categories.index(desc[:category]).to_i * 10000
  score += desc[:revision].to_i * 1000
  score += subtypes.index(desc[:subtype]).to_i * 100
  score += desc[:multiplier].to_i
  score
end


def sort_types(types)
  types.sort_by { |type| score_type(type) }
end


def analytics_code
"
<footer>By <a target='_blank' href='http://grahamc.com/'>Graham Christensen</a></footer>
<script>
  (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
  (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
  m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
  })(window,document,'script','//www.google-analytics.com/analytics.js','ga');

  ga('create', 'UA-34283093-1', 'auto');
  ga('send', 'pageview');

</script>
"
end

def make_table(graphs)
  regions = []
  types = []
  graphs.each do |region, ltypes|
    regions << region
    ltypes.each do |type, args|
      types << type
    end
  end

  types.uniq!


  str = ''
  str += '<title>EC2 Payment Plan Comparisons</title>'
  str += '<link href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.2/css/bootstrap.min.css" rel="stylesheet">'
  str += '<h1>EC2 Payment Plan Comparisons</h1>'
  str += '<table class="table table-striped table-hover">'
  str += '<tr>'
  str += '<td></td>'
  regions.sort.each do |region|
    str += "<th>#{region}</th>"
  end
  str += '</tr>'

  sort_types(types).each do |type|
    str += '<tr>'
    str += "<th>#{type}</th>"
    regions.sort.each do |region|
      graph = graphs[region][type]
      str += '<td>'
      str += "<a href='./#{graph[:title]}.html'>#{graph[:title]}</a>" if graph
      str += '</td>'
    end
    str += '</tr>'
  end
  str += "</table>"
  str += analytics_code
end
File.write('./out/index.html', make_table(graphs))

def make_chart(args)
  str = ''
  str += "<title>#{args[:graph][:title][:text]}</title>"
  str += '<script type="text/javascript" src="https://code.jquery.com/jquery-1.9.1.js"></script>'
  str += '<script src="http://code.highcharts.com/highcharts.js"></script>'
  str += '<script src="http://code.highcharts.com/modules/exporting.js"></script>'
  str += "<script>$(function () {"
  str += "$('#container-#{args[:title].sub(/\./, '-')}').highcharts(#{JSON.pretty_generate(args[:graph])});"
  str += "});</script>"
  str += "<div id='container-#{args[:title].sub(/\./, '-')}' style='height: 100%; width: 100%;'></div>"
  str += analytics_code
  return str
end

graphs.each do |region, types|
  types.each do |type, args|
    File.write("./out/#{args[:title]}.html", make_chart(args))
  end
end

