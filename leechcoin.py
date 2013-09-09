#!/usr/bin/env python
# coding=utf-8

import argparse
import urllib2  # python 2.7
import re

parser = argparse.ArgumentParser()
parser.add_argument('cmd')
parser.add_argument('params', nargs='*')

args = parser.parse_args()

print 'Commande :', args.cmd
print 'Args :', args.params
cmd = args.cmd

if cmd == 'leech':

    try:
        page = int(args.params[0])
    except:
        page = 1
    
    response = urllib2.urlopen(
    'http://www.leboncoin.fr/ventes_immobilieres/offres/'
    + 'provence_alpes_cote_d_azur/bouches_du_rhone/'
    + '?pe=8&sqs=6&ros=2&ret=1&ret=2&f=p&o=' + str(page))

    re_ids = re.compile('ventes_immobilieres/([0-9]+)\.htm')
    m = re_ids.finditer(response.read())

    for m2 in m:
        id = m2.group(1)
        url = 'http://www.leboncoin.fr/ventes_immobilieres/' + id + '.htm'
        response = urllib2.urlopen(url)
        rep = response.read()
    
        m3 = re.findall('class="price"\>([0-9 ]+).*\<', rep)
        prix = int(m3[0].replace(' ', ''))
        m3 = re.findall('<th>Surface : </th>\s*<td>([0-9]+) m<sup>2</sup>', rep)
        surface = int(m3[0])
        m3 = re.findall('<th>Code postal :</th>\s*<td>([0-9]+)</td>', rep)
        cp = m3[0]
        m3 = re.findall('<th>Ville :</th>\s*<td>([^<]+)</td>', rep)
        ville = m3[0].decode('cp1252')
        m3 = re.findall('Mise en ligne par <a rel="nofollow" href="http://www2.leboncoin.fr/ar.ca=21_s&amp;id=[0-9]+" onclick="return [^"]+">([^<]+)</a> le (\d+) (.+) &agrave; (\d+:\d+). </div>', rep)
        #print m3, m3[0]
        nom = m3[0][0].decode('cp1252')
        jour = m3[0][1]
        mois = m3[0][2].decode('cp1252')
        heure = m3[0][3]

        #print ville
        print u'{0:6}€ {1:3}m² {4:4}€/m² {2:5} {3:22s} {6:20} {7}{8}@{9} {5}'. \
        format(prix, surface, cp, ville, prix/surface, url, nom, jour, mois[:4], heure)
        #exit(0)

print 'Fin.'
