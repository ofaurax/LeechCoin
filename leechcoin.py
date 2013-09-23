#!/usr/bin/env python
# coding=utf-8

import argparse
import urllib2  # python 2.7
import re
import sqlite3

parser = argparse.ArgumentParser()
parser.add_argument('cmd')
parser.add_argument('params', nargs='*')

args = parser.parse_args()

print 'Commande :', args.cmd
print 'Args :', args.params
cmd = args.cmd

if cmd == 'help':
    print 'leech [num]: download of data from page [num] (default:1)'

if cmd == 'leech':

    try:
        page = int(args.params[0])
    except:
        page = 1

    conn = sqlite3.connect('leechcoin.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS apparts (id text, prix int, surface int, cp int, ville text, nom text, jour int, mois text, heure text)')

    response = urllib2.urlopen(
        'http://www.leboncoin.fr/ventes_immobilieres/offres/'
        + 'provence_alpes_cote_d_azur/bouches_du_rhone/'
        + '?pe=8&sqs=6&ros=2&ret=1&ret=2&f=p&o=' + str(page))
    
    re_ids = re.compile('ventes_immobilieres/([0-9]+)\.htm')
    m = re_ids.finditer(response.read())

    for m2 in m:
        id = m2.group(1)
        url = 'http://www.leboncoin.fr/ventes_immobilieres/' + id + '.htm'
        try:
            response = urllib2.urlopen(url)
        except Exception as e:
            print 'Error on url', url
            print e
            continue
        rep = response.read()

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
        heure = m3[0][3]

        #print ville
        f = u'{0:6}€ {1:3}m² {4:4}€/m² {2:5} {3:22} {6:20} {7}{8}@{9} {5}'
        print f.format(
            prix, surface, cp, ville, prix / surface,
            url, nom, jour, mois[:4], heure)

        c.execute('INSERT INTO apparts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', \
                  (id, prix, surface, cp, ville, nom, jour, mois, heure))

        #exit(0)

    conn.commit()

print 'Fin.'
