# coding=utf-8
import json
import geojson
import time
import xml.dom.minidom

from datetime import datetime, timedelta
import requests
import sys

def data_from_xml_json(xmlfile):
    fp = open(xmlfile)
    data = fp.read()
    # this is for the air quality data, to split some charicters
    data = data.replace("a:", "")
    data = data.replace("b:", "")
    data = data.replace("c:", "")
    data = data.replace("&mdash", "-")
    return xmlparse(data)


def xmlparse(xmlstr):
    '''
       parse air quality xml data to dict list
    '''
    dom = xml.dom.minidom.parseString(xmlstr)
    root = dom.documentElement
    stats = dom.getElementsByTagName("AQIDataPublishLive")
    airdata = []
    for stat in stats:
        # print len(stat.childNodes)
        r = {}
        for node in stat.childNodes:
            if (node.nodeName == "#text" or
                    node.nodeName == "OpenAccessGenerated"):
                continue
            inx = node.nodeName
            inx = inx.lower()
            for n in node.childNodes:
                # print n.data
                r[inx] = n.data
        airdata.append(r)
    return airdata
    # return json.dumps(airdata, ensure_ascii=False)

def filterkeys(dct, keys):
    return { k: v for k, v in dct.items() if k in keys }

if __name__ == "__main__":
#    aqistationcode = ['1454A', '1455A', '1452A', '1453A']
    openaqlocation = ['金鼎山', '碧鸡广场', '龙泉镇', '东风东路']
#    openaqlocationid = [9657, 9260, 8961, 9841]

    data = data_from_xml_json("data.xml")
    # loop location names first otherwise the location order will be according to the xml input
    filtered = [ filterkeys(recd, ['pm2_5', 'pm2_5_24h', 'positionname', 'primarypollutant', 'stationcode', 'timepoint']) for locationname in openaqlocation for recd in data if recd['positionname'] == locationname ]
#    print([ rec['positionname'] for rec in filtered ])
    latest = filtered[0]['timepoint']
    lateststamp = datetime.fromisoformat(latest)

    previouscheck = int(open('lastcheck').readline())
    if lateststamp.hour == previouscheck:
      sys.exit(0)
    elif lateststamp.hour == (previouscheck + 1) % 24:
      # load old data
      previousdata = [ line[0:-1].split(',') for line in open('/Users/shared/www/pm25.txt').readlines() ]
      newdata = [ [new['pm2_5']] + old[0:-1] for new, old in zip(filtered, previousdata) ]
    else:
      nhours = 36
      limit = nhours * len(openaqlocation)

      locations = '&'.join([ 'location=' + location for location in openaqlocation ])
      openaq = [ filterkeys(recd, ['date', 'location', 'locationId', 'value']) for recd in requests.get(f'https://docs.openaq.org/v2/measurements?parameter=pm25&{locations}&order_by=datetime&sort=desc&limit={limit}').json()['results'] ]
      openaq = [ {k: datetime.fromisoformat(v['local']).replace(tzinfo=None) if k == 'date' else v for k, v in recd.items() } for recd in openaq ]
#      print([ len([ rec for rec in openaq if rec['location'] == site ]) for site in openaqlocation ])
#      print([[ rec for rec in openaq if rec['location'] == site ] for site in openaqlocation ])

      def getvalue(location, dh):
          try:
              return next(filter(lambda m: m['location'] == location and m['date'] == lateststamp - timedelta(hours=dh), openaq))['value']
          except StopIteration:
              return -1
      newdata = [ [ newest['pm2_5'] ] + [ str(getvalue(newest['positionname'], dh)) for dh in range(1, nhours) ] for newest in filtered ]
    with open('/Users/shared/www/pm25.txt', 'w') as f:
      for locationdata in newdata:
         f.write(','.join([ str(pt) for pt in locationdata ]) + '\n')
    with open('lastcheck', 'w') as f:
      f.write(str(lateststamp.hour))

    sys.exit(0)

    featList = []
    for recd in data:
        try:
            lon = float(recd["longitude"])
            lat = float(recd["latitude"])
        except:
            continue
        geom = geojson.Point((lon, lat))
        del recd["longitude"]
        del recd["latitude"]
        properties = recd
        feat = geojson.Feature(geometry=geom, properties=properties)
        featList.append(feat)
    fc = geojson.FeatureCollection(featList)
    fname = time.strftime("%Y-%m-%d-%H", time.localtime())
    fstr = geojson.dumps(fc, sort_keys=True)
    fp = open("archives/%s.json" % fname, "w")
    fp.write(fstr)
    fp.close()
    fp = open("airnow.json", "w")
    fp.write(fstr)
    fp.close()
