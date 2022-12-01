require 'net/http'
require 'date'
require 'uri'
require 'json'
require 'nokogiri'
require 'fileutils'


# 산업통상자원부 산업통계분석시스템 홈페이지에서 경기종합지수 데이터 내려 받기

def http_post( url )
    uri = URI( url )
    data = NIL
    res = Net::HTTP.post(uri, data, headers={}) # => String
    case res
    when Net::HTTPSuccess, Net::HTTPRedirection
        res
    when Net::HTTPError
        false
    else
        res
    end
end

def xmltext_to_json( xmltext, title, current_date )
    # xml = Nokogiri::XML.parse(res.body) 
    xml = Nokogiri::XML.parse(xmltext) 
    # puts xml.at('I').attributes
    raw_text = xml.at('B').text.gsub(/[<>]/, "").strip()
    # puts raw_text
    my_data = {}
    raw_data = raw_text.split("\n").map{ |x| x.strip().gsub(/\s/, "")}.filter{ |x| x.length > 0 }

    for e in raw_data
        k, v = e.split("=")   
        my_data[k] = v.gsub('"', '').to_f
    end
    # puts my_data
    _data = my_data.sort.to_h
    data = _data.map { |key, value| { d: key, v: value } }
    {
        title: title,
        current_date: current_date,
        data: data
    }.to_json
end

url_main = "https://www.istans.or.kr/su/newSuGridData.do"
url_params = "&pivotType=1&datePeriod=4&countryCode=WLD&from_year_month=1970&to_year_month=" + Time.now.year.to_s + "&from_month=1&to_month=12"
urls=[
    { name: "CoincidenceIndex", namek: "경기동행지수", url: url_main + "?wstScode=S99" + url_params},
    { name: "CoincidenceIndexCyclicalComponent", namek: "경기동행지수_순환변동치", url: url_main + "?wstScode=S100" + url_params},
    { name: "LeadingIndex", namek: "경기선행지수", url: url_main + "?wstScode=S101" + url_params},
    { name: "LeadingIndexCyclicalComponent", namek: "경기선행지수_순환변동치", url: url_main + "?wstScode=S102" + url_params}
]

res_data = []
for e in urls
    res = http_post( e[:url] )
    if !res 
        exit
    end
    res_data.push( res.body )
end

today = Time.now.strftime("%Y%m%d")
target_path = File.join("_data", "CompositeIndex")
Dir.mkdir(target_path) unless File.exists?(target_path)

urls.each_with_index do | e, i |
    filename = File.join(target_path, e[:name] + ".json" )
    json_text = xmltext_to_json( res_data[i], title=e[:namek], current_date=today )
	File.open(filename, "w") { |f| f.write( json_text ) }
end