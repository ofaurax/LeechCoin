#!/usr/bin/env python
# coding=utf-8

import argparse
import urllib2  # python 2.7
import re
import sqlite3
import traceback
import datetime

headers = { 'User-Agent' : 'Mozilla/5.0 (compatible; Googlebot/2.1;'
                               +' +http://www.google.com/bot.html)' } 
                               # http://www.useragentstring.com

parser = argparse.ArgumentParser()
parser.add_argument('cmd')
parser.add_argument('-d',
                    help='database name to use (default:database.db)',
                    default='database.db')
parser.add_argument('params', nargs='*')

args = parser.parse_args()

print 'Commande :', args.cmd
print 'Args :', args
cmd = args.cmd
database = args.d

fgen = u'{0} {1:6}€ {2:3}m² {3} {4:30} {5:25} {6}/{7}/{8} {9}'
fdb = u'DB : ' + fgen

if cmd == 'help':
    print 'leech [num]: download of data from page [num] (default:1)'

if cmd == 'list':
    conn = sqlite3.connect(database)
    c = conn.cursor()
    
    for tmp in c.execute('SELECT * FROM apparts'):
        print fdb.format(*tmp)

if cmd == 'leech':

    try:
        page = int(args.params[0])
    except:
        page = 1

    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS apparts (id text PRIMARY KEY, prix int, surface int, cp int, ville text, nom text, jour int, mois int, annee int, heure text)')

    req = urllib2.Request(
        'http://www.leboncoin.fr/ventes_immobilieres/offres/'
        + 'provence_alpes_cote_d_azur/bouches_du_rhone/'
        + '?pe=8&sqs=6&ros=2&ret=1&ret=2&f=p&o=' + str(page), None, headers) 
    response = urllib2.urlopen(req)
    re_id = re.compile('ventes_immobilieres/(?P<id>[0-9]+)\.htm')
    m = re_id.finditer(response.read())

    for m2 in m:

        id = m2.group("id")
        url = 'http://www.leboncoin.fr/ventes_immobilieres/' + id + '.htm'

        c.execute('SELECT * FROM apparts WHERE id=?', (id,))
        tmp = c.fetchone()
        if(tmp):
            print fdb.format(*tmp)
            continue

        try:
            response = urllib2.urlopen(url)
        except Exception as e:
            print 'Error on url', url
            print e
            continue
        rep = response.read()

        try:
            m3 = re.findall('class="price"\>([0-9 ]+).*\<', rep)
            prix = int(m3[0].replace(' ', ''))
            m3 = re.findall(
                '<th>Surface : </th>\s*<td>([0-9]+) m<sup>2</sup>', rep)
            surface = int(m3[0])
            m3 = re.findall(
                '<th>Code postal :</th>\s*<td>([0-9]+)</td>', rep)
            cp = m3[0]
            m3 = re.findall(
                '<th>Ville :</th>\s*<td>([^<]+)</td>', rep)
            ville = m3[0].decode('cp1252')
            m3 = re.findall(
                'Mise en ligne par <a rel="nofollow" '
                + 'href="http://www2.leboncoin.fr/ar.ca=21_s&amp;id=[0-9]+" '
                + 'onclick="return [^"]+">([^<]+)</a> '
                + 'le (\d+) (.+) &agrave; (\d+:\d+). </div>', rep)
        #print m3, m3[0]
            nom = m3[0][0].decode('cp1252')
            jour = m3[0][1]
            mois = m3[0][2].decode('cp1252')
            if mois[:4] == 'janv' : mois = 1
            elif mois[0] == 'f' : mois = 2
            elif mois[:4] == 'mars' : mois = 3
            elif mois[:4] == 'avri' : mois = 4
            elif mois[:3] == 'mai' : mois = 5
            elif mois[:4] == 'juin' : mois = 6
            elif mois[:4] == 'juil' : mois = 7
            elif mois[0] == 'a' : mois = 8
            elif mois[:4] == 'sept' : mois = 9
            elif mois[:4] == 'octo' : mois = 10
            elif mois[:3] == 'nov' : mois = 11
            elif mois[:3] == 'déc' : mois = 12
            else : mois = 0
            
            ddt = datetime.datetime.today()
            annee = ddt.year
            # si on est en début d'année (ex: 3 jan 2014)
            # et que l'annonce est d'un mois de fin d'année (ex: 20 déc)
            # on corrige l'année (ex: pour avoir 20 déc 2013)
            if ddt.month < 6 and mois > 6:
                annee -= 1

            heure = m3[0][3]
        except Exception as e:
            print 'Error on url', url
            traceback.print_exc()
            #print e
            continue

        #print ville
        f = u'{0:6}€ {1:3}m² {4:4}€/m² {2:5} {3:22} {6:20} {7}/{8}/{9}@{10} {5}'
        print f.format(
            prix, surface, cp, ville, prix / surface,
            url, nom, jour, mois, annee, heure)

        c.execute('INSERT INTO apparts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', \
                  (id, prix, surface, cp, ville, nom, jour, mois, annee, heure))

        #exit(0)

    conn.commit()

if cmd == 'stats':

    conn = sqlite3.connect(database)
    c = conn.cursor()

    prix_m2_cp = {}

    c.execute('SELECT * FROM apparts')
    tmp = c.fetchone()
    while(tmp):
        #print fdb.format(*tmp)
        try:
            prix_m2_cp[tmp[3]]
        except:
            prix_m2_cp[tmp[3]] = []
        prix_m2_cp[tmp[3]].append(tmp[1]/tmp[2])
        #print tmp[1]/tmp[2], tmp[3]
        tmp = c.fetchone()

    print prix_m2_cp

    for k,v in prix_m2_cp.iteritems():
        print u'{0:5} {1:4} {2}'.format( k, sum(v)/len(v), len(v) )

print 'Fin.'
