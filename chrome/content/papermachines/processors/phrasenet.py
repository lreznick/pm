#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import json
import re
import tempfile
import cStringIO
import logging
import traceback
import codecs
import textprocessor
from collections import defaultdict
from math import log
import pdb
from datetime import datetime, timedelta

class PhraseNet(textprocessor.TextProcessor):

    """
    Generate phrase net
    cf. http://www-958.ibm.com/software/data/cognos/manyeyes/page/Phrase_Net.html
    """

    def _basic_params(self):
        self.name = 'phrasenet'


    def getfiledate(self, filename):
        date_str = self.metadata[filename]['date']
        if date_str.strip() == '':
            logging.error(("File {:} has invalid date" +
                          "-- removing...").format(filename))
            del self.metadata[filename]
            return None
        cleaned_date = date_str[0:10]
        if '-00' in cleaned_date:
            cleaned_date = cleaned_date[0:4] + '-01-01'
        try:
            date_for_doc = datetime.strptime(cleaned_date,
                    '%Y-%m-%d')
            #datestr_to_datetime[date_str] = date_for_doc
            # if (self.start_date is not None and 
            #         date_for_doc < self.start_date):
            #     logging.error(("File {:} is before date range" +
            #                    "-- removing...").format(filename))
            #     del self.metadata[filename]
            #     return None
            # if (self.end_date is not None and 
            #         date_for_doc > self.end_date):
            #     logging.error(("File {:} is after date range" +
            #                    "-- removing...").format(filename))
            #     del self.metadata[filename]
            #     return None
            return date_for_doc
        except:
            logging.error(traceback.format_exc())
            logging.error('Date {:} not recognized'.format(cleaned_date))
            return None

    #add phrases w/ key by date that file was written
    def _findPhrases(self, pattern):
        self.nodes = defaultdict((lambda: 0))
        self.times = defaultdict((lambda: defaultdict(lambda: 0)))
        self.edges = defaultdict((lambda: defaultdict(lambda: 0)))

        for filename in self.files:
            self.update_progress()
            date = str(self.getfiledate(filename))
            if (date is None): 
                continue
            with codecs.open(filename, 'r', encoding='utf8') as f:
                logging.info('processing ' + filename)
                for re_match in pattern.finditer(f.read()):
                    match = [w.lower() for w in re_match.groups()]
                    if any([word in self.stopwords_set for word in
                           match]):
                        continue
                    for word in match:
                        self.nodes[word]+=1
                    
                    edge = match[0] + self.edgesep + match[1]
                    self.times[date][edge] += 1
                    self.edges[edge][date] += 1


    #calculate tdidf scores per phrase in time period
    def _tfidf(self):
        #tf for each phrase = count in time period * log (number of time periods / (1+number of time periods with phrase))
        self.tfidf_scores = defaultdict((lambda: defaultdict((lambda:0))))
        numperiods = float(len(self.times.keys()))
        logging.info(str(self.edges))
        logging.info(str(self.times))
        for time, edgecounts in self.times.iteritems():
            for edge, count in edgecounts.iteritems():
                num_matching_periods = 0
                for x in self.times.values():
                    if (x.__contains__(edge) ):
                        num_matching_periods+=1
                self.tfidf_scores[edge][time] = (count * (log(numperiods/(1+num_matching_periods))))

    #go through phrases and store significance
    #def _mww(self):
    #    self._tfidf()
    #    for 
    def process(self):
        #pdb.set_trace()
        logging.info('starting to process')
 
        self.stopwords_set = set(self.stopwords)

        self.edgesep = ','

        wordregex = "(\w+)"

        if len(self.extra_args) > 0:
            pattern_str = self.extra_args[0]
        else:
            pattern_str = 'x and y'

        if pattern_str.count('x') == 1 and pattern_str.count('y') == 1:
            pattern = pattern_str.replace('x', wordregex)
            pattern = pattern.replace('y', wordregex)
        else:
            pattern = pattern_str

        logging.info('extracting phrases according to pattern '
                     + repr(pattern))

        self._findPhrases(re.compile(pattern, flags=re.UNICODE))
        self._tfidf()
        logging.info('generating JSON')

        used_nodes = set()
        
        jsondata = defaultdict((lambda: []))

        #jsondata = self.edges
        #top_edges = filter((lambda (x, y): sum(y.values()) > 3),  self.edges.iteritems())

        #logging.info("Edges: "+str(len(self.edges.iteritems())))
        
        #top_edges = 
        top_edges = sorted(self.edges.keys(), key=(lambda x: sum(self.edges[x].values())), reverse = True)
        #top_edges.reverse()
        top_edges = top_edges[:50]
        logging.info("Top edge: "+str(top_edges))

        for edge in top_edges:
            words = edge.split(',')
            used_nodes.update(words)

        nodeindex = dict(zip(used_nodes, range(len(used_nodes))))

        for edge in top_edges:
            weight = sum(self.edges[edge].values())
            timecounts = dict(filter((lambda (x, y): y>0), self.edges[edge].iteritems()))
            tfidf = self.tfidf_scores[edge]
            words = edge.split(',')
            jsondata['edges'].append({'source': nodeindex[words[0]],
                    'target': nodeindex[words[1]], 'weight': weight, 
                    'weightbytime': timecounts, 'tfidf':tfidf})

        for node in used_nodes:
            jsondata['nodes'].append({'index': nodeindex[node],
                    'name': node, 'freq': self.nodes[node]})
        #want a dict of {time:{edge:count}}, but just with some edges filtered out
        filteredtimes = []
        for time, edgecounts in self.times.iteritems():
            filterededges = [{"edge":key, "count": value} for key, value in edgecounts.iteritems() if key in top_edges]
            filteredtimes.append({"time": time, "edgecounts": filterededges})
        jsondata['times'] = filteredtimes
        
        params = {'DATA': jsondata, 'PATTERN': pattern_str}
        self.write_html(params)
        


if __name__ == '__main__':
    try:
        processor = PhraseNet(track_progress=True)
        processor.process()
    except:
        logging.error(traceback.format_exc())
