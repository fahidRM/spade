import os
import sys
import time
import unittest

sys.path.append('..'+os.sep+'trunk')
sys.path.append('..')

import spade
import xmpp

import pxdom
from xml.dom import minidom



class ContentObjectTestCase(unittest.TestCase):
    
    def setUp(self):
        #self.rdf = """<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:foaf="http://xmlns.com/foaf/0.1/" xmlns:dc="http://purl.org/dc/elements/1.1/"><rdf:Description rdf:about="http://en.wikipedia.org/wiki/Tony_Benn"><dc:title>Tony Benn</dc:title><dc:publisher>Wikipedia</dc:publisher><foaf:primaryTopic><foaf:Person><foaf:name>Tony Benn</foaf:name></foaf:Person></foaf:primaryTopic></rdf:Description></rdf:RDF>"""
        self.rdf = """<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:foaf="http://xmlns.com/foaf/0.1/" xmlns:dc="http://purl.org/dc/elements/1.1/"><rdf:Description><dc:title>Tony Benn</dc:title><dc:publisher>Wikipedia</dc:publisher><foaf:primaryTopic><foaf:Person><foaf:name>Tony Benn</foaf:name></foaf:Person></foaf:primaryTopic></rdf:Description></rdf:RDF>"""
        self.nb = xmpp.simplexml.NodeBuilder(self.rdf)
        
        self.co = spade.content.ContentObject()
        self.co.addNamespace("http://xmlns.com/foaf/0.1/","foaf:")
        self.co.addNamespace("http://purl.org/dc/elements/1.1/", "dc")
        self.co["rdf:Description"] = spade.content.ContentObject()
        self.co["rdf:Description"]["dc:title"] = "Tony Benn"
        self.co["rdf:Description"]["dc:publisher"] = "Wikipedia"
        self.co["rdf:Description"]["foaf:primaryTopic"] = spade.content.ContentObject()
        self.co["rdf:Description"]["foaf:primaryTopic"]["foaf:Person"] = spade.content.ContentObject()
        self.co["rdf:Description"].primaryTopic.Person["foaf:name"] = "Tony Benn"

    def tearDown(self):
        pass
        
    def testRDFXML2CO(self):
        sco = spade.content.RDFXML2CO(self.rdf) 
        self.assertEqual(sco, self.co)
        
    def testCO2RDFXML(self):
        rdf = self.co.asRDFXML()
        assert self.isEqualXML(rdf, self.rdf)
        
        
    def testGetData(self):
        co = spade.content.ContentObject()
        co["test1"] = spade.content.ContentObject()
        co["test1"]["test2"]= "test3"
        
        assert co.test1.test2 == "test3"
        
    def testCOSanity(self):        
        rdf = self.co.asRDFXML()
        co = spade.content.RDFXML2CO(rdf)
        
        assert co == self.co
        
    def testRDFSanity(self):
        co = spade.content.RDFXML2CO(self.rdf)        
        rdf = co.asRDFXML()

        assert self.isEqualXML(rdf, self.rdf)


    def isEqualXML(self, a, b):
        #da, db= pxdom.parseString(a), pxdom.parseString(a)
        #return da.isEqualNode(db)
        #da, db= minidom.parseString(a), minidom.parseString(b)
        da,db = xmpp.simplexml.NodeBuilder(a),xmpp.simplexml.NodeBuilder(b)
        self.isEqualElement(da.getDom(),db.getDom())

    def isEqualElement(self,a, b):
        if a.getName()!=b.getName():
            return False
        if sorted(a.getAttrs().items())!=sorted(b.getAttrs().items()):
            return False
        if len(a.getChildren())!=len(b.getChildren()):
            return False
        for ac in a.getChildren():
            l = []
            for bc in b.getChildren():
                if ac.getName() == bc.getName():
                    l.append(bc)
            if len(l) == 0: return False
            r = False
            for n in l:
                if len(ac.kids)==len(n.kids): r = True
            if not r: return False
            
            if ac.getData():
                for n in l:
                    if n.getData()==ac.getData(): r = True
                if not r: return False
                
            if not ac.getData() and (len(ac.kids)>0):
                for n in l:
                    if self.isEqualElement(ac,n): r = True
                if not r: return False
                
        """for ac, bc in zip(a.getChildren(), b.getChildren()):
            if len(ac.kids)!=len(bc.kids):
                return False
            if ac.getData() and ac.getData()!=bc.getData():
                return False
            if not ac.getData() and (len(ac.kids)>0) and not self.isEqualElement(ac, bc):
                return False"""
        return True



if __name__ == "__main__":
    unittest.main()



