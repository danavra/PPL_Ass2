

import sqlite3
import csv
from statistics import mean
from math import sin, cos, sqrt, atan2, radians

class Database:

    def __init__(self):
        '''
        creates the table if not allready created
        '''
        connection = sqlite3.connect('lite.db')
        cur = connection.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS Trips (duration INTEGER , start_location VARCHAR , end_location VARCHAR, birthDate INTEGER , sex INTEGER, start_lat NUMERIC, start_lang NUMERIC, end_lat NUMERIC, end_lang NUMERIC )")
        connection.commit()
        connection.close()



    def loadData(self,csvfile):
        '''
         loads the data from a csv file to the DB
        :param csvfile: csvfile: the local path of the csv file
        '''
        connection = sqlite3.connect('lite.db')
        cur = connection.cursor()

        with open('BikeShare.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if line_count != 0:
                    if not row[0] or not row[4] or not row[8] or not row[13] or not row[14] or not row[5] or not row[6] or not row[9] or not row[10]:
                        print('\nbad data\n')
                        continue
                    cur.execute("INSERT INTO Trips VALUES (?,?,?,?,?,?,?,?,?); ",(row[0], row[4], row[8], row[13], row[14],row[5],row[6],row[9],row[10]))
                line_count += 1
                print("\rlisting #" + str(line_count),end="")

            connection.commit()
            print(f'\nProcessed {line_count} lines.')
            connection.close()


# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


    def findTrip(self,start,time_low,time_high,riding_level,sex):
        '''
        will return the relevant trips
        :param start: the start locations name
        :param time_low: the minimum time (min) of a trip wanted
        :param time_high: the maximum time (min) of a trip wanted
        :param riding_level: the level of the rider (begginer: -1, intermedian: 0, pro: 1)
        :param sex: the sex of the rider if is a fucking chauvinistic pig (None: good guy, 0: female, 1: male, 2: had an operation)
        :return: a sorted list of locations and their data sorted by the range given
        '''
        mid = (time_high +time_low)/2
        end_location = self.getAllEndPoints(start,sex)
        relaventETAs = []
        for location in end_location:
            realETA =  self.getETA(end_location[location],riding_level)
            if realETA >= time_low and  realETA <= time_high:  # in range => add to relaventETAs[]
                new_set={}
                new_set['destination'] = location
                new_set['eta'] = realETA
                new_set['Distance'] = self.getDistance(start,location)
                relaventETAs.append(new_set)

        return sorted(relaventETAs, key=lambda i: abs(mid - i['eta'])) # sorts by clossest to center of given range



    def getETA(self,all_etas,riding_level):
        '''
        calculattes the estimated eta based on the riders skill level:
            example: if you are a intermedian rider, it will return the average time of every body.
                     if you are a pro/begginer, it will calculate the total avrage, then make an average of only
                     the etas that are less/more than the total average.
        :param all_etas:  a list of all of the eta's aquiered for the current trip
        :param riding_level: the skill of the rider (begginer: -1, intermedian: 0, pro: 1)
        :return:  will return a estimated ETA according to the riders skill level
        '''

        setOfETA = set(all_etas) # takes care of only one value (error is when taking only values over or under)

        if len(setOfETA) == 1:
            return all_etas[0] / 60

        total_avg = mean(all_etas)
        if riding_level == 0: #intermide
            return total_avg/60
        try:
            if len(all_etas) == 1:
                return all_etas[0]/60

            if riding_level < 0: #beginner

                return mean(list(filter(lambda x: (x > total_avg),all_etas)))/60

            if riding_level > 0: #pro
                return mean(list(filter(lambda x: (x < total_avg), all_etas))) / 60

        except:
            print("error: " + str(all_etas))
            return -1



    def getAllEndPoints(self,start,sex):
        '''
         retrieves all of the trips that start from the given start point with regards to the sex of the wanted data
        :param start: the start location's name.
        :param sex: (None: use all data, 0: only female data, 1: only male data , 2: only trans data)
        :return: all the end locations + eta that a trip from start to them have been found in the DB
        '''

        connection = sqlite3.connect('lite.db')
        ans = {}
        cur = connection.cursor()

        if sex == None:
            cur.execute("SELECT end_location ,duration FROM Trips WHERE start_location = ?",(start,))
        else:
            cur.execute("SELECT end_location ,duration FROM Trips WHERE (start_location = ? AND sex = ?)",(start, sex,))

        rows = cur.fetchall()
        if len(rows) == 0:
            print( "It looks like there is no bike trip that will satisfy your needs,\nThe good news is that we have found a Mcdonalds extremely close to your current location! (name of branch: Mcdonalds " + start + " branch)")
        for row in rows:

            destination = row[0]
            eta = row[1]
            if destination in ans:
                ans[destination].append(eta)
            else:
                ans[destination] = [eta];

        connection.close()

        return ans


    def calculateAirDistance(self,start_lat,star_lang,end_lat,end_lang):
        '''
          will calculate the distance in KM between two coordinates
        :param start_lat: start lattitude
        :param star_lang:  start longtitude
        :param end_lat: end lattitude
        :param end_lang: end longtitude
        :return:
        '''
        if not star_lang or not start_lat or not end_lang or not end_lat:
            return None
        # approximate radius of earth in km
        R = 6373.0
        lat1 = radians(start_lat)
        lon1 = radians(star_lang)
        lat2 = radians(end_lat)
        lon2 = radians(end_lang)

        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance = R * c

        return distance


    def getDistance(self,start,end):
        '''
        will calculate the average distance between two locations out of all the coordinates in the DB
        :param start: start location's name
        :param end: end location's name
        :return: the average distance between two locations
        '''
        connection = sqlite3.connect('lite.db')
        allDistances = []
        cur = connection.cursor()
        cur.execute("SELECT start_lat,start_lang,end_lat,end_lang FROM Trips WHERE (start_location = ? AND end_location = ?)",(start,end))
        rows = cur.fetchall()
        if len(rows) == 0:
           return None

        for row in rows:
            distance = self.calculateAirDistance(row[0], row[1], row[2], row[3])
            if distance != None:
                allDistances.append(distance)

        return mean(allDistances)
        connection.close()


# ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////




db = Database()
# db.loadData('BikeShare.csv')
minTime = 1
maxTime =10
level = 1
sex = 1
print(db.findTrip('Hilltop',minTime,maxTime,level,sex))
