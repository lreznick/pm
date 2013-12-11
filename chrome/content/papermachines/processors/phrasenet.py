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

class PhraseNet(textprocessor.TextProcessor):

    """
    Generate phrase net
    cf. http://www-958.ibm.com/software/data/cognos/manyeyes/page/Phrase_Net.html
    """

    def _basic_params(self):
        self.name = 'phrasenet'

    #add phrases w/ key by date that file was written
    def _findPhrases(self, pattern):
        #{x,y: {time: count})}
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
                        """
                        for word in match:
                            if not word in self.nodes:
                                nodes[word] = 1
                            else:
                                nodes[word] += 1
                        """
                        edge = match[0] + self.edgesep + match[1]
                        self.edges[edge][time] += 1

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

        #should put files into intervals
        self.split_into_intervals(start_and_end_dates=True)
        #logging.info("intervals: " + str(self.labels))

        self._findPhrases(re.compile(pattern, flags=re.UNICODE))



        logging.info('generating JSON')

        #used_nodes = set()
        
        #jsondata = {'edges': []}

        #jsondata = self.edges
        jsondata = filter((lambda (x, y): sum(y.values()) > 3),  self.edges.iteritems())

        """
        top_edges = self.edges.keys()
        top_edges.sort(key=lambda x: sum(self.edges[x].values())
        top_edges.reverse()
        top_edges = top_edges[:50]

        for edge in top_edges:
            words = edge.split(',')
            #used_nodes.update(words)

        #nodeindex = dict(zip(used_nodes, range(len(used_nodes))))
        """


        """
        for edge in top_edges:
            weight = self.edges[edge]
            words = edge.split(',')
            jsondata['edges'].append({'source': nodeindex[words[0]],
                    'target': nodeindex[words[1]], 'weight': weight})

        for node in used_nodes:
            jsondata['nodes'].append({'index': nodeindex[node],
                    'name': node, 'freq': self.nodes[node]})
        """
        params = {'DATA': jsondata, 'PATTERN': pattern_str}
        self.write_html(params)
        


if __name__ == '__main__':
    try:
        processor = PhraseNet(track_progress=True)
        processor.process()
    except:
        logging.error(traceback.format_exc())
