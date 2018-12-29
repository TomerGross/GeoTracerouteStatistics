from __future__ import print_function


import urllib2
import sys
import subprocess
import re
import json
import os
import socket
import collections

api_key = "AIzaSyCbUBSKwJMEDq1_XJm4_1MoUzVPKzWh2eo"
electron_path = os.getcwd() + "\\electron-quick-start"
goal = "www.u-tokyo.ac.jp"
flag = True


class Map(object):


    def __init__(self):
        self._locations = []

    def add_point(self, coordinates):
        self._locations.append(coordinates)

    def __str__(self):



        centerLat = sum((x[0] for x in self._locations)) / len(self._locations)
        centerLon = sum((x[1] for x in self._locations)) / len(self._locations)


        add_markers = "\n".join(
            [ """new google.maps.Marker({{
                position: new google.maps.LatLng({lat}, {lon}),
                icon: "Google Maps Markers/blue_Marker{order}.png",
                map: map
                
                }});""".format(lat=x[0], lon=x[1], order=x[2]) for x in self._locations
            ])


        return """
            <script src="https://maps.googleapis.com/maps/api/js?v=3.exp&sensor=false"></script>
            <div id="map-canvas" style="height: 100%; width: 100%"></div>
            <script type="text/javascript">
                var map;
                function showMap() {{
                    map = new google.maps.Map(document.getElementById("map-canvas"), {{
                        zoom: 3,
                        center: new google.maps.LatLng({centerLat}, {centerLon})
                    }});
                    {markersCode}
                }}
                google.maps.event.addDomListener(window, 'load', showMap);
            </script>
        """.format(centerLat=centerLat, centerLon=centerLon,
                   markersCode=add_markers)





def validate_ip(ip):
    """
    Validates all the ip addresses
    """

    splited = ip.split('.')
    for i in range(4):
        check_num = int(splited[i])
        if check_num > 255 or check_num < 0:
            return False
    return True


def route_by_dicts(ips):
    """
    Send request to "http://ip-api.com" for information about these ips in JSON format
    # in python - json converted into dictionary using `json.loads`
    """
    route_list_dicts = []

    for ip in ips:
        url = "http://ip-api.com/json/" + ip
        response = urllib2.urlopen(url)
        data = json.loads(response.read())
        route_list_dicts.append(data)

    return route_list_dicts


def route_by_ips(goal):
    """
    Returns a list of router addresses we passed through, until we reached the goal
    """
    global flag
    counter = ord("A")
    route_list = []

    route_list_dicts = []

    goal = socket.gethostbyaddr(goal)[0]
    last = goal
    traceroute = subprocess.Popen(["tracert", '-d', goal], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while True:

        hop = traceroute.stdout.readline()

        end_sign = re.match("Trace complete\.", hop)
        if end_sign:
            break
        find_match = re.search("\ (\d+\.\d+\.\d+\.\d+)", hop)
        if not find_match:
            continue

        last = find_match.group(1)
        counter2 = len(re.findall("\d+\ ms", hop))

        match = re.findall("(\d+)\ ms", hop)

        sum=0
        for i in range(len(match)):
            sum += int(match[i])

        avg = sum / len(match)

        ip = find_match.group(1)
        route_list.append(str(ip))

        print("hop " + chr(counter))

        url = "http://ip-api.com/json/" + ip
        response = urllib2.urlopen(url)
        data = json.loads(response.read())
        route_list_dicts.append(data)

        route_list_dicts[-1]["order"] = chr(counter)
        route_list_dicts[-1]["success"] = str(counter2) + "/3 in " + str(avg) + " ms"

        counter += 1

    if socket.gethostbyaddr(last)[0] != goal:
        flag = False
    #print(route_list_dicts)
    #print(flag)
    #print(socket.gethostbyaddr(last)[0] + "  " + goal)
    return route_list_dicts



def current_json(route):
    """
    Creates a json object from the route information in python syntax
    """
    to_json_f = {}



    for p in route:

        if p["status"] == "success":

            if goal not in to_json_f.keys():
                to_json_f[goal] = {p["query"] : {"country": p["country"], "city": p["city"], "regionName": p["regionName"],
                                     "timezone": p["timezone"], "lon": p["lon"], "lat": p["lat"], "visits": 1, "order": p["order"], "success" : p["success"]}}
            else:
                to_json_f[goal][p["query"]] = {"country": p["country"], "city": p["city"], "regionName": p["regionName"],
                                     "timezone": p["timezone"], "lon": p["lon"], "lat": p["lat"], "visits": 1, "order": p["order"], "success" : p["success"]}
        else:
            if goal not in to_json_f.keys():
                to_json_f[goal] = {p["query"] : {"country": "Fail", "city": "Fail", "regionName": "Fail",
                                     "timezone": "Fail", "lon": "Fail", "lat": "Fail", "visits": 1, "order": p["order"], "success" : p["success"]}}
            else:
                to_json_f[goal][p["query"]] = {"country": "Fail", "city": "Fail", "regionName": "Fail",
                                     "timezone": "Fail", "lon": "Fail", "lat": "Fail", "visits": 1, "order": p["order"], "success" : p["success"]}

    return to_json_f


def check_if_exist(ip, total_dict):
    """
    Checks if ip is already exits in the db
    """

    for i in range(len(total_dict.keys())):

        if total_dict.keys()[i] == ip:
            return True

    return False


def update_json_db(total_json, curr_js):

    t_json = total_json

    if goal in t_json.keys():

        for i in range(len(curr_js[goal])):

            bool = check_if_exist(curr_js[goal].keys()[i], t_json[goal])
            if bool:
                print("trying")
                t_json[goal][curr_js[goal].keys()[i]]["visits"] += 1
            else:
                v = curr_js[goal].values()[i]
                t_json[goal][curr_js[goal].keys()[i]] = {"country": v["country"], "city": v["city"],
                                        "regionName": v["regionName"],
                                        "timezone": v["timezone"], "lon": v["lon"], "lat": v["lat"],
                                        "visits": 1, "order": v["order"]}


    else:
        t_json[goal] = curr_js[goal]

    return t_json


def remove_duplicates(list_of_dicts):
    seen = set()
    new_l = []
    for d in list_of_dicts:
        t = tuple(d.items())
        if t not in seen:
            seen.add(t)
            new_l.append(d)

    return new_l


def main():

    global goal


    if len(sys.argv) > 1:
        goal = sys.argv[1]

    print(goal)


    route = remove_duplicates(route_by_ips(goal))



    total_json_file = {}
    cur_json = {}

    if os.path.isfile("total.json"):
        with open('total.json', 'r') as f:
            total_json_file = json.load(f)

    cur_json = current_json(route)
    total_json_file = update_json_db(total_json_file, cur_json)



    temp = collections.OrderedDict(sorted(cur_json[goal].items(), key=lambda tup: tup[1]["order"]))


    cur_json[goal] = temp

    """with open('current.json', 'w') as out:
        json.dump(cur_json, out, indent=4)"""
	
    with open('total.json', 'w') as outfile:
        json.dump(total_json_file, outfile, indent=4)

    mapy = Map()


    for ip_info in cur_json[goal].values():

        if ip_info["regionName"] != "Fail":
            mapy.add_point((float(ip_info["lat"]), float(ip_info["lon"]), ip_info["order"]))



    text = """<html>
              <head>

              </head>
              <body>

                <!-- Latest compiled and minified CSS -->
                <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css">

                <!-- jQuery library -->
                <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>

                <!-- Latest compiled JavaScript -->
                <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js"></script>

                <table id="table" class="table table-striped"></table>


                <script type="text/javascript">        


                    json_data = JSON.parse(`{jsonstring}`);

                    table = document.getElementById("table");

                    function enumerate(jsonList) {{ return Object.keys(jsonList).map(function(key, index) {{ return [index, key,  jsonList[key]]; }}); }}

                    for (var line in json_data) {{

                        var new_row = table.insertRow(table.length + 1);
                        new_row.insertCell(0).innerHTML = line;
                        
                        for (var tup of enumerate(json_data[line]))
                            new_row.insertCell(tup[0]+1).innerHTML = tup[2];

                    }}

                    if (Object.keys(json_data).length > 0){{

                        var header_row = table.createTHead().insertRow(0);
                        header_row.insertCell(0).innerHTML = "ip";

                        for (var tup of enumerate(json_data[Object.keys(json_data)[0]]))
                            header_row.insertCell(tup[0]+1).innerHTML = tup[1];

                    }}
                    

                </script>

              </body>
              </html>""".format(jsonstring=str(json.dumps(cur_json[goal])))

    with open(electron_path + "\\index.html", "w") as outy:
        print(text, file=outy)

    with open(electron_path + "\\index.html", "a") as out:
        print(mapy, file=out)



    os.chdir(electron_path)
    os.system('npm start')



if __name__ == '__main__':
    main()