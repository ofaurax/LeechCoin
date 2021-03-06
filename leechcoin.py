#!/usr/bin/env python
# coding=utf-8

import argparse
import urllib2  # python 2.7
import re
import sqlite3
import traceback
import datetime
import csv

headers = { 'User-Agent' : 'Mozilla/5.0 (compatible; Googlebot/2.1;'
                               +' +http://www.google.com/bot.html)' } 
                               # http://www.useragentstring.com

parser = argparse.ArgumentParser()
parser.add_argument('cmd', choices=['help', 'leech', 'leechuntil', 'list', 'stats', 'search', 'searchconfig', 'config', 'check'])
parser.add_argument('-d',
                    help='database name to use (default:database.db)',
                    default='database.db')
parser.add_argument('params', nargs='*')

args = parser.parse_args()

print 'Commande :', args.cmd
print 'Args :', args
cmd = args.cmd
database = args.d

fgen = u"{0} {1:6}€ {2:3}m² {3} {4:25} {5:35} {6:2}/{7:2}/{8} {9} enligne:{13}\nhttp://www.leboncoin.fr/ventes_immobilieres/{0}.htm"
fdb = u'DB : ' + fgen
fdbs = fdb + u' {11}'

if cmd == 'help':
    print 'leech [num]: download of data from page [num] (default:1)'
    print 'list'
    print 'stats [code postal]'

if cmd == 'list':
    conn = sqlite3.connect(database)
    c = conn.cursor()
    
    for tmp in c.execute('SELECT * FROM apparts'):
        print fdb.format(*tmp)

def leechpage(page, cp):
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS apparts ( '+
    'id text PRIMARY KEY, ' +
    'prix int, ' +
    'surface int, ' +
    'cp int, ville text, ' +
    'nom text, ' +
    'jour int, mois int, annee int, heure text, ' +
    'tel text, ' +
    'desc text, ' +
    'siren text, ' +
    'enligne int)')

    req = urllib2.Request(
        'http://www.leboncoin.fr/ventes_immobilieres/offres/'
        #+ 'provence_alpes_cote_d_azur/bouches_du_rhone/'
        + '?'
        + 'ps=10&pe=14' # de 250k à 350k
        + '&ros=4' # pièces min
        + '&ret=1' # 1:maison, appart= '&ret=2'
        #+ '&f=p' # p:particuler c:pro
        + '&location=' + cp
        + '&o=' + str(page), None, headers) 
    response = urllib2.urlopen(req)
    re_id = re.compile('ventes_immobilieres/(?P<id>[0-9]+)\.htm')
    m = re_id.finditer(response.read())

    for m2 in m:

        id = m2.group("id")
        url = 'http://www.leboncoin.fr/ventes_immobilieres/' + id + '.htm'

        c.execute('SELECT * FROM apparts WHERE id=?', (id,))
        tmp = c.fetchone()
        if(tmp):
            try:
                print fdb.format(*tmp)
            except Exception:
                print tmp
                tmp = list(tmp)
                print type(tmp[4])
                tmp[4] = tmp[4].encode('utf-8')
                print type(tmp[4])
                print tmp
                print fdb.format(*tmp)
            continue

        try:
            response = urllib2.urlopen(url)
        except Exception as e:
            print 'Error on url', url
            print e
            continue
        rep = response.read().decode('cp1252')

        try:
            m3 = re.findall('class="price"\>([0-9 ]+).*\<', rep)
            try:
                prix = int(m3[0].replace(' ', ''))
            except:
                print rep
            m3 = re.findall(
                '<th>Surface : </th>\s*<td>([0-9 ]+) m<sup>2</sup>', rep)
            surface = int(m3[0].replace(' ', ''))
            m3 = re.findall(
                '<th>Code postal :</th>\s*<td>([0-9]+)</td>', rep)
            cp = m3[0]
            m3 = re.findall(
                '<th>Ville :</th>\s*<td>([^<]+)</td>', rep)
            try:
                ville = m3[0]
            except IndexError:
                ville = ''
            m3 = re.findall("'utilisateur_v2','N'\)\">([^<]+)</a>", rep)
            nom = m3[0]
            m3 = re.findall(' Mise en ligne le (\d+) (.+) &agrave; (\d+:\d+).', rep)
            jour = m3[0][0]
            mois = m3[0][1]
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
            elif mois[0] == 'd' : mois = 12
            else : mois = 0
            
            ddt = datetime.datetime.today()
            annee = ddt.year
            # si on est en début d'année (ex: 3 jan 2014)
            # et que l'annonce est d'un mois de fin d'année (ex: 20 déc)
            # on corrige l'année (ex: pour avoir 20 déc 2013)
            if ddt.month < 6 and mois > 6:
                annee -= 1

            heure = m3[0][2]

            m3 = re.findall('/pg/0([^\.]+)\.gif" class="AdPhonenum', rep)
            try:
                tel_raw = m3[0]
            except:
                tel_raw = ''
            #print m3, m3[0]

            m3 = re.findall('class="content">(.+?)</div>', rep, re.DOTALL)
            try:
                desc = m3[0]
            except:
                desc = ''
                
            m3 = re.findall('Siren : ([0-9]+)', rep)
            try:
                siren = m3[0]
            except:
                siren = 0

        except Exception as e:
            print 'Error on url', url
            traceback.print_exc()
            #print e
            continue

        #print ville
        f = u'{0:6}€ {1:3}m² {4:4}€/m² {2:5} {3:22} {6:20} {7}/{8}/{9}@{10} {5} {12} {11}'
        print f.format(
            prix, surface, cp, ville, prix / surface,
            url, nom, jour, mois, annee, heure, tel_raw, siren)
        print desc

        c.execute('INSERT INTO apparts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', \
                  (id, prix, surface, cp, ville, nom, jour, mois, annee, heure, \
                   tel_raw, desc, siren, 1))

        #exit(0)

    conn.commit()

if cmd == 'leech':

    try:
        page = int(args.params[0])
    except:
        page = 1

    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute("SELECT * FROM config")

    tmp = c.fetchone()
    while(tmp):
        print u'{0:10}: {1}'.format(*tmp)
        if tmp[0] == 'cp' :
            print 'CP:',tmp[1]
            cp = tmp[1].split(',')
        tmp = c.fetchone()

    for cpi in cp:
        print 'Leech', cpi, page
        leechpage(page, cpi)

if cmd == 'leechuntil':

    try:
        page = int(args.params[0])
    except:
        page = 1

    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute("SELECT * FROM config")

    tmp = c.fetchone()
    while(tmp):
        print u'{0:10}: {1}'.format(*tmp)
        if tmp[0] == 'cp' :
            print 'CP:',tmp[1]
            cp = tmp[1].split(',')
        tmp = c.fetchone()

    for cpi in cp:
        for i in range(page, 0, -1):
            print 'Leech', cpi, i
            leechpage(i,cpi)

if cmd == 'stats':

    try:
        cp = int(args.params[0])
    except:
        cp = 0

    conn = sqlite3.connect(database)
    c = conn.cursor()

    prix_m2_cp = {}
    prix_m2_cp_pro = {}

    if cp:
        c.execute('SELECT * FROM apparts WHERE cp=?', (cp,))
    else:
        c.execute('SELECT * FROM apparts')
        
    tmp = c.fetchone()
    while(tmp):
        #print fdb.format(*tmp)
        try:
            prix_m2_cp[tmp[3]]
        except:
            prix_m2_cp[tmp[3]] = []
        try:
            prix_m2_cp_pro[tmp[3]]
        except:
            prix_m2_cp_pro[tmp[3]] = []

        if tmp[1]/tmp[2] > 1000 and tmp[1]/tmp[2] < 8000:

            if cp:
                print '{0} {1:3} {2} {3:22} {4}'.format(
                    tmp[1], tmp[2],
                    str(tmp[1]/tmp[2])+'€/m²',
                    tmp[5].encode('utf8'),
                    'http://www.leboncoin.fr/ventes_immobilieres/'+tmp[0]+'.htm')

            #print tmp[12]
            if int(tmp[12]) > 0: #siren
                prix_m2_cp_pro[tmp[3]].append(tmp[1]/tmp[2])
            else: # pas pro
                prix_m2_cp[tmp[3]].append(tmp[1]/tmp[2])
            #print tmp[1]/tmp[2], tmp[3]
        tmp = c.fetchone()

    #print prix_m2_cp
    #print prix_m2_cp_pro

    cp_ville = {}
    with open('data/insee.csv') as inseefile:
        inseedata = csv.reader(inseefile, delimiter=';')
        for ligne in inseedata:
            try:
                cp_ville[int(ligne[1])] = ligne[0]
                #print int(ligne[1]), ligne[0]
            except ValueError:
                pass

    for k in list(set(prix_m2_cp.keys() + prix_m2_cp_pro.keys())):

        numpart = len(prix_m2_cp[k])
        if numpart: moypart = sum(prix_m2_cp[k])/numpart
        else: moypart = 0

        numpro = len(prix_m2_cp_pro[k])
        if numpro: moypro = sum(prix_m2_cp_pro[k])/numpro
        else: moypro = 0

        if moypro: ratio = moypart / float(moypro)
        else: ratio = 0

        print u'{0:5} part({1:3}): {2:4}€/m² pro({3:3}): {4:4}€/m² {5:3}% {6}'.format( \
            k, numpart, moypart, numpro, moypro, int(ratio*100), cp_ville[k])

if cmd == 'test':
    with open('data/insee.csv') as inseefile:
        inseedata = csv.reader(inseefile, delimiter=';')
        for ligne in inseedata:
            try:
                print int(ligne[1]), ligne[0]
            except ValueError:
                pass

if cmd == 'search':

    try:
        s = args.params[0]
    except:
        raise Exception('Recherche manquante')

    conn = sqlite3.connect(database)
    c = conn.cursor()

    c.execute("SELECT * FROM apparts WHERE desc LIKE ?", ('%'+s+'%',))
        
    tmp = c.fetchone()
    while(tmp):
        print fdbs.format(*tmp)
        tmp = c.fetchone()

if cmd == 'searchconfig':

    conn = sqlite3.connect(database)
    c = conn.cursor()
    
    c.execute("SELECT * FROM config")

    tmp = c.fetchone()
    while(tmp):
        print u'{0:10}: {1}'.format(*tmp)
        if tmp[0] == 'cp' :
            print 'CP:',tmp[1]
            cp = tmp[1].split(',')
        if tmp[0] == 'prixmax' :
            print 'PrixMax:',tmp[1]
            prixmax = tmp[1]
        if tmp[0] == 'surfmin' :
            print 'SurfMin:',tmp[1]
            surfmin = tmp[1]
        tmp = c.fetchone()
    
    c.execute("SELECT * FROM apparts ORDER BY annee,mois,jour,cp,heure,id")
        
    tmp = c.fetchone()
    while(tmp):
        if str(tmp[3]) in cp:
            print fdb.format(*tmp)
        tmp = c.fetchone()

if cmd == 'config':

    if len(args.params) < 1:
        conn = sqlite3.connect(database)
        c = conn.cursor()

        c.execute("SELECT * FROM config")

        print 'Config:'
        tmp = c.fetchone()
        while(tmp):
            print u'{0:10}: {1}'.format(*tmp)
            tmp = c.fetchone()


    elif len(args.params) != 2:
        raise Exception('Attendu: clé valeur')

    else:
        conn = sqlite3.connect(database)
        c = conn.cursor()

        c.execute('CREATE TABLE IF NOT EXISTS config (key text PRIMARY KEY, value text)')

        try:
            c.execute('INSERT INTO config VALUES (?, ?)', (args.params[0], args.params[1]))
        except sqlite3.IntegrityError:
            c.execute('UPDATE config SET value=? WHERE key=?', (args.params[1], args.params[0]))
                
        conn.commit()

def check_id(id):

    url = 'http://www.leboncoin.fr/ventes_immobilieres/' + id + '.htm'
    try:
        response = urllib2.urlopen(url)
    except urllib2.HTTPError as he:
        #Usually, 404
        print 'HTTP Error on url', url
        print he
        return False
    except Exception as e:
        print 'Error on url', url
        print e

    #rep = response.read().decode('cp1252')
    #if rep.find(u'Cette annonce est désactivée') > -1: return False

    return True

if cmd == 'check':

    conn = sqlite3.connect(database)
    c = conn.cursor()

    c.execute("SELECT id FROM apparts WHERE enligne=1")

    tmp = c.fetchone()
    dead = []
    while(tmp):
        print tmp
        if not check_id(tmp[0]): dead.append(tmp[0])
        tmp = c.fetchone()

    for d in dead:
        print d
        c.execute("UPDATE apparts SET enligne=0 WHERE id=?", (d,))
        
    conn.commit()

print 'Fin.'
