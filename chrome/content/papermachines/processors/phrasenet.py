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

class PhraseNet(textprocessor.TextProcessor):

    """
    Generate phrase net
    cf. http://www-958.ibm.com/software/data/cognos/manyeyes/page/Phrase_Net.html
    """

    def _basic_params(self):
        self.name = 'phrasenet'

    #add phrases w/ key by date that file was written
    def _findPhrases(self, pattern):
        self.nodes = defaultdict((lambda: 0))
        self.times = defaultdict((lambda: defaultdict(lambda: 0)))
        self.edges = defaultdict((lambda: defaultdict(lambda: 0)))
        for time, fileset in self.labels.iteritems():
            for filename in fileset:
                self.update_progress()
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
                        self.times[time][edge] += 1
                        self.edges[edge][time] += 1


    #calculate tdidf scores per phrase in time period
    def _tfidf(self):
        #pdb.set_trace()
        #tf for each phrase = count in time period * log (number of time periods / (1+number of time periods with phrase))
        self.tfidf_scores = defaultdict((lambda: defaultdict((lambda:0))))
        numperiods = float(len(self.times.keys()))
        logging.info(str(self.edges))
        logging.info(str(self.times))
        for time, edgecounts in self.times.iteritems():
            for edge, count in edgecounts.iteritems():
                num_matching_periods = 0
                for x in self.times.values():
                    val = x.get(edge) 
                    if ((val!=None) and (val!=0)):
                        num_matching_periods+=1
                self.tfidf_scores[edge][time] = (count * (log(numperiods/(1+num_matching_periods))))

    #go through phrases and store significance
    #def _mww(self):
    #    self._tfidf()
    #    for 
    def process(self):
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
        print("1")

        #should put files into intervals
        self.split_into_intervals(start_and_end_dates=False)
        #logging.info("intervals: " + str(self.labels))
        print("1")

        self._findPhrases(re.compile(pattern, flags=re.UNICODE))
        print("1")
        self._tfidf()
        print("1")
        logging.info('generating JSON')

        used_nodes = set()
        
        jsondata = defaultdict((lambda: []))

        #jsondata = self.edges
        #top_edges = filter((lambda (x, y): sum(y.values()) > 3),  self.edges.iteritems())

        #logging.info("Edges: "+str(len(self.edges.iteritems())))
        
        top_edges = self.edges.keys()
        top_edges.sort(key=(lambda x: sum(self.edges[x].values())))
        top_edges.reverse()
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
        
        params = {'DATA': jsondata, 'PATTERN': pattern_str}
        self.write_html(params)
        


if __name__ == '__main__':
    try:
        processor = PhraseNet(track_progress=True)
        processor.process()
    except:
        logging.error(traceback.format_exc())
