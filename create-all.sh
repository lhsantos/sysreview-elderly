#!/bin/bash
sed '2s/.*/\<\!DOCTYPE\ PubmedArticleSet\ SYSTEM\ \"nlmmedlinecitationset\_160101\.dtd\"\>/' pubmed-in.xml > pubmed-out.xml
xsltproc -o pubmed.bib pubmed2bibtex.xsl pubmed-out.xml
sed '2s/.*/\<\!DOCTYPE\ PubmedArticleSet\ SYSTEM\ \"nlmmedlinecitationset\_160101\.dtd\"\>/' pubmed-cog-in.xml > pubmed-cog-out.xml
xsltproc -o pubmed-cog.bib pubmed2bibtex.xsl pubmed-cog-out.xml
mkdir -p temp
python merger.py -a temp -o all.bib acm.bib ieee.bib pubmed.bib sd.bib
python merger.py -a temp -o all-cog.bib acm-cog.bib ieee-cog.bib pubmed-cog.bib sd-cog.bib
